"""Events router — UZE domain. All responses use the APIResponse envelope.

Event creation is operator-only (S1; §6.1); inputs are typed (S3).
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.auth import require_role
from src.db import prisma
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/events", tags=["events"])


class EventCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    venue: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    startsAt: datetime


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


@router.post("/", response_model=APIResponse[dict])
async def create_event(
    body: EventCreateIn, user_id: str = Depends(require_role("operator"))
):
    event = await prisma.event.create(
        data={
            "title": body.title,
            "venue": body.venue,
            "city": body.city,
            "startsAt": body.startsAt,
        }
    )
    return ok(event, message="Event created")
