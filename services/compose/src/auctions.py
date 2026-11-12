"""Arcium auctions + Commitment Ladder (MOCK — no live MPC).

Built 2026-11-11 on the owner's own tap (Directives 7 + 8 of
the evening's scoped set). Two mechanisms, both mock:

COMMITMENT LADDER — a syndicate auction's capital discipline:
partners lock against their target bid on a schedule derived
from the close time:
  30% by T-7 days · 90% by T-72 hours · 100% by T-12 hours.
A partner under the due percentage at a checkpoint falls off
the whitelist. Evaluation takes an explicit `now` so the
schedule is deterministic and testable.

TEMPORAL TRIGGER (the amended, ratified shape) — when the
Delphi market closes, the trigger LOCKS the escrow state,
finalizes the whitelist, and raises a READY_TO_EXECUTE alert.
It does NOT start any auction execution: a human clicks
Execute (POST /execute with human_confirmed: true) before
anything resolves. No Arcium MPC is integrated; the execute
step is a mock reveal of the highest sealed bid.

Sealed bids: amounts are stored server-side and never appear
in any response until a human-confirmed execution reveals the
winner. All state is in-memory (the real EntityPool schema
is the owner's Directive 6, deferred post-demo).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/assign", tags=["auctions"])

# (percent of target bid, time before close)
LADDER = [(30, timedelta(days=7)), (90, timedelta(hours=72)), (100, timedelta(hours=12))]

_auctions: dict[str, dict[str, Any]] = {}
_counter = [0]


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _checkpoints(target: float, close_at: datetime) -> list[dict[str, Any]]:
    return [
        {
            "pct": pct,
            "amount_usdc": round(target * pct / 100, 2),
            "due_at": (close_at - delta).isoformat(),
        }
        for pct, delta in LADDER
    ]


def _view(a: dict[str, Any]) -> dict[str, Any]:
    """Public view — bid amounts stay sealed until execution."""
    view = {
        "auction_id": a["auction_id"],
        "entity_id": a["entity_id"],
        "title": a["title"],
        "target_bid_usdc": a["target_bid_usdc"],
        "close_at": a["close_at"].isoformat(),
        "status": a["status"],
        "ladder": a["ladder"],
        "locks": a["locks"],
        "whitelist": sorted(a["whitelist"]),
        "removed": sorted(a["removed"]),
        "bid_count": len(a["bids"]),
        "alerts": a["alerts"],
        "mock": True,
    }
    if a["status"] == "EXECUTED_MOCK":
        view["result"] = a["result"]
    return view


class AuctionIn(BaseModel):
    entity_id: str
    title: str = ""
    target_bid_usdc: float
    close_at: str


class BidIn(BaseModel):
    partner_id: str
    amount_usdc: float


class LockIn(BaseModel):
    partner_id: str
    amount_usdc: float


class NowIn(BaseModel):
    now: str


class ExecuteIn(BaseModel):
    human_confirmed: bool = False


@router.post("/auctions")
def create_auction(body: AuctionIn):
    if body.target_bid_usdc <= 0:
        raise HTTPException(status_code=422, detail="target_bid_usdc must be positive")
    try:
        close_at = _parse(body.close_at)
    except ValueError:
        raise HTTPException(status_code=422, detail="close_at must be ISO 8601")
    _counter[0] += 1
    auction_id = f"auction-{_counter[0]}"
    a = {
        "auction_id": auction_id,
        "entity_id": body.entity_id,
        "title": body.title,
        "target_bid_usdc": body.target_bid_usdc,
        "close_at": close_at,
        "status": "OPEN",
        "ladder": _checkpoints(body.target_bid_usdc, close_at),
        "locks": {},
        "whitelist": set(),
        "removed": set(),
        "bids": {},
        "alerts": [],
        "result": None,
    }
    _auctions[auction_id] = a
    return _view(a)


def _get(auction_id: str) -> dict[str, Any]:
    a = _auctions.get(auction_id)
    if a is None:
        raise HTTPException(status_code=404, detail="auction not found")
    return a


@router.get("/auctions/{auction_id}")
def get_auction(auction_id: str):
    return _view(_get(auction_id))


@router.post("/auctions/{auction_id}/bids")
def place_bid(auction_id: str, body: BidIn):
    a = _get(auction_id)
    if a["status"] != "OPEN":
        raise HTTPException(status_code=409, detail="auction is not open")
    a["bids"][body.partner_id] = body.amount_usdc
    return {"sealed": True, "bid_count": len(a["bids"]), "mock": True}


@router.post("/auctions/{auction_id}/lock")
def lock_capital(auction_id: str, body: LockIn):
    a = _get(auction_id)
    if a["status"] != "OPEN":
        raise HTTPException(status_code=409, detail="auction is not open")
    total = a["locks"].get(body.partner_id, 0.0) + body.amount_usdc
    a["locks"][body.partner_id] = total
    if body.partner_id not in a["removed"]:
        a["whitelist"].add(body.partner_id)
    pct = round(100.0 * total / a["target_bid_usdc"], 2)
    return {
        "partner_id": body.partner_id,
        "locked_total_usdc": total,
        "locked_pct": pct,
        "whitelisted": body.partner_id in a["whitelist"],
        "mock": True,
    }


@router.post("/auctions/{auction_id}/evaluate")
def evaluate_ladder(auction_id: str, body: NowIn):
    """Apply the ladder at `now`: partners below the due
    percentage lose the whitelist."""
    a = _get(auction_id)
    try:
        now = _parse(body.now)
    except ValueError:
        raise HTTPException(status_code=422, detail="now must be ISO 8601")
    due_pct = 0
    for cp in a["ladder"]:
        if now >= _parse(cp["due_at"]):
            due_pct = max(due_pct, cp["pct"])
    for partner, locked in list(a["locks"].items()):
        pct = 100.0 * locked / a["target_bid_usdc"]
        if pct < due_pct and partner in a["whitelist"]:
            a["whitelist"].discard(partner)
            a["removed"].add(partner)
    return {"due_pct": due_pct, **_view(a)}


@router.post("/auctions/{auction_id}/close")
def close_auction(auction_id: str):
    """The Temporal Trigger: close LOCKS the escrow state and
    raises READY_TO_EXECUTE. It executes nothing — a human
    must confirm on /execute."""
    a = _get(auction_id)
    if a["status"] != "OPEN":
        raise HTTPException(status_code=409, detail="auction is not open")
    a["status"] = "READY_TO_EXECUTE"
    a["alerts"].append(
        {"type": "READY_TO_EXECUTE", "auction_id": auction_id, "mock": True}
    )
    return {**_view(a), "executed": False}


@router.post("/auctions/{auction_id}/execute")
def execute_auction(auction_id: str, body: ExecuteIn):
    a = _get(auction_id)
    if not body.human_confirmed:
        raise HTTPException(
            status_code=422,
            detail="human Execute confirmation required — no auto-execution",
        )
    if a["status"] != "READY_TO_EXECUTE":
        raise HTTPException(
            status_code=409, detail="auction must be closed (READY_TO_EXECUTE) first"
        )
    a["status"] = "EXECUTED_MOCK"
    if a["bids"]:
        winner, amount = max(a["bids"].items(), key=lambda kv: kv[1])
        a["result"] = {"winner": winner, "winning_bid_usdc": amount, "revealed": True}
    else:
        a["result"] = {"winner": None, "winning_bid_usdc": None, "revealed": True}
    return _view(a)
