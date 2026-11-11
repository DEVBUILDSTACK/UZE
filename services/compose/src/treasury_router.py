"""Autonomous Treasury & Swap Engine — agent compute funding.

Built 2026-11-11 on James's explicit override (his own words,
16:30 ET): "lift the freeze, break the UZEmarkets/SigLayer
boundary, and build it now." The override addendum is filed in
research_notes/xsiglayer-specs/BOUNDARY-UZEMARKETS-vs-SIGLAYER.md.

What this module is (and is not):

  The mechanism is structurally real: before an agent task runs
  on the x402-gated agent surface (src/agents.py), the agent's
  NEAR compute balance is checked against the inference
  threshold. If the balance is below threshold, the engine
  autonomously executes a swap from a supported settlement rail
  into native NEAR and records the swap as an append-only
  EventLog entry (event type `agent.treasury.swap_executed`).

  Execution is MOCKED for the hackathon, in the same honest
  register as the x402 mock tariff and the mock partner adapters:
  balances are mock state, the swap is a simulation labelled
  `mock: True` in every payload it touches, the provider is
  recorded as the Coinbase Developer Platform (CDP) swap in
  mock form, and NO funds move — SoSem holds no keys (custody
  gate A5 is open) and no live swap rail exists in this repo.
  The production swap replaces `execute_mock_swap` at the seam
  marked below; the check, the rail table, the event record and
  the response shapes do not change.

Supported rails (mock router):

  - SOLANA_USDC     Solana           USDC  -> NEAR
  - BASE_ETH        Base             ETH   -> NEAR
  - ROBINHOOD_USDG  Robinhood Chain  USDG  -> NEAR
  - INK_ASSET       Ink              INK   -> NEAR

Endpoints:

  GET  /api/v1/treasury/balance/{agent}
  POST /api/v1/treasury/ensure-compute  {agent, rail?}
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import models
from db import get_session

router = APIRouter(prefix="/api/v1/treasury")

# NEAR required before an inference-bearing agent task may run.
INFERENCE_THRESHOLD_NEAR = float(
    os.environ.get("TREASURY_INFERENCE_THRESHOLD_NEAR", "0.5")
)

# The mock swap packages, one per supported rail. Amounts are the
# directive's packages (10 USDC / 0.05 ETH); the NEAR received is
# the module's declared mock conversion, labelled mock everywhere
# it surfaces. Production pricing replaces this table at the CDP
# seam — nothing else reads these numbers as real.
SUPPORTED_RAILS: dict[str, dict[str, Any]] = {
    "SOLANA_USDC": {
        "chain": "Solana",
        "source_asset": "SOLANA_USDC",
        "source_symbol": "USDC",
        "amount_in": 10,
        "near_received": 8.0,
    },
    "BASE_ETH": {
        "chain": "Base",
        "source_asset": "BASE_ETH",
        "source_symbol": "ETH",
        "amount_in": 0.05,
        "near_received": 40.0,
    },
    "ROBINHOOD_USDG": {
        "chain": "Robinhood Chain",
        "source_asset": "ROBINHOOD_USDG",
        "source_symbol": "USDG",
        "amount_in": 10,
        "near_received": 8.0,
    },
    "INK_ASSET": {
        "chain": "Ink",
        "source_asset": "INK_ASSET",
        "source_symbol": "INK",
        "amount_in": 10,
        "near_received": 8.0,
    },
}

DEFAULT_RAIL = "SOLANA_USDC"
TARGET_ASSET = "NEAR"

# Mock compute balances, in NEAR, per agent. The demo state is
# deliberately LOW (below threshold) so the autonomous swap fires
# on the first agent task, exactly as the demo beat shows. Tests
# and the demo set balances through set_mock_near_balance.
_MOCK_BALANCES: dict[str, float] = {"GIRA": 0.10, "SURA": 0.10}
_DEFAULT_MOCK_BALANCE = float(
    os.environ.get("TREASURY_MOCK_NEAR_BALANCE", "0.10")
)


def get_mock_near_balance(agent: str) -> float:
    """The agent's (mock) native NEAR compute balance."""
    return _MOCK_BALANCES.get(agent.upper(), _DEFAULT_MOCK_BALANCE)


