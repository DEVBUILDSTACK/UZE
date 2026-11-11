"""A2A Contribution Receipts — entity escrow pools (MOCK).

Built 2026-11-11 on the owner's tap ("Build the Assign
expansion + contribution receipts as mocks now"), implementing
the Directive 2 funding flow as a mock:

  - Partners (through their agents) contribute USDC amounts to
    an Entity's pool. Each contribution MINTS A CONTRIBUTION
    RECEIPT: the partner's share of the pool in basis points,
    recomputed across the whole pool on every contribution so
    shares always sum to 10,000 bps (rounding residue lands on
    the largest contributor — deterministic, stated here).
  - TRUE-UP: given the entity's legal equity split (bps per
    partner, must sum to 10,000), the endpoint computes each
    partner's target value against the pool total and returns
    the balancing transfers — who sends whom how much — as
    MOCK send/receive instructions. Nothing executes: the
    instructions are the output, recorded in the EventLog
    (treasury.escrow.true_up_computed) for the agents to act
    on through the treasury send/receive rail when a real
    rail exists.

  Custody state, stated in every payload: THIS IS A MOCK
  ESCROW. No funds are held, moved, or owed by this service;
  pools and receipts are accounting records in an in-memory
  registry plus the append-only EventLog
  (treasury.escrow.contribution). Real pooled capital sits
  behind the custody gate and does not exist in this build.
"""

from __future__ import annotations

import itertools
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import models
from db import get_session

router = APIRouter(prefix="/api/v1/treasury/escrow", tags=["escrow"])

_pools: dict[str, dict[str, Any]] = {}
_receipt_ids = itertools.count(1)

MOCK_NOTE = "mock escrow — accounting record only; no funds are held or moved"


def _shares(pool: dict[str, Any]) -> dict[str, int]:
    """Partner -> share of pool in bps; sums to exactly 10000."""
    total = pool["total_usdc"]
    if total <= 0:
        return {}
    raw = {
        partner: int(amount * 10000 // total)
        for partner, amount in pool["contributions"].items()
    }
    residue = 10000 - sum(raw.values())
    if residue and raw:
        largest = max(raw, key=lambda p: pool["contributions"][p])
        raw[largest] += residue
    return raw


def _pool_view(entity_id: str) -> dict[str, Any]:
    pool = _pools[entity_id]
    shares = _shares(pool)
    return {
        "entity_id": entity_id,
        "total_usdc": pool["total_usdc"],
        "receipts": [
            {
                "partner_id": partner,
                "amount_usdc": amount,
                "share_bps": shares.get(partner, 0),
            }
            for partner, amount in pool["contributions"].items()
        ],
        "receipt_history": pool["receipts"],
        "mock": True,
        "custody": MOCK_NOTE,
    }


@router.post("/contribute")
async def contribute(body: dict, db: Session = Depends(get_session)):
    body = body or {}
    entity_id = body.get("entity_id")
    partner_id = body.get("partner_id")
    amount = body.get("amount_usdc")
    if not entity_id or not partner_id:
        raise HTTPException(
            status_code=422, detail="entity_id and partner_id are required"
        )
    if (
        isinstance(amount, bool)
        or not isinstance(amount, (int, float))
        or float(amount) <= 0
    ):
        raise HTTPException(
            status_code=422, detail="amount_usdc must be a positive number"
        )
    pool = _pools.setdefault(
        entity_id, {"total_usdc": 0.0, "contributions": {}, "receipts": []}
    )
    pool["contributions"][partner_id] = (
        pool["contributions"].get(partner_id, 0.0) + float(amount)
    )
    pool["total_usdc"] += float(amount)
    receipt = {
        "receipt_id": f"rcpt-{next(_receipt_ids):04d}",
        "entity_id": entity_id,
        "partner_id": partner_id,
        "agent_id": body.get("agent_id"),
        "amount_usdc": amount,
        "share_bps_after": _shares(pool)[partner_id],
        "pool_total_usdc_after": pool["total_usdc"],
        "mock": True,
        "custody": MOCK_NOTE,
    }
    pool["receipts"].append(receipt)
    db.add(
        models.EventLog(
            aggregate_type="treasury",
            aggregate_id=f"escrow:{entity_id}",
            event_type="treasury.escrow.contribution",
            actor="system",
            payload=receipt,
        )
    )
    db.commit()
    return JSONResponse(content=receipt)


@router.get("/{entity_id}")
async def get_pool(entity_id: str):
    if entity_id not in _pools:
        raise HTTPException(status_code=404, detail="no pool for this entity")
    return JSONResponse(content=_pool_view(entity_id))


@router.post("/{entity_id}/true-up")
async def true_up(entity_id: str, body: dict, db: Session = Depends(get_session)):
    """Compute the balancing transfers that bring contribution
    shares in line with the legal equity split. Returns MOCK
    send/receive instructions; executes nothing."""
    if entity_id not in _pools:
        raise HTTPException(status_code=404, detail="no pool for this entity")
    equity = (body or {}).get("equity_bps")
    if not isinstance(equity, dict) or not equity:
        raise HTTPException(
            status_code=422, detail="equity_bps {partner_id: bps} is required"
        )
    if sum(equity.values()) != 10000:
        raise HTTPException(
            status_code=422, detail="equity_bps must sum to exactly 10000"
        )
    pool = _pools[entity_id]
    total = pool["total_usdc"]
    contributed = pool["contributions"]
    partners = set(contributed) | set(equity)
    # Net position per partner: contributed minus target value.
    nets = {
        p: contributed.get(p, 0.0) - (total * equity.get(p, 0) / 10000.0)
        for p in partners
    }
    senders = sorted(
        ((p, v) for p, v in nets.items() if v > 0.005), key=lambda kv: -kv[1]
    )
    receivers = sorted(
        ((p, -v) for p, v in nets.items() if v < -0.005), key=lambda kv: -kv[1]
    )
    transfers: list[dict[str, Any]] = []
    recv = [[p, amt] for p, amt in receivers]
    for sender, owed in senders:
        remaining = owed
        for entry in recv:
            if remaining <= 0.005:
                break
            if entry[1] <= 0.005:
                continue
            pay = min(remaining, entry[1])
            transfers.append(
                {
                    "from_partner": sender,
                    "to_partner": entry[0],
                    "amount_usdc": round(pay, 2),
                    "rail": "treasury send/receive (mock instruction)",
                    "executed": False,
                }
            )
            remaining -= pay
            entry[1] -= pay
    result = {
        "entity_id": entity_id,
        "pool_total_usdc": total,
        "equity_bps": equity,
        "transfers": transfers,
        "mock": True,
        "custody": MOCK_NOTE,
    }
    db.add(
        models.EventLog(
            aggregate_type="treasury",
            aggregate_id=f"escrow:{entity_id}",
            event_type="treasury.escrow.true_up_computed",
            actor="system",
            payload=result,
        )
    )
    db.commit()
    return JSONResponse(content=result)
