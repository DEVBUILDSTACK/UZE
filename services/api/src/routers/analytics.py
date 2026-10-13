"""Analytics router — ops KPIs for the Command Center dashboard."""
from fastapi import APIRouter, Depends

from src.auth import require_auth
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=APIResponse[dict],
            dependencies=[Depends(require_auth)])
async def overview():
    events = await prisma.event.count()
    tickets = await prisma.ticket.count()
    listings = await prisma.listing.count()
    auctions = await prisma.auction.count()
    return ok({
        "events": events,
        "tickets": tickets,
        "activeListings": listings,
        "auctions": auctions,
    })
