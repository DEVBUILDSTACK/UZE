"""Persisted underwrite reports — HTTP surface (2026-11-13).

Pins the report lifecycle wired through the three doors'
shared core (underwrite_reports): POST /api/v1/ingest/
multiyear persists a report and returns its receipt;
GET /api/v1/underwrite/reports/{id} reads the same stored
analysis back; the PDF door renders it; the notifications
door returns the two queued beats in order; an unknown
prior report is the labelled PRIOR_NOT_FOUND delta state,
never a failure; and the email door persists its SURA
assessment with claim_id None (the mock-extraction rule:
no claim is ever issued from a mock).

Fixtures are synthetic and modeled on
tests/test_comp_benchmark.py (SUBJECT / COMPS / YEARS).
"""

from __future__ import annotations

import base64
import re

SENDER = "owner@example.com"

SUBJECT = {
    "property_type": "Garden Style",
    "year_built": 2005,
    "property_class": "B",
    "unit_count": 100,
    "micro_region": "baltimore-washington",
}

SUBJECT_ITEMS = {
    "Market Rent Potential": 1_200_000,
    "Parking": 10_000,
    "Vacancy Loss": -60_000,
    "Repairs & Maintenance": 150_000,
    "Property Taxes": 90_000,
    "Insurance": 30_000,
}


def _comp(name, units, items, *, year=2004, ptype="GARDEN_STYLE",
          pclass="B", region="baltimore-washington"):
    return {
        "name": name,
        "profile": {
            "property_type": ptype,
            "year_built": year,
            "property_class": pclass,
            "unit_count": units,
            "micro_region": region,
        },
        "line_items": items,
    }


COMPS = [
    _comp("Comp One", 80, {
        "Market Rent Potential": 1_040_000, "Parking": 16_000,
        "Vacancy Loss": -40_000, "R&M": 96_000,
    }),
    _comp("Comp Two", 120, {
        "Market Rent Potential": 1_560_000, "Parking": 24_000,
        "Vacancy Loss": -60_000, "Repairs and Maintenance": 144_000,
    }),
]

YEARS = [
    {"period": "2024", "line_items": {
        "Rental Income": 900_000, "Repairs & Maintenance": 120_000,
    }},
    {"period": "2025", "line_items": SUBJECT_ITEMS},
]

# Latest-period NOI, computed independently of the code
# under test: (1,200,000 + 10,000 - 60,000) revenue
# - 150,000 OpEx - 90,000 taxes - 30,000 insurance.
EXPECTED_LATEST_NOI = 880_000


def _post_multiyear(client, **overrides):
    payload = {
        "years": YEARS,
        "subject_profile": SUBJECT,
        "comps": COMPS,
        "sender_email": SENDER,
    }
    payload.update(overrides)
    return client.post("/api/v1/ingest/multiyear", json=payload)


def test_multiyear_post_persists_and_returns_receipt(client):
    r = _post_multiyear(client)
    assert r.status_code == 200
    body = r.json()
    receipt = body["receipt"]
    assert receipt["report_id"].startswith("uwr_")
    assert re.fullmatch(r"[0-9a-f]{64}", receipt["input_hash"])
    assert receipt["engine_version"]
    # The analysis itself is present and arithmetically pinned.
    assert body["periods"][-1]["period"] == "2025"
    assert body["periods"][-1]["noi"] == EXPECTED_LATEST_NOI
    # Beat 1 rides the response when a sender was supplied.
    beat1 = body["notification_beat1"]
    assert beat1["to"] == SENDER
    assert beat1["status"] == "QUEUED"


def test_get_report_returns_the_stored_analysis(client):
    posted = _post_multiyear(client).json()
    report_id = posted["receipt"]["report_id"]
    r = client.get(f"/api/v1/underwrite/reports/{report_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["receipt"]["report_id"] == report_id
    assert body["receipt"]["input_hash"] == posted["receipt"]["input_hash"]
    assert body["periods"] == posted["periods"]
    assert body["periods"][-1]["noi"] == EXPECTED_LATEST_NOI
    assert body["report"]["id"] == report_id


def test_get_unknown_report_is_404_report_not_found(client):
    r = client.get("/api/v1/underwrite/reports/uwr_missing")
    assert r.status_code == 404
    assert "REPORT_NOT_FOUND" in r.json()["detail"]
    r = client.get("/api/v1/underwrite/reports/uwr_missing/pdf")
    assert r.status_code == 404
    assert "REPORT_NOT_FOUND" in r.json()["detail"]
    r = client.get("/api/v1/underwrite/reports/uwr_missing/notifications")
    assert r.status_code == 404
    assert "REPORT_NOT_FOUND" in r.json()["detail"]


def test_get_report_pdf_renders_a_real_pdf(client):
    posted = _post_multiyear(client).json()
    report_id = posted["receipt"]["report_id"]
    r = client.get(f"/api/v1/underwrite/reports/{report_id}/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")


def test_notifications_are_the_two_beats_in_order(client):
    posted = _post_multiyear(client).json()
    report_id = posted["receipt"]["report_id"]
    r = client.get(f"/api/v1/underwrite/reports/{report_id}/notifications")
    assert r.status_code == 200
    body = r.json()
    assert body["report_id"] == report_id
    notes = body["notifications"]
    assert len(notes) == 2
    assert notes[0]["beat"] < notes[1]["beat"]  # ordered by beat
    assert all(n["status"] == "QUEUED" for n in notes)
    assert all(n["report_id"] == report_id for n in notes)
    assert notes[0]["to"] == SENDER


def test_unknown_prior_report_is_labelled_not_fatal(client):
    r = _post_multiyear(client, prior_report_id="uwr_missing")
    assert r.status_code == 200
    body = r.json()
    assert body["delta"]["status"] == "PRIOR_NOT_FOUND"
    # The analysis still ran and persisted.
    assert body["periods"][-1]["noi"] == EXPECTED_LATEST_NOI
    assert body["receipt"]["report_id"].startswith("uwr_")


def test_email_door_persists_with_no_claim_from_the_mock(client):
    r = client.post(
        "/api/v1/ingest/email",
        json={
            "subject": "HiCRE T-12 for the Brickell hotel",
            "sender": SENDER,
            "attachment_base64": base64.b64encode(
                b"%PDF-1.4 fake client statement"
            ).decode(),
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["agent"] == "SURA"
    # The pre-existing response fields are untouched.
    assert base64.b64decode(body["pdf_base64"]).startswith(b"%PDF")
    # Persistence is additive: a receipt whose claim_id is
    # None — the mock extraction never issues a claim.
    receipt = body["receipt"]
    assert receipt["report_id"].startswith("uwr_")
    assert receipt["claim_id"] is None
    assert body["notification_beat1"]["to"] == SENDER
    assert body["notification_beat1"]["status"] == "QUEUED"
