"""Tickets router — issuance, wallet, transfers, by-id read.

Owner IDs come from the token, never the payload; transfers require current
ownership (S3). The by-id read is public, like the single-resource reads in
the events and listings routers; R4's commit-time reconciliation reads a
ticket's current state through it. Its response is narrowed to exactly the
five fields reconciliation consumes (id, eventId, ownerId, tier, status) —
a least-field response for a server-to-server read.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.auth import require_auth
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/tickets", tags=["tickets"])


class TicketIssueIn(BaseModel):
    eventId: str
    tier: str = Field(default="general", max_length=50)


class TransferIn(BaseModel):
    ownerId: str


@router.get("/mine", response_model=APIResponse[list])
async def my_tickets(user_id: str = Depends(require_auth)):
    tickets = await prisma.ticket.find_many(
        where={"ownerId": user_id}, order={"createdAt": "desc"}
    )
    return ok(tickets)


@router.get("/{ticket_id}", response_model=APIResponse[dict])
async def get_ticket(ticket_id: str):
    ticket = await prisma.ticket.find_unique(where={"id": ticket_id})
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    # Narrowed to the fields R4 reconciliation consumes — nothing else the
    # record carries (createdAt, updatedAt, ...) leaves this endpoint.
    return ok(
        {
            "id": ticket.id,
            "eventId": ticket.eventId,
            "ownerId": ticket.ownerId,
            "tier": ticket.tier,
            "status": ticket.status,
        }
    )


@router.post("/", response_model=APIResponse[dict])
async def issue_ticket(
    body: TicketIssueIn, user_id: str = Depends(require_auth)
):
    """Issue a ticket to the caller. ownerId comes from the token."""
    event = await prisma.event.find_unique(where={"id": body.eventId})
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    ticket = await prisma.ticket.create(
        data={
            "eventId": body.eventId,
            "ownerId": user_id,
            "tier": body.tier,
            "status": "active",
        }
    )
    return ok(ticket, message="Ticket issued")


@router.post("/{ticket_id}/transfer", response_model=APIResponse[dict])
async def transfer_ticket(
    ticket_id: str, body: TransferIn, user_id: str = Depends(require_auth)
):
    """Transfer a ticket the caller owns."""
    ticket = await prisma.ticket.find_unique(where={"id": ticket_id})
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.ownerId != user_id:
        raise HTTPException(
            status_code=403, detail="Only the ticket owner can transfer it"
        )
    ticket = await prisma.ticket.update(
        where={"id": ticket_id},
        data={"ownerId": body.ownerId, "status": "transferred"},
    )
    return ok(ticket, message="Ticket transferred")
