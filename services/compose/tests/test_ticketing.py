"""Ticketing + Delphi mock layer (owner override integration, 2026-11-12).

Covers: venue-as-data events, per-seat minting, the provenance
invariant on transfer (same id, no re-mint), holder-gated Delphi
calls, the scalar->threshold market derivation, and mock bridge
intents. All state is the module's in-memory mock store.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "generated"))

from fastapi.testclient import TestClient  # noqa: E402

from app import create_app  # noqa: E402

client = TestClient(create_app(), raise_server_exceptions=False)

W1 = "0xwallet00000000000000000000000000000001"
W2 = "0xwallet00000000000000000000000000000002"
FOCUS = {"event_id": "soccer", "sector": "Tribuna Central", "ring": "Lower Ring"}


def _mint(wallet=W1, qty=4):
    r = client.post("/api/v1/ticketing/mint", json={**FOCUS, "qty": qty, "wallet": wallet, "row": 5, "seat_start": 1})
    assert r.status_code == 200, r.text
    return r.json()


def test_events_are_venue_as_data():
    r = client.get("/api/v1/ticketing/events")
    assert r.status_code == 200
    ids = {e["id"] for e in r.json()["events"]}
    assert {"soccer", "music", "summit", "f1-miami", "f1-vegas", "f1-austin", "la28"} <= ids
    assert r.json()["status"] == "mock"


def test_per_seat_minting():
    out = _mint()
    tickets = out["tickets"]
    assert len(tickets) == 4
    assert len({t["id"] for t in tickets}) == 4  # distinct token ids
    assert out["unitPrice"] == 483  # 420 base x 1.15 Lower Ring
    assert all(t["price"] == 483 for t in tickets)  # unit price per seat, not a package total
    assert [t["seat"] for t in tickets] == [1, 2, 3, 4]


def test_transfer_keeps_id_and_appends_provenance():
    t = _mint(qty=1)["tickets"][0]
    r = client.post("/api/v1/ticketing/transfer", json={"ticket_id": t["id"], "to_wallet": W2})
    assert r.status_code == 409  # not listed yet
    r = client.post("/api/v1/ticketing/list", json={"ticket_id": t["id"], "wallet": W1, "price": 662})
    assert r.status_code == 200
    r = client.post("/api/v1/ticketing/transfer", json={"ticket_id": t["id"], "to_wallet": W2})
    assert r.status_code == 200
    moved = r.json()["ticket"]
    assert moved["id"] == t["id"]  # provenance invariant: same token, no re-mint
    assert moved["owner"] == W2 and moved["acquiredVia"] == "secondary"
    assert len(moved["provenance"]) == 2
    v = client.get(f"/api/v1/ticketing/verify/{t['id']}")
    assert v.json()["genuine"] is True and v.json()["currentOwner"] == W2


def test_delphi_call_requires_primary_holding():
    r = client.post("/api/v1/delphi/calls", json={**FOCUS, "wallet": "0xstranger000000000000000000000000000099", "call": 600})
    assert r.status_code == 403
    _mint(wallet=W2, qty=1)
    r = client.post("/api/v1/delphi/calls", json={**FOCUS, "wallet": W2, "call": 600})
    assert r.status_code == 200


def test_threshold_markets_derive_from_call_stream():
    _mint(wallet=W1, qty=1)
    client.post("/api/v1/delphi/calls", json={**FOCUS, "wallet": W1, "call": 600})
    r = client.get("/api/v1/delphi/markets", params=FOCUS)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "mock_proposed" and body["callsObserved"] >= 6  # 5 seeded + W1 (+W2 if ordered after)
    assert body["markets"], "expected a derived threshold ladder"
    m = body["markets"][0]
    assert "Tribuna Central" in m["question"] and m["outcomes"] == ["Yes", "No"]
    assert 0.0 <= m["initialYes"] <= 1.0
    assert "clearing price" in m["resolutionSource"]


def test_bridge_intent_is_a_mock_record():
    t = _mint(qty=1)["tickets"][0]
    r = client.post("/api/v1/ticketing/bridge-intents", json={"ticket_id": t["id"], "to_chain": "solana"})
    assert r.status_code == 200
    rec = r.json()["bridgeIntent"]
    assert rec["fromChain"] == "near" and rec["toChain"] == "solana"
    assert rec["status"] == "mock_recorded"
    r = client.post("/api/v1/ticketing/bridge-intents", json={"ticket_id": t["id"], "to_chain": "dogechain"})
    assert r.status_code == 422


def test_unknown_event_and_sector_rejected():
    r = client.post("/api/v1/ticketing/mint", json={"event_id": "nope", "sector": "X", "ring": "Y", "qty": 1, "wallet": W1})
    assert r.status_code == 422
    r = client.post("/api/v1/ticketing/mint", json={**FOCUS, "sector": "Nope", "qty": 1, "wallet": W1})
    assert r.status_code == 422
