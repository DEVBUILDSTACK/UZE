"""Listings router — UZED.si secondary-market resale.

Ownership is enforced: sellers are taken from the token, ticket ownership is
verified on create, and buying stays 501 until settlement exists (S3; §5.2).
Moderation and the flagged queue are operator-only (S1; §6.1).
"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.auth import require_auth, require_role
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/listings", tags=["listings"])


class ListingCreateIn(BaseModel):
    ticketId: str
    priceCents: int = Field(gt=0)
    feeCents: int = Field(default=0, ge=0)


class ModerateIn(BaseModel):
    action: Literal["approve", "flag", "remove"]


@router.get("/", response_model=APIResponse[list])
async def list_listings(limit: int = 20):
    listings = await prisma.listing.find_many(
        where={"status": "active"},
        take=min(limit, 100),
        order={"createdAt": "desc"},
    )
    return ok(listings)


@router.get("/mine", response_model=APIResponse[list])
async def my_listings(user_id: str = Depends(require_auth)):
    listings = await prisma.listing.find_many(
        where={"sellerId": user_id},
        order={"createdAt": "desc"},
    )
    return ok(listings)


@router.get("/flagged", response_model=APIResponse[list])
async def flagged_listings(user_id: str = Depends(require_role("operator"))):
    listings = await prisma.listing.find_many(where={"status": "flagged"})
    return ok(listings)


@router.get("/{listing_id}", response_model=APIResponse[dict])
async def get_listing(listing_id: str):
    listing = await prisma.listing.find_unique(where={"id": listing_id})
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return ok(listing)


@router.post("/", response_model=APIResponse[dict])
async def create_listing(
    body: ListingCreateIn, user_id: str = Depends(require_auth)
):
    """List a ticket the caller owns. sellerId comes from the token."""
    ticket = await prisma.ticket.find_unique(where={"id": body.ticketId})
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.ownerId != user_id:
        raise HTTPException(
            status_code=403, detail="You can only list tickets you own"
        )
    if ticket.status != "active":
        raise HTTPException(
            status_code=409, detail="Ticket is not in a listable state"
        )
    listing = await prisma.listing.create(
        data={
            "ticketId": body.ticketId,
            "sellerId": user_id,
            "priceCents": body.priceCents,
            "feeCents": body.feeCents,
            "status": "active",
        }
    )
    await prisma.ticket.update(
        where={"id": body.ticketId}, data={"status": "listed"}
    )
    return ok(listing, message="Listing created")


@router.post("/{listing_id}/buy", response_model=APIResponse[dict])
async def buy_listing(
    listing_id: str, user_id: str = Depends(require_auth)
):
    # Settlement (payment, transfer, payout) is not built yet. Marking a
    # listing "sold" with no payment is a P0 mass-assignment hole (S3; §5.2).
    raise HTTPException(
        status_code=501, detail="Buying is unavailable until settlement exists"
    )


@router.post("/{listing_id}/moderate", response_model=APIResponse[dict])
async def moderate_listing(
    listing_id: str,
    body: ModerateIn,
    user_id: str = Depends(require_role("operator")),
):
    status = {"approve": "active", "flag": "flagged",
              "remove": "cancelled"}[body.action]
    listing = await prisma.listing.update(
        where={"id": listing_id}, data={"status": status}
    )
    return ok(listing, message=f"Listing {body.action}d")
