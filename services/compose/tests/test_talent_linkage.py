"""Talent linkage (owner tap, 2026-11-12 — Master Directive
Parts 2 & 3).

Pins: JSON resumes validate against TalentProfile and are
recorded; invalid ones return INSUFFICIENT_DATA with the exact
field names; PDF/Word resumes on the talent track return the
January-2nd deferral verbatim; and analyze_multiyear carries
the talent_placement bridge object derived from the asset's
own payroll lines.
"""

from __future__ import annotations

import base64
import io
import json
import zipfile

import email_gateway


def _post(client, subject: str, raw: bytes):
    return client.post(
        "/api/v1/ingest/email",
        json={
            "subject": subject,
            "sender": "talent@example.com",
            "attachment_base64": base64.b64encode(raw).decode(),
        },
    )


VALID_PROFILE = {
    "name": "Casey Rivera",
    "role": "Property Manager",
    "experience_years": 6,
    "skills": ["Yardi", "lease-up", "vendor management"],
    "expected_rate_usd": 78000,
    "certifications": ["CAM"],
}


def test_talent_json_resume_validates_and_records(client, tmp_path, monkeypatch):
    monkeypatch.setenv("TALENT_PROFILES_PATH", str(tmp_path / "profiles.jsonl"))
    r = _post(client, "Talent application - property manager",
              json.dumps(VALID_PROFILE).encode())
    assert r.status_code == 200
    body = r.json()
    assert body["routedTo"] == "Talent Placement — profile validated"
    assert body["profile"]["name"] == "Casey Rivera"
    rows = (tmp_path / "profiles.jsonl").read_text().strip().splitlines()
    assert len(rows) == 1
    assert json.loads(rows[0])["profile"]["role"] == "Property Manager"


def test_talent_json_resume_missing_fields_names_them(client):
    bad = {"name": "No Rate", "role": "Leasing Agent"}
    r = _post(client, "Hiring - leasing", json.dumps(bad).encode())
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "INSUFFICIENT_DATA"
    assert set(body["missing_fields"]) == {
        "experience_years", "skills", "expected_rate_usd",
    }


def test_talent_pdf_resume_gets_the_january_deferral(client):
    r = _post(client, "Talent - my resume", b"%PDF-1.4 resume bytes")
    assert r.status_code == 422
    assert r.json()["error"] == (
        "PDF/Word resume parsing is deferred to our January 2nd "
        "update. Please provide your resume in JSON format."
    )


def test_talent_docx_resume_gets_the_january_deferral(client):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("word/document.xml", "<w:document/>")
    r = _post(client, "Hiring - resume attached", buf.getvalue())
    assert r.status_code == 422
    assert "January 2nd" in r.json()["error"]


def test_financial_pdf_on_a_non_talent_track_is_untouched(client):
    # The deferral is a TALENT-track rule only; a P&L PDF keeps
    # the established SURA mock flow.
    r = _post(client, "HiCRE T-12 for the Brickell hotel", b"%PDF-1.4 p&l")
    assert r.status_code == 200
    assert r.json()["agent"] == "SURA"


def test_talent_placement_bridge_derives_roles_from_payroll_lines():
    years = [{
        "period": "T-12",
        "line_items": {
            "Rental Income": 500000.0,
            "Payroll - resid. manager": 62000.0,
            "Payroll - mainten. staff": 41000.0,
            "Payroll - resid. leasing": 33000.0,
            "Real Estate Taxes": 40000.0,
            "Insurance": 9000.0,
        },
    }]
    out = email_gateway.analyze_multiyear(years)
    tp = out["talent_placement"]
    assert tp["required"] is True
    assert "Property Manager" in tp["roles"]
    assert "Maintenance" in tp["roles"]
    assert "Leasing Agent" in tp["roles"]
    assert tp["payroll_budget_annual"] == 136000.0
    assert tp["cta_url"].startswith("/talent/placement")


def test_talent_placement_bridge_is_quiet_without_role_lines():
    years = [{"period": "T-12", "line_items": {"Rental Income": 1000.0}}]
    tp = email_gateway.analyze_multiyear(years)["talent_placement"]
    assert tp["required"] is False
    assert tp["roles"] == []
