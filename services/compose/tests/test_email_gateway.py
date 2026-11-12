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


def test_anrd_subject_rejected_politely(client):
    # Scope narrowing (2026-11-10): UZE Underwrite is HiCRE only.
    r = _post(client, "ANRD farm operating statement - Goias")
    assert r.status_code == 422
    assert r.json() == {
        "error": (
            "UZE Underwrite currently processes Hospitality & "
            "Income CRE only. Please contact our team directly "
            "for A|NR|D spatial underwriting."
        )
    }


def test_land_acquisition_rejected_before_valuation(client):
    # The ANRD rejection precedes use-case routing: even an
    # acquisition subject is declined when it is a land subject.
    r = _post(client, "Land acquisition due diligence")
    assert r.status_code == 422
    assert "Hospitality & Income CRE only" in r.json()["error"]


def test_unknown_subject_returns_422(client):
    r = _post(client, "Quarterly newsletter")
    assert r.status_code == 422
    assert r.json() == {"error": "Could not determine asset track"}


def test_emergency_subject_flags_sura_and_cross_sell(client):
    r = _post(client, "Urgent P&L - replacement analyst, hotel T-12")
    assert r.status_code == 200
    body = r.json()
    assert body["useCase"] == "emergency_replacement"
    assert body["agent"] == "SURA"
    assert body["crossSell"] == (
        "Need to replace your Property Manager too? UZEmarkets "
        "Talent Placement can source a vetted human manager for "
        "your market in 48 hours."
    )
    assert base64.b64decode(body["pdf_base64"]).startswith(b"%PDF")


def test_acquisition_subject_runs_valuation(client):
    r = _post(client, "Acquisition due diligence - HiCRE hotel")
    assert r.status_code == 200
    body = r.json()
    assert body["useCase"] == "acquisition_due_diligence"
    assert body["agent"] == "SURA"
    ext = body["extracted"]
    assert ext["historicalsNOI"] == {
        "months12": 504100,
        "months18": 731200,
        "months36": 1398500,
    }
    # Implied value is NOI / Cap Rate, computed — never hardcoded.
    assert ext["impliedValue"] == round(504100 / 0.055, 2)


def test_talent_subject_bypasses_analysis_to_placement(client):
    r = _post(client, "Hiring - need a property manager")
    assert r.status_code == 200
    body = r.json()
    assert body["useCase"] == "talent_placement"
    assert body["routedTo"] == "Human Talent Placement"
    assert body["agent"] is None
    assert "pdf_base64" not in body


def test_refinancing_modifier_directs_the_analysis(client):
    r = _post(client, "HiCRE hotel P&L - refinancing package")
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "pnl_verification"
    assert body["modifier"] == "refinancing"
    assert body["focus"] == "debt service coverage"


def test_distressed_valuation_modifier(client):
    r = _post(client, "Valuation - distressed hotel sale, HiCRE")
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "valuation"
    assert body["modifier"] == "distressed_sale"
    assert body["focus"] == "rapid liquidity"
