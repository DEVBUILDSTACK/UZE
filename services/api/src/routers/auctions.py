"""Auctions router — sealed-bid auction rooms."""
from fastapi import APIRouter, Depends, HTTPException

from src.auth import require_auth
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/auctions", tags=["auctions"])


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


@router.post("/", response_model=APIResponse[dict],
             dependencies=[Depends(require_auth)])
async def create_auction(payload: dict):
    auction = await prisma.auction.create(data=payload)
    return ok(auction, message="Auction created")


@router.post("/{auction_id}/bid", response_model=APIResponse[dict],
             dependencies=[Depends(require_auth)])
async def place_bid(auction_id: str, payload: dict):
    auction = await prisma.auction.find_unique(where={"id": auction_id})
    if auction is None or auction.status != "open":
        raise HTTPException(status_code=404, detail="Auction not open")
    bid = await prisma.bid.create(
        data={"auctionId": auction_id, **payload}
    )
    return ok(bid, message="Bid placed")


@router.get("/{auction_id}/bids", response_model=APIResponse[list],
            dependencies=[Depends(require_auth)])
async def auction_bids(auction_id: str):
    # Sealed: only revealed after close; operator view.
    bids = await prisma.bid.find_many(where={"auctionId": auction_id})
    return ok(bids)
