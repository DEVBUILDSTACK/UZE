"""Listings router — UZED.si secondary-market resale."""
from fastapi import APIRouter, Depends, HTTPException

from src.auth import require_auth
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("/", response_model=APIResponse[list])
async def list_listings(limit: int = 20):
    listings = await prisma.listing.find_many(
        where={"status": "active"},
        take=min(limit, 100),
        order={"createdAt": "desc"},
    )
    return ok(listings)


@router.get("/mine", response_model=APIResponse[list],
            dependencies=[Depends(require_auth)])
async def my_listings():
    return ok([])


@router.get("/flagged", response_model=APIResponse[list],
            dependencies=[Depends(require_auth)])
async def flagged_listings():
    listings = await prisma.listing.find_many(where={"status": "flagged"})
    return ok(listings)


@router.get("/{listing_id}", response_model=APIResponse[dict])
async def get_listing(listing_id: str):
    listing = await prisma.listing.find_unique(where={"id": listing_id})
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return ok(listing)


@router.post("/", response_model=APIResponse[dict],
             dependencies=[Depends(require_auth)])
async def create_listing(payload: dict):
    listing = await prisma.listing.create(data=payload)
    await prisma.ticket.update(
        where={"id": payload["ticketId"]}, data={"status": "listed"}
    )
    return ok(listing, message="Listing created")


@router.post("/{listing_id}/buy", response_model=APIResponse[dict],
             dependencies=[Depends(require_auth)])
async def buy_listing(listing_id: str, payload: dict):
    listing = await prisma.listing.find_unique(where={"id": listing_id})
    if listing is None or listing.status != "active":
        raise HTTPException(status_code=404, detail="Listing not available")
    # Settlement (payment, transfer, payout) is team build work; state moves here.
    listing = await prisma.listing.update(
        where={"id": listing_id}, data={"status": "sold"}
    )
    return ok(listing, message="Listing sold")


@router.post("/{listing_id}/moderate", response_model=APIResponse[dict],
             dependencies=[Depends(require_auth)])
async def moderate_listing(listing_id: str, payload: dict):
    action = payload.get("action")  # approve | flag | remove
    status = {"approve": "active", "flag": "flagged",
              "remove": "cancelled"}.get(action)
    if status is None:
        raise HTTPException(status_code=422, detail="Unknown action")
    listing = await prisma.listing.update(
        where={"id": listing_id}, data={"status": status}
    )
    return ok(listing, message=f"Listing {action}d")
