"""UZEmarkets Treasury — on-ramp configuration + Send/Receive.

Implements the corrected Treasury specification (2026-11-11,
under the owner's override of the same day; see
treasury_router.py for the compute-funding half):

  The treasury is permissionless and self-custodial. UZEmarkets
  never touches fiat and holds no customer funds:

  - FIAT ON-RAMP: a third-party fiat provider (debit / ACH /
    bank) routes funds DIRECTLY to the user's self-custodial
    wallet. That is the whole MSB posture: no UZEmarkets money
    transmission, because no UZEmarkets custody. Default target
    is USDC on Solana; alternatives are USDC on Base, Robinhood
    Chain, Ink, or Arc. Amounts follow a fixed increment ladder.
  - SEND & RECEIVE (no off-ramp): funds move P2P and cross-chain
    through the CDP swap router between Solana, Base, Ink,
    Robinhood Chain, Arc, and native NEAR. There is no
    traditional off-ramp in this design.
  - X402 handles the payment rails. X401 handles identity
    verification — and Arc is explicitly a supported network
    for X401 identity-credential routing (see X401_NETWORKS).

  Sourcing (verified 2026-11-11, research note 18):
  - X402 payments / swaps: CDP is the target integration
    (AgentKit is a Sprint 2 build item). The Fundio repo's
    contribution is its CDP ONRAMP SESSION pattern
    (src/app/api/session/route.ts — a JWT-minted onramp session
    token); Fundio contains no AgentKit and no swap module —
    verified by code read, not assumed.
  - X401 identity: Proof's open protocol (draft 0.2.0).
    Credential verification is issuer-key verification over
    HTTP (chain-agnostic); Arc's role is on the settlement
    side of the combined flow. Real x401 verification is
    PENDING RESEARCH — research note 18 carries the findings
    and the integration design (the metering identity seam).
    Until it lands, the identity gate remains the build's
    stub verifier, labelled mock like everything else here.

  Execution state, in the build's standing honest register:
  on-ramp configuration is real validation logic (the ladder
  below is enforced exactly); Send/Receive routing is a MOCK of
  the CDP swap — every payload is labelled `mock: True`, the
  transfer is recorded in the append-only EventLog, and no
  funds move (no keys are held; custody gate A5 is open). When
  a Send/Receive targets NEAR for an agent, the agent's mock
  compute balance (treasury_router) is credited, so the demo
  chain — send USDC, agent funded, inference proceeds — runs
  end to end on the mock state.

CCTP NOTE (2026-11-11, research note 18 Part 4): cross-chain
USDC movement in the production design rides Circle's CCTP.
**CCTP V1 contracts are paused December 1, 2026** (burn limits
falling since Oct 31, 2026) — any bridge integrated into UZE
must be configured on **CCTP V2** (Wormhole Connect current
major, CCTP V2 route explicit, never defaults) and tested
before that date. No CCTP code exists in this stack today;
settlement here is the Chain Signatures / Solana path.

Endpoints:

  POST /api/v1/treasury/onramp/config   {amount, chain?}
  POST /api/v1/treasury/send-receive    {amount, source_chain,
                                         target_chain, agent?,
                                         recipient?}
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import models
import treasury_router
from db import get_session

router = APIRouter(prefix="/api/v1/treasury")

# ------------------------------------------------------------------
# The increment ladder (spec, enforced exactly):
#   $5    – $100   in steps of $5
#   $101  – $250   in steps of $10
#   $251  – $1,750 in steps of $50
#   above $1,750   refused (422)
# ------------------------------------------------------------------
ONRAMP_MIN = 5
ONRAMP_MAX = 1750

# On-ramp target networks: chain -> the asset fiat lands as.
ONRAMP_TARGETS: dict[str, dict[str, str]] = {
    "SOLANA": {"chain": "Solana", "asset": "USDC"},
    "BASE": {"chain": "Base", "asset": "USDC"},
    "ROBINHOOD": {"chain": "Robinhood Chain", "asset": "USDC"},
    "INK": {"chain": "Ink", "asset": "USDC"},
    "ARC": {"chain": "Arc", "asset": "USDC"},
}
DEFAULT_ONRAMP_CHAIN = "SOLANA"

# Send/Receive networks (CDP swap router, mock).
SEND_RECEIVE_CHAINS: dict[str, str] = {
    "SOLANA": "Solana",
    "BASE": "Base",
    "INK": "Ink",
    "ROBINHOOD": "Robinhood Chain",
    "ARC": "Arc",
    "NEAR": "NEAR",
}

# X401 identity routing: Arc is explicitly supported for X401
# identity-credential verification routing (spec, 2026-11-11).
X401_NETWORKS = ["ARC", "SOLANA", "BASE", "INK", "ROBINHOOD", "NEAR"]
X402_RAILS = ["SOLANA", "BASE", "INK", "ROBINHOOD", "ARC", "NEAR"]


def validate_onramp_amount(amount: Any) -> int:
    """Return the amount as an int, or raise ValueError with the
    ladder rule it broke. Amounts are whole dollars."""
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("amount must be a whole-dollar number")
    if float(amount) != int(amount):
        raise ValueError("amount must be a whole-dollar number")
    amount = int(amount)
    if amount < ONRAMP_MIN:
        raise ValueError(f"amount must be at least ${ONRAMP_MIN}")
    if amount > ONRAMP_MAX:
        raise ValueError(
            f"amount exceeds the ${ONRAMP_MAX} on-ramp maximum"
        )
    if amount <= 100:
        if amount % 5 != 0:
            raise ValueError("$5–$100 amounts must be in $5 increments")
    elif amount <= 250:
        if amount % 10 != 0:
            raise ValueError("$101–$250 amounts must be in $10 increments")
    else:
        if amount % 50 != 0:
            raise ValueError("$251–$1,750 amounts must be in $50 increments")
    return amount


def _norm_chain(value: Any) -> str:
    return str(value or "").strip().upper()


@router.post("/onramp/config")
async def onramp_config(body: dict):
    """Validate an on-ramp amount against the increment ladder
    and return the routing configuration: third-party provider,
    direct to the user's self-custodial wallet — UZEmarkets
    never touches the fiat."""
    if "amount" not in (body or {}):
        raise HTTPException(status_code=422, detail="amount is required")
    try:
        amount = validate_onramp_amount(body.get("amount"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    chain_key = _norm_chain(body.get("chain") or DEFAULT_ONRAMP_CHAIN)
    if chain_key not in ONRAMP_TARGETS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"unsupported on-ramp chain: {chain_key} "
                f"(supported: {', '.join(sorted(ONRAMP_TARGETS))})"
            ),
        )
    target = ONRAMP_TARGETS[chain_key]
    return JSONResponse(
        content={
            "amount": amount,
            "currency": "USD",
            "target_chain": target["chain"],
            "target_asset": target["asset"],
            "custody": "self-custodial",
            "fiat_provider": "third-party",
            "uze_touches_fiat": False,
            "off_ramp": False,
            "increments": {
                "tier1": "$5–$100 in $5 steps",
                "tier2": "$101–$250 in $10 steps",
                "tier3": "$251–$1,750 in $50 steps",
            },
            "mock": True,
        }
    )


@router.post("/send-receive")
async def send_receive(body: dict, db: Session = Depends(get_session)):
    """Mock the CDP swap routing for a Send/Receive move.

    Cross-chain moves route through the (mock) CDP swap router;
    same-chain moves are P2P sends. Either way the move is
    recorded in the append-only EventLog. When the target is
    NEAR and an agent is named, the agent's mock compute balance
    is credited with the routed amount (in NEAR), which is what
    lets an agent fund its own inference through this surface.
    """
    body = body or {}
    amount = body.get("amount")
    if (
        isinstance(amount, bool)
        or not isinstance(amount, (int, float))
        or float(amount) <= 0
    ):
        raise HTTPException(
            status_code=422, detail="amount must be a positive number"
        )
    source = _norm_chain(body.get("source_chain"))
    target = _norm_chain(body.get("target_chain"))
    for label, key in (("source_chain", source), ("target_chain", target)):
        if key not in SEND_RECEIVE_CHAINS:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"unsupported {label}: {key or '(missing)'} "
                    f"(supported: {', '.join(sorted(SEND_RECEIVE_CHAINS))})"
                ),
            )
    agent = body.get("agent")
    recipient = body.get("recipient")
    cross_chain = source != target
    credited_near = None
    if target == "NEAR" and agent:
        credited_near = float(amount)
        treasury_router.set_mock_near_balance(
            str(agent),
            treasury_router.get_mock_near_balance(str(agent)) + credited_near,
        )
    record = {
        "amount": amount,
        "source_chain": SEND_RECEIVE_CHAINS[source],
        "target_chain": SEND_RECEIVE_CHAINS[target],
        "route": "cdp-swap" if cross_chain else "p2p-send",
        "cross_chain": cross_chain,
        "agent": str(agent).upper() if agent else None,
        "recipient": recipient,
        "credited_near": credited_near,
        "identity": {
            "protocol": "x401",
            "arc_supported": True,
            "note": (
                "Arc is a supported network for X401 identity "
                "verification routing."
            ),
        },
        "payments": {"protocol": "x402", "rails": X402_RAILS},
        "mock": True,
    }
    db.add(
        models.EventLog(
            aggregate_type="agent" if agent else "treasury",
            aggregate_id=str(agent).upper() if agent else "send-receive",
            event_type="treasury.send_receive",
            actor=f"agent:{str(agent).upper()}" if agent else "human:syndicate",
            payload=record,
        )
    )
    db.commit()
    return JSONResponse(content=record)


# ------------------------------------------------------------------
# NEAR Intents swap route (1Click API).
#
# The cross-chain swap's liquidity route is NEAR Intents via
# the 1Click API (https://1click.chaindefuser.com) — the same
# route the AgentKit ecosystem's cross_chain_swap actions call.
# This route talks to 1Click DIRECTLY: Fundio contains no
# embedded AgentKit to configure (note 35, §0/§4), and a quote
# needs no intermediary. A quote request returns a deposit
# address; the caller's wallet sends the origin asset there;
# the solver network delivers the destination asset. This
# service never holds funds and never sends the deposit — it
# fetches quotes and records them.
#
# Asset IDs below are the 1Click registry's own identifiers,
# pulled live from GET /v0/tokens on 2026-11-11 (229 assets).
# INK IS NOT IN THE 1CLICK REGISTRY (39 chains, no Ink) — Ink
# swap requests are refused with that reason until 1Click
# lists it. NEAR destinations arrive as wNEAR (wrap.near),
# 1Click's NEAR asset.
#
# Credentials: the quote API works without a JWT for standard
# quotes; when ONECLICK_JWT is set in the environment it is
# sent as a Bearer token (higher limits). The token value is
# never logged or returned.
# ------------------------------------------------------------------
import datetime
import json as _json
import os
import urllib.request

ONECLICK_BASE = "https://1click.chaindefuser.com/v0"

# (chain, symbol) -> (1Click assetId, decimals)
ONECLICK_ASSETS: dict[tuple[str, str], tuple[str, int]] = {
    ("SOLANA", "USDC"): (
        "nep141:sol-5ce3bf3a31af18be40ba30f721101b4341690186.omft.near", 6),
    ("SOLANA", "SOL"): ("nep141:sol.omft.near", 9),
    ("BASE", "ETH"): ("nep141:base.omft.near", 18),
    ("BASE", "USDC"): (
        "nep141:base-0x833589fcd6edb6e08f4c7c32d4f71b54bda02913.omft.near", 6),
    ("ETHEREUM", "ETH"): ("nep141:eth.omft.near", 18),
    ("ETHEREUM", "USDC"): (
        "nep141:eth-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48.omft.near", 6),
    ("ROBINHOOD", "USDG"): (
        "nep141:hood-0x5fc5360d0400a0fd4f2af552add042d716f1d168.omft.near", 6),
    ("ROBINHOOD", "ETH"): ("nep141:hood.omft.near", 18),
    ("NEAR", "NEAR"): ("nep141:wrap.near", 24),
    ("NEAR", "USDC"): (
        "nep141:17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1", 6),
}

# Default asset per chain when the caller names only chains.
ONECLICK_DEFAULT_ASSET: dict[str, str] = {
    "SOLANA": "USDC",
    "BASE": "ETH",
    "ETHEREUM": "ETH",
    "ROBINHOOD": "USDG",
    "NEAR": "NEAR",
}


def _oneclick_quote(payload: dict) -> dict:
    """POST /v0/quote against the live 1Click API. Isolated as
    the module's single network seam so tests can stub it."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "uzemarkets-treasury/1click",
    }
    jwt = os.environ.get("ONECLICK_JWT")
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"
    req = urllib.request.Request(
        f"{ONECLICK_BASE}/quote",
        data=_json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return _json.load(resp)


def _resolve_asset(chain: str, symbol: str | None) -> tuple[str, str, int]:
    chain = _norm_chain(chain)
    if chain == "INK":
        raise ValueError(
            "Ink is not listed in the NEAR Intents 1Click registry "
            "yet; swaps to or from Ink cannot be quoted"
        )
    symbol = (symbol or ONECLICK_DEFAULT_ASSET.get(chain, "")).upper()
    entry = ONECLICK_ASSETS.get((chain, symbol))
    if entry is None:
        raise ValueError(
            f"no 1Click asset mapping for {chain}/{symbol or '(default)'}"
        )
    return entry[0], symbol, entry[1]


@router.post("/swap")
async def treasury_swap(body: dict, db: Session = Depends(get_session)):
    """Fetch a NEAR Intents (1Click) quote for a cross-chain
    swap and return the deposit address.

    Both `recipient` and `refund_to` are required (the 1Click
    API demands them even for dry quotes — verified live).
    Unless the caller passes `dry: true`, the quote is WET: it
    carries the deposit address the caller's wallet sends the
    origin asset to. A dry quote returns amounts only. The
    quote is recorded in
    the EventLog either way. If the 1Click API is unreachable,
    the route answers 502 with the mapped request — never a
    fabricated deposit address.
    """
    body = body or {}
    amount = body.get("amount")
    if (
        isinstance(amount, bool)
        or not isinstance(amount, (int, float))
        or float(amount) <= 0
    ):
        raise HTTPException(
            status_code=422, detail="amount must be a positive number"
        )
    try:
        origin_asset, origin_symbol, origin_decimals = _resolve_asset(
            body.get("source_chain") or "", body.get("source_asset")
        )
        dest_asset, dest_symbol, _dest_decimals = _resolve_asset(
            body.get("target_chain") or "", body.get("target_asset")
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    amount_minor = str(int(round(float(amount) * (10 ** origin_decimals))))
    recipient = body.get("recipient")
    refund_to = body.get("refund_to")
    if not recipient or not refund_to:
        # The 1Click API requires both addresses even for dry
        # quotes (verified live 2026-11-11: HTTP 400 naming
        # refundTo / recipient / their type enums).
        raise HTTPException(
            status_code=422,
            detail="recipient and refund_to are required (1Click quote requirement)",
        )
    wet = not bool(body.get("dry"))
    deadline = (
        datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=2)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload: dict[str, Any] = {
        "dry": not wet,
        "swapType": "EXACT_INPUT",
        "originAsset": origin_asset,
        "depositType": "ORIGIN_CHAIN",
        "amount": amount_minor,
        "destinationAsset": dest_asset,
        "slippageTolerance": 100,
        "deadline": deadline,
    }
    payload.update(
        {
            "refundTo": refund_to,
            "refundType": "ORIGIN_CHAIN",
            "recipient": recipient,
            "recipientType": "DESTINATION_CHAIN",
        }
    )
    try:
        resp = _oneclick_quote(payload)
    except Exception as exc:  # network, HTTP, decode — all honest 502s
        raise HTTPException(
            status_code=502,
            detail=(
                f"NEAR Intents 1Click quote failed ({type(exc).__name__}); "
                f"mapped request was origin={origin_asset} "
                f"destination={dest_asset} amount={amount_minor}"
            ),
        )
    quote = resp.get("quote", {}) if isinstance(resp, dict) else {}
    result = {
        "provider": "near-intents-1click",
        "dry": not wet,
        "origin_asset": origin_asset,
        "origin_symbol": origin_symbol,
        "destination_asset": dest_asset,
        "destination_symbol": dest_symbol,
        "amount": amount,
        "amount_in": quote.get("amountIn"),
        "amount_out": quote.get("amountOut"),
        "deposit_address": quote.get("depositAddress"),
        "deposit_memo": quote.get("depositMemo"),
        "deadline": quote.get("deadline") or deadline,
        "mock": False,
    }
    db.add(
        models.EventLog(
            aggregate_type="treasury",
            aggregate_id="swap",
            event_type="treasury.swap_quote",
            actor="system",
            payload=result,
        )
    )
    db.commit()
    return JSONResponse(content=result)
