"""Auctions router — sealed-bid auction rooms.

Bids are sealed: amounts are revealed only after the auction closes, and
only to operators/admins (S1; §6.1). Bidder IDs come from the token (S3).
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.auth import require_auth, require_role_claims
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/auctions", tags=["auctions"])


class AuctionCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    eventId: str | None = None
    startsAt: datetime
    endsAt: datetime


class BidIn(BaseModel):
    amountCents: int = Field(gt=0)


@router.get("/", response_model=APIResponse[list])
async def list_auctions():
    auctions = await prisma.auction.find_many(order={"endsAt": "asc"})
    return ok(auctions)


@router.get("/{auction_id}", response_model=APIResponse[dict])
async def get_auction(auction_id: str):
    auction = await prisma.auction.find_unique(where={"id": auction_id})
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    return ok(auction)


@router.post("/", response_model=APIResponse[dict])
async def create_auction(
    body: AuctionCreateIn, user_id: str = Depends(require_auth)
):
    if body.endsAt <= body.startsAt:
        raise HTTPException(
            status_code=422, detail="endsAt must be after startsAt"
        )
    auction = await prisma.auction.create(
        data={
            "title": body.title,
            "eventId": body.eventId,
            "startsAt": body.startsAt,
            "endsAt": body.endsAt,
            "status": "scheduled",
        }
    )
    return ok(auction, message="Auction created")


@router.post("/{auction_id}/bid", response_model=APIResponse[dict])
async def place_bid(
    auction_id: str, body: BidIn, user_id: str = Depends(require_auth)
):
    """Place a sealed bid. bidderId comes from the token, never the payload."""
    auction = await prisma.auction.find_unique(where={"id": auction_id})
    if auction is None or auction.status != "open":
        raise HTTPException(status_code=404, detail="Auction not open")
    bid = await prisma.bid.create(
        data={
            "auctionId": auction_id,
            "bidderId": user_id,
            "amountCents": body.amountCents,
        }
    )
    return ok(bid, message="Bid placed")


@router.get("/{auction_id}/bids", response_model=APIResponse[list])
async def auction_bids(
    auction_id: str, claims: dict = Depends(require_role_claims("operator"))
):
    """Sealed-bid reveal: operator view only, and only after the auction
    closes. Admins may read at any time (§6.1)."""
    auction = await prisma.auction.find_unique(where={"id": auction_id})
    if auction is None:
        raise HTTPException(status_code=404, detail="Auction not found")
    ends_at = auction.endsAt
    if ends_at.tzinfo is None:
        ends_at = ends_at.replace(tzinfo=timezone.utc)
    closed = auction.status == "closed" or ends_at <= datetime.now(timezone.utc)
    if claims["role"] != "admin" and not closed:
        raise HTTPException(
            status_code=403,
            detail="Bids are revealed only after the auction closes",
        )
    bids = await prisma.bid.find_many(where={"auctionId": auction_id})
    return ok(bids)
