"""Events router — UZE domain. All responses use the APIResponse envelope."""
from fastapi import APIRouter, Depends, HTTPException

from src.auth import require_auth
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=APIResponse[list])
async def list_events(limit: int = 20):
    events = await prisma.event.find_many(
        take=min(limit, 100), order={"startsAt": "asc"}
    )
    return ok(events)


@router.get("/{event_id}", response_model=APIResponse[dict])
async def get_event(event_id: str):
    event = await prisma.event.find_unique(where={"id": event_id})
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return ok(event)


@router.post("/", response_model=APIResponse[dict],
             dependencies=[Depends(require_auth)])
async def create_event(payload: dict):
    event = await prisma.event.create(data=payload)
    return ok(event, message="Event created")
