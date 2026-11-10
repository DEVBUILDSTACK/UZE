"""Agentic Email Gateway (directed build, 2026-11-10; demo scope).

Pins the directed contract: subject-keyword routing to the track's
underwriting agent, a 422 with the exact error body when no track
can be determined, and a real one-page PDF (base64) in the success
response. The extraction is a mock by design (see
src/email_gateway.py) — these tests pin routing, contract, and
PDF generation, NOT OCR accuracy, which does not exist yet.
"""

from __future__ import annotations

import base64

ATTACHMENT = base64.b64encode(b"%PDF-1.4 fake client statement").decode()


def _post(client, subject: str):
    return client.post(
        "/api/v1/ingest/email",
        json={
            "subject": subject,
            "sender": "owner@example.com",
            "attachment_base64": ATTACHMENT,
        },
    )


def test_hicre_subject_routes_to_sura_with_pdf(client):
    r = _post(client, "HiCRE T-12 for the Brickell hotel")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["agent"] == "SURA"
    assert body["extracted"]["taxes"] != body["extracted"]["operatingExpenses"]
    pdf = base64.b64decode(body["pdf_base64"])
    assert pdf.startswith(b"%PDF")


def test_anrd_subject_routes_to_gira_with_pdf(client):
    r = _post(client, "ANRD farm operating statement - Goias")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["agent"] == "GIRA"
    pdf = base64.b64decode(body["pdf_base64"])
    assert pdf.startswith(b"%PDF")


def test_unknown_subject_returns_422(client):
    r = _post(client, "Quarterly newsletter")
    assert r.status_code == 422
    assert r.json() == {"error": "Could not determine asset track"}