def set_mock_near_balance(agent: str, balance: float) -> None:
    _MOCK_BALANCES[agent.upper()] = float(balance)


def execute_mock_swap(db: Session, agent: str, rail: str) -> dict[str, Any]:
    """Execute one (mock) swap into NEAR and record it.

    THE PRODUCTION SEAM: a live CDP swap call replaces the
    simulation inside this function. The EventLog record, the
    balance update and the returned shape are the contract the
    rest of the system already consumes.
    """
    spec = SUPPORTED_RAILS[rail]
    before = get_mock_near_balance(agent)
    after = before + spec["near_received"]
    set_mock_near_balance(agent, after)
    record = {
        "source_asset": spec["source_asset"],
        "source_chain": spec["chain"],
        "target_asset": TARGET_ASSET,
        "amount": spec["amount_in"],
        "amount_asset": spec["source_symbol"],
        "near_received": spec["near_received"],
        "provider": "coinbase-cdp",
        "mock": True,
        "balance_before_near": before,
        "balance_after_near": after,
        "threshold_near": INFERENCE_THRESHOLD_NEAR,
    }
    db.add(
        models.EventLog(
            aggregate_type="agent",
            aggregate_id=agent.upper(),
            event_type="agent.treasury.swap_executed",
            actor=f"agent:{agent.upper()}",
            payload=record,
        )
    )
    return record


def ensure_compute_funded(
    db: Session, agent: str, rail: str = DEFAULT_RAIL
) -> dict[str, Any]:
    """The pre-task trigger: check the agent's NEAR balance and,
    if it is below the inference threshold, autonomously swap
    from the chosen rail into NEAR so the task can proceed.

    Adds the swap's EventLog row to the session when a swap
    executes; the CALLER commits (the agent handlers commit their
    own event in the same transaction; the treasury endpoint
    commits here via its route wrapper below).
    """
    if rail not in SUPPORTED_RAILS:
        raise ValueError(
            f"unsupported rail: {rail} "
            f"(supported: {', '.join(sorted(SUPPORTED_RAILS))})"
        )
    agent = agent.upper()
    balance = get_mock_near_balance(agent)
    if balance >= INFERENCE_THRESHOLD_NEAR:
        return {
            "agent": agent,
            "funded": True,
            "swap_executed": False,
            "near_balance": balance,
            "threshold_near": INFERENCE_THRESHOLD_NEAR,
            "mock": True,
        }
    swap = execute_mock_swap(db, agent, rail)
    return {
        "agent": agent,
        "funded": True,
        "swap_executed": True,
        "swap": swap,
        "near_balance": get_mock_near_balance(agent),
        "threshold_near": INFERENCE_THRESHOLD_NEAR,
        "mock": True,
    }


@router.get("/balance/{agent}")
def treasury_balance(agent: str):
    agent = agent.upper()
    return {
        "agent": agent,
        "asset": TARGET_ASSET,
        "balance": get_mock_near_balance(agent),
        "threshold_near": INFERENCE_THRESHOLD_NEAR,
        "funded": get_mock_near_balance(agent) >= INFERENCE_THRESHOLD_NEAR,
        "supported_rails": sorted(SUPPORTED_RAILS),
        "mock": True,
    }


@router.post("/ensure-compute")
async def treasury_ensure_compute(
    body: dict, db: Session = Depends(get_session)
):
    agent = (body or {}).get("agent")
    if not agent:
        raise HTTPException(status_code=422, detail="agent is required")
    rail = (body or {}).get("rail") or DEFAULT_RAIL
    try:
        result = ensure_compute_funded(db, str(agent), str(rail))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    db.commit()
    return JSONResponse(content=result)
