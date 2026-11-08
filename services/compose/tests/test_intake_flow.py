"""The intake flow end-to-end through the FastAPI app (TestClient):
create -> missing slots reported -> answer -> module readiness flips.
Runs against the real migrated schema (see conftest's substrate
docstring) with the Sprint 1 seed manifest active.
"""

from __future__ import annotations


def test_health_reports_schema_head(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] is True
    assert body["schemaRevision"] == "7cef249c9b40"


def test_intake_flow_readiness_flips(client):
    created = client.post("/intakes", json={"answers": {}})
    assert created.status_code == 201
    view = created.json()
    intake_id = view["id"]
    # Every required applicable slot is missing; the deferrable tier
    # is deferred; the stay dates sit on an untaken branch.
    assert view["missingSlots"] == ["event.city", "party.seats", "stay.needed"]
    assert view["deferredSlots"] == ["tickets.tier"]
    assert view["notApplicableSlots"] == ["stay.checkin", "stay.checkout"]
    assert view["moduleReadiness"] == {"STAY": "NOT_READY", "TICKETS": "NOT_READY"}

    step1 = client.post(
        f"/intakes/{intake_id}/answers",
        json={"answers": {
            "event.city": "Miami", "party.seats": 2, "stay.needed": True,
        }},
    )
    assert step1.status_code == 200
    view = step1.json()
    # TICKETS flips READY; answering stay.needed=true OPENS the stay
    # branch, so check-in becomes missing and STAY stays NOT_READY.
    assert view["moduleReadiness"]["TICKETS"] == "READY"
    assert view["missingSlots"] == ["stay.checkin"]
    assert view["moduleReadiness"]["STAY"] == "NOT_READY"

    step2 = client.post(
        f"/intakes/{intake_id}/answers",
        json={"answers": {"stay.checkin": "2026-11-06"}},
    )
    view = step2.json()
    assert view["missingSlots"] == []
    assert view["moduleReadiness"] == {"STAY": "READY", "TICKETS": "READY"}
    assert view["deferredSlots"] == ["tickets.tier", "stay.checkout"]

    # The read path recomputes the same classification — identical view.
    fetched = client.get(f"/intakes/{intake_id}")
    assert fetched.status_code == 200
    assert fetched.json() == view


def test_answers_merge_correct_and_delete(client):
    created = client.post(
        "/intakes",
        json={"answers": {
            "event.city": "Miami", "party.seats": 99, "stay.needed": False,
        }},
    )
    view = created.json()
    intake_id = view["id"]
    assert view["invalidSlots"] == {"party.seats": "max"}
    assert view["moduleReadiness"]["TICKETS"] == "NOT_READY"

    fixed = client.post(
        f"/intakes/{intake_id}/answers", json={"answers": {"party.seats": 4}}
    )
    assert fixed.json()["invalidSlots"] == {}
    assert fixed.json()["moduleReadiness"]["TICKETS"] == "READY"

    # A null value deletes the answer — the slot goes back to missing.
    deleted = client.post(
        f"/intakes/{intake_id}/answers", json={"answers": {"party.seats": None}}
    )
    assert deleted.json()["missingSlots"] == ["party.seats"]


def test_unknown_intake_is_404(client):
    assert client.get("/intakes/nope").status_code == 404
    resp = client.post("/intakes/nope/answers", json={"answers": {}})
    assert resp.status_code == 404


def test_token_collision_is_409(client):
    first = client.post("/intakes", json={"answers": {}, "token": "resume-1"})
    assert first.status_code == 201
    second = client.post("/intakes", json={"answers": {}, "token": "resume-1"})
    assert second.status_code == 409
