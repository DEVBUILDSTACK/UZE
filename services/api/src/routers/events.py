"""Events router — UZE domain scaffold. Team fills in business logic."""
from fastapi import APIRouter, HTTPException

from src.db import prisma

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/")
async def list_events(limit: int = 20):
    events = await prisma.event.find_many(take=min(limit, 100),
                                         order={"startsAt": "asc"})
    return {"data": events}


@router.get("/{event_id}")
async def get_event(event_id: str):
    event = await prisma.event.find_unique(where={"id": event_id})
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"data": event}
