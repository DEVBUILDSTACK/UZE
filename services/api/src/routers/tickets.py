"""Tickets router — issuance, wallet, transfers."""
from fastapi import APIRouter, Depends, HTTPException

from src.auth import require_auth
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("/mine", response_model=APIResponse[list],
            dependencies=[Depends(require_auth)])
async def my_tickets():
    # Privy-authenticated lookup goes here; scaffold returns envelope shape.
    return ok([])


@router.post("/", response_model=APIResponse[dict],
             dependencies=[Depends(require_auth)])
async def issue_ticket(payload: dict):
    ticket = await prisma.ticket.create(data=payload)
    return ok(ticket, message="Ticket issued")


@router.post("/{ticket_id}/transfer", response_model=APIResponse[dict],
             dependencies=[Depends(require_auth)])
async def transfer_ticket(ticket_id: str, payload: dict):
    new_owner = payload.get("ownerId")
    if not new_owner:
        raise HTTPException(status_code=422, detail="ownerId required")
    ticket = await prisma.ticket.update(
        where={"id": ticket_id},
        data={"ownerId": new_owner, "status": "transferred"},
    )
    return ok(ticket, message="Ticket transferred")
