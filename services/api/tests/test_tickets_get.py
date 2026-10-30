"""GET /tickets/{ticket_id} — the single-ticket read R4 reconciliation uses.

Substrate: mocked Prisma. The router's `prisma` object is replaced with an
in-memory fake (find_unique over a dict of attribute-access records, like
the real client's), so these tests exercise the route, its 404 style, the
APIResponse envelope, and the narrowed response shape without a database.
"""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routers import tickets as tickets_router

TICKET = {
    "id": "t-123",
    "eventId": "evt-1",
    "ownerId": "user-9",
    "tier": "vip",
    "status": "listed",
    "createdAt": datetime(2026, 10, 30, tzinfo=timezone.utc),
    "updatedAt": datetime(2026, 10, 30, tzinfo=timezone.utc),
}


class _FakeTicketTable:
    def __init__(self, rows):
        self._rows = rows

    async def find_unique(self, where):
        return self._rows.get(where["id"])


class _FakePrisma:
    def __init__(self, rows):
        self.ticket = _FakeTicketTable(rows)


@pytest.fixture()
def client(monkeypatch):
    record = SimpleNamespace(**TICKET)
    monkeypatch.setattr(
        tickets_router, "prisma", _FakePrisma({TICKET["id"]: record})
    )
    app = FastAPI()
    app.include_router(tickets_router.router)
    return TestClient(app)


def test_get_ticket_returns_record(client):
    res = client.get("/tickets/t-123")
    assert res.status_code == 200
    body = res.json()
    assert body["status_code"] == 200
    data = body["data"]
    # Exactly the four fields R4 reconciliation consumes — the stored
    # record also carries ownerId, createdAt, and updatedAt, and none of
    # them may leak.
    assert set(data.keys()) == {"id", "eventId", "tier", "status"}
    assert data["id"] == "t-123"
    assert data["eventId"] == "evt-1"
    assert data["tier"] == "vip"
    # "listed", not just "active": the read returns the *current* state,
    # which is what commit-time reconciliation compares against.
    assert data["status"] == "listed"


def test_get_ticket_unknown_id_is_404(client):
    res = client.get("/tickets/nope")
    assert res.status_code == 404
    assert res.json()["detail"] == "Ticket not found"


def test_mine_still_routes_to_wallet_not_by_id(client):
    # /mine is declared before /{ticket_id}; without a token it must hit
    # require_auth (401), not the by-id read (which would 404 "nope"-style).
    res = client.get("/tickets/mine")
    assert res.status_code == 401
