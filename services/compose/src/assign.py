"""UZE Assign — the assignment marketplace surface (MOCK).

Built 2026-11-11 on the owner's tap ("Build the Assign
expansion + contribution receipts as mocks now"). Record note:
no AssignmentContract existed anywhere in the compose schema
or the generated schema family before this module — despite
the directive's "expand the schema" framing, UZE Assign is
CREATED here, as a mock, with the Directive 2 category set.

  - Listings carry one of nine categories (ASSIGN_CATEGORIES).
    Unknown categories are refused 422 — the category set is a
    closed vocabulary, extended only by a filed change.
  - Listings and bids live in an in-memory registry and are
    written to the append-only EventLog (assign.listing_created
    / assign.bid_placed) as the audit surface. There is NO
    custody, NO escrow, NO settlement in this module: a bid is
    a recorded expression, and closing a listing is out of
    scope for the mock. Every payload says so (mock: true).
  - Deliberately NOT in SUBMISSION.md: the owner's 2026-11-10
    scope ruling keeps the hackathon narrative B2B agentic/RWA;
    categories like SECONDARY_TICKETS and COLLECTIBLE_CARDS
    stay an internal build item until he rules otherwise.
"""

from __future__ import annotations

import itertools
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import models
from db import get_session

router = APIRouter(prefix="/api/v1/assign", tags=["assign"])

# The Directive 2 category set (closed vocabulary).
ASSIGN_CATEGORIES: tuple[str, ...] = (
    "REAL_ESTATE_CONTRACT",
    "OPERATING_BUSINESS",
    "DEFUNCT_BUSINESS",
    "BANKRUPTCY_ESTATE",
    "COLLECTIBLE_CARDS",
    "FINE_ART",
    "VEHICLES",
    "ON_CHAIN_NFT",
    "SECONDARY_TICKETS",
)

_listings: dict[str, dict[str, Any]] = {}
_ids = itertools.count(1)


def _log(db: Session, aggregate_id: str, event_type: str, payload: dict) -> None:
    db.add(
        models.EventLog(
            aggregate_type="assign",
            aggregate_id=aggregate_id,
            event_type=event_type,
            actor="system",
            payload=payload,
        )
    )
    db.commit()


@router.get("/categories")
async def assign_categories():
    return {"categories": list(ASSIGN_CATEGORIES), "mock": True}


@router.post("/listings")
async def create_listing(body: dict, db: Session = Depends(get_session)):
    body = body or {}
    category = str(body.get("category") or "").upper()
    if category not in ASSIGN_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"unknown assignment category {category!r}; "
                f"the category set is closed: {', '.join(ASSIGN_CATEGORIES)}"
            ),
        )
    title = body.get("title")
    if not title or not isinstance(title, str):
        raise HTTPException(status_code=422, detail="title is required")
    listing_id = f"assign-{next(_ids):04d}"
    listing = {
        "listing_id": listing_id,
        "category": category,
        "title": title,
        "entity_id": body.get("entity_id"),
        "reserve_price_usdc": body.get("reserve_price_usdc"),
        "status": "OPEN",
        "bids": [],
        "mock": True,
        "custody": "none — mock listing; no asset or funds are held",
    }
    _listings[listing_id] = listing
    _log(db, listing_id, "assign.listing_created", listing)
    return JSONResponse(content=listing)


@router.get("/listings")
async def list_listings(category: str | None = None):
    items = list(_listings.values())
    if category:
        items = [i for i in items if i["category"] == category.upper()]
    return {"listings": items, "count": len(items), "mock": True}


@router.post("/listings/{listing_id}/bids")
async def place_bid(
    listing_id: str, body: dict, db: Session = Depends(get_session)
):
    listing = _listings.get(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="listing not found")
    body = body or {}
    amount = body.get("amount_usdc")
    if (
        isinstance(amount, bool)
        or not isinstance(amount, (int, float))
        or float(amount) <= 0
    ):
        raise HTTPException(
            status_code=422, detail="amount_usdc must be a positive number"
        )
    bidder = body.get("bidder")
    if not bidder:
        raise HTTPException(status_code=422, detail="bidder is required")
    bid = {
        "bidder": bidder,
        "amount_usdc": amount,
        "mock": True,
        "settlement": "none — mock bid; no funds move",
    }
    listing["bids"].append(bid)
    _log(db, listing_id, "assign.bid_placed", bid)
    return JSONResponse(
        content={"listing_id": listing_id, "bid": bid, "bid_count": len(listing["bids"])}
    )
