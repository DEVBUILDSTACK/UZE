"""UZE Underwrite reports — persistence, receipts, NOI claims,
notifications, delta tracking, and the anonymized comp pool
(2026-11-13 night sprint).

Pins the data-layer contract of underwrite_reports:

  - an ingest persists a report whose receipt hash equals an
    independently computed sha256 of the canonical payload, and
    whose stored NOI is the analysis engine's own figure;
  - an NOI claim issues only from the multiyear/mcp doors,
    only against a declared micro-region present in the
    reference table — and, once judged UPHELD and finalized,
    the claim is visible on the Reliance API;
  - the email door NEVER issues a claim (its extraction is a
    labelled mock) and records NOT_APPLICABLE with the reason;
  - notifications are composed as two QUEUED beats, in order;
  - delta tracks NOI/bucket movement and judges each prior
    plan line by distance-to-benchmark movement;
  - the comp pool is opt-in, per-unit, and anonymized — and
    only benchmarks a later run once >= 2 contributions exist
    in its micro-region.

Fixtures are synthetic and modeled on test_comp_benchmark
(SUBJECT / COMPS / YEARS). The juror is stubbed at the module
seam exactly as test_assuraties does; no live attestation is
fabricated.
"""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

import email_gateway
import juror
import metering
import models
import underwrite_reports as ur
from db import session as db_session
from test_comp_benchmark import COMPS, SUBJECT, SUBJECT_ITEMS, YEARS

SENDER = "owner@example.com"
SENDER2 = "second@example.com"
REGION = "baltimore-washington"


def _wipe(session):
    """FK-safe cleanup of everything these tests write. The
    three report tables are new tonight (only these tests and
    the API tests write them) and are wiped wholesale; the
    shared claim/intent/region tables are wiped ONLY for rows
    these tests create — in the full suite they hold other
    tests' rows with FK children (bids, anchors) that a bulk
    delete would violate."""
    session.query(models.ReportNotification).delete()
    session.query(models.CompPoolEntry).delete()
    session.query(models.UnderwriteReport).delete()
    claim_ids = [
        c.id
        for c in session.query(models.Claim)
        .filter(models.Claim.claimant_entity_id == "uze-underwrite-engine")
        .all()
    ]
    if claim_ids:
        session.query(models.AttestationAnchor).filter(
            models.AttestationAnchor.claim_id.in_(claim_ids)
        ).delete(synchronize_session=False)
        session.query(models.Claim).filter(
            models.Claim.id.in_(claim_ids)
        ).delete(synchronize_session=False)
    session.query(models.Intent).filter(
        models.Intent.poster_account == "uze-underwrite-engine"
    ).delete()
    refs = (
        session.query(models.Intent)
        .filter(models.Intent.micro_region_id == REGION)
        .count()
    )
    if refs == 0:
        session.query(models.MicroRegion).filter(
            models.MicroRegion.id == REGION
        ).delete()
    session.commit()


def _wipe_report_tables(session):
    session.query(models.ReportNotification).delete()
    session.query(models.CompPoolEntry).delete()
    session.query(models.UnderwriteReport).delete()
    session.commit()


@pytest.fixture()
def clean_session(migrated_db):
    session = db_session()
    _wipe(session)
    try:
        yield session
    finally:
        try:
            _wipe(session)
        finally:
            session.close()


def _payload(**overrides):
    payload = {
        "years": copy.deepcopy(YEARS),
        "context": None,
        "subject_profile": copy.deepcopy(SUBJECT),
        "comps": copy.deepcopy(COMPS),
        "comp_threshold_pct": None,
        "sender_email": None,
        "prior_report_id": None,
        "contribute_comps": False,
    }
    payload.update(overrides)
    return payload


def _add_region(session, region_id=REGION):
    if session.get(models.MicroRegion, region_id) is None:
        session.add(
            models.MicroRegion(
                id=region_id,
                label="Baltimore-Washington",
                metro="Baltimore",
                region="MD",
            )
        )
        session.commit()


def _upheld(claim):
    return {
        "status": "ok",
        "verdict": "UPHELD",
        "rationale": "statement is specific and consistent",
        "confidence": 0.9,
        "model": "stub-juror-model",
        "completionId": "chatcmpl-stub-uwr",
        "verification": {"signatureKind": "gateway", "result": "verified"},
    }


# ------------------------------------------------------------------
# (1) Persistence + receipt
# ------------------------------------------------------------------


def test_ingest_persists_with_verifiable_receipt(clean_session):
    payload = _payload()
    snapshot = copy.deepcopy(payload)
    expected_hash = hashlib.sha256(
        json.dumps(
            snapshot, sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")
    ).hexdigest()

    resp = ur.run_multiyear_ingest(clean_session, payload, door="multiyear")
    receipt = resp["receipt"]
    assert receipt["report_id"].startswith("uwr_")
    assert receipt["input_hash"] == expected_hash
    assert receipt["engine_version"] == ur.ENGINE_VERSION
    assert receipt["issued_at"].endswith("Z")
    # No micro-region row exists in this test: no claim.
    assert receipt["claim_id"] is None

    row = ur.get_report(clean_session, receipt["report_id"])
    assert row is not None
    assert row.input_hash == expected_hash
    assert row.door == "multiyear"
    fresh = email_gateway.analyze_multiyear(
        YEARS, subject_profile=SUBJECT, comps=COMPS
    )
    assert row.result["periods"][-1]["noi"] == fresh["periods"][-1]["noi"] == 880000

    view = ur.report_view(clean_session, row)
    assert view["receipt"]["report_id"] == receipt["report_id"]
    assert view["report"]["door"] == "multiyear"
    assert view["report"]["claim_status"] == "NOT_ISSUED"

    other = _payload()
    other["years"][1]["line_items"]["Repairs & Maintenance"] = 151_000
    resp2 = ur.run_multiyear_ingest(clean_session, other, door="multiyear")
    assert resp2["receipt"]["report_id"] != receipt["report_id"]
    assert resp2["receipt"]["input_hash"] != expected_hash


# ------------------------------------------------------------------
# (2) Claim issuance and the walk to Reliance grade
# ------------------------------------------------------------------


def test_claim_issues_and_reaches_reliance(market_client, monkeypatch):
    session = db_session()
    try:
        _wipe_report_tables(session)
        _add_region(session)

        resp = ur.run_multiyear_ingest(session, _payload(), door="multiyear")
        receipt = resp["receipt"]
        claim_id = receipt["claim_id"]
        assert claim_id is not None

        row = ur.get_report(session, receipt["report_id"])
        assert row.claim_status == "ISSUED"
        claim = session.get(models.Claim, claim_id)
        assert claim is not None
        assert claim.status == models.ClaimStatus.ISSUED
        assert claim.claimant_entity_id == "uze-underwrite-engine"
        assert claim.claimed_value["reportId"] == receipt["report_id"]
        assert claim.claimed_value["metric"] == "NOI"
        assert claim.claimed_value["amount"] == 880000
        intent_id = claim.intent_id
    finally:
        session.close()

    monkeypatch.setattr(juror, "judge_claim", _upheld)
    judged = market_client.post(f"/api/v1/claims/{claim_id}/judge")
    assert judged.status_code == 200, judged.text
    assert judged.json()["status"] == "RESOLVED_TRUE"

    finalized = market_client.post(
        f"/api/v1/claims/{claim_id}/finalize",
        json={"authorizationReference": "credit-committee-2026-11-13-test"},
    )
    assert finalized.status_code == 200, finalized.text
    assert finalized.json()["status"] == "ASSURATIZED"

    headers = {"X-IDENTITY": metering.build_mock_identity("lender:bank-1")}
    resp = market_client.get(
        "/api/v1/reliance/claims",
        params={"intentId": intent_id},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert [c["id"] for c in resp.json()["claims"]] == [claim_id]

    session = db_session()
    try:
        _wipe_report_tables(session)
    finally:
        session.close()


# ------------------------------------------------------------------
# (3) The no-claim rules
# ------------------------------------------------------------------


def test_no_claim_without_subject_profile(clean_session):
    payload = _payload(subject_profile=None, comps=None)
    resp = ur.run_multiyear_ingest(clean_session, payload, door="multiyear")
    assert resp["receipt"]["claim_id"] is None
    row = ur.get_report(clean_session, resp["receipt"]["report_id"])
    assert row.claim_status == "NOT_ISSUED"
    assert "micro-region" in row.claim_note
    assert clean_session.query(models.Claim).count() == 0


def test_no_claim_for_unknown_micro_region(clean_session):
    # SUBJECT declares baltimore-washington; no such row exists.
    resp = ur.run_multiyear_ingest(clean_session, _payload(), door="multiyear")
    assert resp["receipt"]["claim_id"] is None
    row = ur.get_report(clean_session, resp["receipt"]["report_id"])
    assert row.claim_status == "NOT_ISSUED"
    assert "reference table" in row.claim_note
    assert clean_session.query(models.Claim).count() == 0


def test_email_report_never_issues_a_claim(clean_session):
    before = clean_session.query(models.Claim).count()
    out = ur.persist_email_report(
        clean_session,
        sender=SENDER,
        subject="HiCRE T-12 for the Brickell hotel",
        response={
            "status": "success",
            "agent": "SURA",
            "extracted": {"netOperatingIncome": 504100},
            "pdf_base64": "JVBERi0xLjQgZmFrZQ==",
        },
        attachment_bytes=4321,
    )
    assert out["receipt"]["claim_id"] is None
    assert clean_session.query(models.Claim).count() == before

    row = ur.get_report(clean_session, out["receipt"]["report_id"])
    assert row.door == "email"
    assert row.claim_status == "NOT_APPLICABLE"
    assert "mock" in row.claim_note
    # The PDF bytes are not re-stored; the row says where they live.
    assert "pdf_base64" not in row.result
    assert row.result["pdf_in_original_response"] is True
    # The attachment CONTENT is never stored — only its size.
    assert row.request_payload == {
        "subject": "HiCRE T-12 for the Brickell hotel",
        "sender": SENDER,
        "attachment_bytes": 4321,
    }
    assert out["notification_beat1"]["status"] == "QUEUED"


# ------------------------------------------------------------------
# (4) Notifications
# ------------------------------------------------------------------


def test_notifications_are_two_queued_beats_in_order(clean_session):
    resp = ur.run_multiyear_ingest(
        clean_session, _payload(sender_email=SENDER), door="multiyear"
    )
    report_id = resp["receipt"]["report_id"]
    beat1 = resp["notification_beat1"]
    assert beat1["to"] == SENDER
    assert beat1["status"] == "QUEUED"
    assert beat1["subject"] == (
        f"UZE Underwrite — submission received (report {report_id})"
    )

    notes = ur.list_notifications(clean_session, report_id)
    assert [n["beat"] for n in notes] == [1, 2]
    assert all(n["status"] == "QUEUED" for n in notes)
    assert all(n["to"] == SENDER for n in notes)
    assert report_id in notes[0]["body"]
    assert resp["receipt"]["input_hash"] in notes[0]["body"]
    assert f"GET /api/v1/underwrite/reports/{report_id}" in notes[0]["body"]
    assert notes[1]["subject"] == (
        f"UZE Underwrite — your report is ready (report {report_id})"
    )
    assert f"/api/v1/underwrite/reports/{report_id}/pdf" in notes[1]["body"]
    # No body claims the service sent anything.
    for n in notes:
        assert "was sent" not in n["body"]


# ------------------------------------------------------------------
# (5) Delta
# ------------------------------------------------------------------


def test_delta_tracks_noi_buckets_and_plan_progress(clean_session):
    first = ur.run_multiyear_ingest(clean_session, _payload(), door="multiyear")
    r1 = first["receipt"]["report_id"]

    years2 = copy.deepcopy(YEARS)
    years2[1]["line_items"]["Repairs & Maintenance"] = 130_000
    second = ur.run_multiyear_ingest(
        clean_session,
        _payload(years=years2, prior_report_id=r1),
        door="multiyear",
    )
    delta = second["delta"]
    assert delta["status"] == "OK"
    assert delta["prior_report_id"] == r1
    # Hand-computed: NOI 880,000 -> 900,000 (R&M down 20,000).
    assert delta["noi"]["prior"] == 880000
    assert delta["noi"]["current"] == 900000
    assert delta["noi"]["change_abs"] == 20000
    assert delta["noi"]["change_pct"] == 2.27
    opex = delta["buckets"]["Operating Expenses"]
    assert opex["prior"] == 150000
    assert opex["current"] == 130000
    assert opex["change_abs"] == -20000
    assert opex["change_pct"] == -13.33

    lines = {row["line"]: row for row in delta["lines"]}
    rm = lines["Repairs & Maintenance"]
    assert rm["prior_per_unit"] == 1500
    assert rm["current_per_unit"] == 1300
    assert rm["change_per_unit"] == -200

    tracking = {row["line"]: row for row in delta["plan_tracking"]}
    rm_plan = tracking["Repairs & Maintenance"]
    assert rm_plan["benchmark_per_unit"] == 1200
    assert rm_plan["prior_per_unit"] == 1500
    assert rm_plan["current_per_unit"] == 1300
    # Distance to benchmark: 300 -> 100 per unit. Improved.
    assert rm_plan["status"] == "improved"
    assert rm_plan["annualized_change_usd"] == -20000


def test_delta_with_missing_prior_still_returns_analysis(clean_session):
    resp = ur.run_multiyear_ingest(
        clean_session,
        _payload(prior_report_id="uwr_missing"),
        door="multiyear",
    )
    assert resp["delta"] == {
        "status": "PRIOR_NOT_FOUND",
        "prior_report_id": "uwr_missing",
    }
    assert resp["periods"][-1]["noi"] == 880000


# ------------------------------------------------------------------
# (6) The comp pool
# ------------------------------------------------------------------


def test_pool_contribution_is_opt_in(clean_session):
    payload = _payload(sender_email=SENDER)
    del payload["contribute_comps"]
    ur.run_multiyear_ingest(clean_session, payload, door="multiyear")
    assert clean_session.query(models.CompPoolEntry).count() == 0

    ur.run_multiyear_ingest(
        clean_session,
        _payload(sender_email=SENDER, contribute_comps=False),
        door="multiyear",
    )
    assert clean_session.query(models.CompPoolEntry).count() == 0


def test_pool_row_is_per_unit_and_anonymized(clean_session):
    ur.run_multiyear_ingest(
        clean_session,
        _payload(sender_email=SENDER, contribute_comps=True),
        door="multiyear",
    )
    rows = clean_session.query(models.CompPoolEntry).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.micro_region == REGION
    assert row.unit_count == 100
    assert row.vintage_band == "VINTAGE_2000_2009"
    assert row.period == "2025"
    assert row.credit_units == 1
    # Per-unit, benchmark-scope lines only.
    assert set(row.lines) == {
        "Market Rent",
        "Parking Income",
        "Vacancy Loss",
        "Repairs & Maintenance",
    }
    assert row.lines["Repairs & Maintenance"]["per_unit"] == 1500.0
    assert row.lines["Market Rent"]["per_unit"] == 12000.0
    assert row.lines["Repairs & Maintenance"]["label"] == "Repairs & Maintenance"
    assert all(
        info["bucket"] in ("Revenue", "Operating Expenses")
        for info in row.lines.values()
    )
    # Anonymized: the reference is the sender's hash, and neither
    # the sender, a property/comp name, nor any raw total appears.
    assert row.contributor_ref == hashlib.sha256(
        SENDER.encode("utf-8")
    ).hexdigest()
    blob = json.dumps(
        {
            "lines": row.lines,
            "contributor_ref": row.contributor_ref,
            "micro_region": row.micro_region,
            "property_type": row.property_type,
            "property_class": row.property_class,
        }
    )
    assert SENDER not in blob
    assert "Comp One" not in blob
    assert "1200000" not in blob
    assert "150000" not in blob


def _contribution_payload(sender, units, items):
    return _payload(
        years=[{"period": "2025", "line_items": items}],
        subject_profile={**SUBJECT, "unit_count": units},
        comps=None,
        sender_email=sender,
        contribute_comps=True,
    )


def test_pool_benchmarks_a_later_run_once_two_entries_exist(clean_session):
    ur.run_multiyear_ingest(
        clean_session,
        _contribution_payload(
            SENDER,
            80,
            {"Market Rent Potential": 1_040_000, "Repairs & Maintenance": 96_000},
        ),
        door="multiyear",
    )
    ur.run_multiyear_ingest(
        clean_session,
        _contribution_payload(
            SENDER2,
            120,
            {"Market Rent Potential": 1_560_000, "Repairs & Maintenance": 144_000},
        ),
        door="multiyear",
    )
    assert clean_session.query(models.CompPoolEntry).count() == 2

    third = ur.run_multiyear_ingest(
        clean_session, _payload(comps=None), door="multiyear"
    )
    section = third["comp_benchmark"]
    assert section["source"] == "contributed_pool"
    assert section["pool_size"] >= 2
    assert section["status"] == "OK"
    assert section["findings"]
    assert section["findings"][0]["line"] == "Repairs & Maintenance"


def test_single_pool_entry_never_benchmarks(clean_session):
    profile = {**SUBJECT, "micro_region": "pool-single-region"}
    ur.run_multiyear_ingest(
        clean_session,
        _payload(
            subject_profile=profile,
            sender_email=SENDER,
            contribute_comps=True,
        ),
        door="multiyear",
    )
    assert clean_session.query(models.CompPoolEntry).count() == 1

    resp = ur.run_multiyear_ingest(
        clean_session,
        _payload(subject_profile=profile, comps=None),
        door="multiyear",
    )
    assert resp["comp_benchmark"]["status"] == "NO_COMP_SET_SUPPLIED"
    assert "source" not in resp["comp_benchmark"]


# ------------------------------------------------------------------
# (7) PDF
# ------------------------------------------------------------------


def test_render_pdf_for_multiyear_report(clean_session):
    resp = ur.run_multiyear_ingest(clean_session, _payload(), door="multiyear")
    row = ur.get_report(clean_session, resp["receipt"]["report_id"])
    data = ur.render_report_pdf(clean_session, row)
    assert data.startswith(b"%PDF")


def test_render_pdf_refused_for_email_door(clean_session):
    out = ur.persist_email_report(
        clean_session,
        sender=SENDER,
        subject="HiCRE T-12 for the Brickell hotel",
        response={
            "status": "success",
            "agent": "SURA",
            "extracted": {"netOperatingIncome": 504100},
            "pdf_base64": "JVBERi0xLjQgZmFrZQ==",
        },
        attachment_bytes=128,
    )
    row = ur.get_report(clean_session, out["receipt"]["report_id"])
    with pytest.raises(ValueError, match="REPORT_PDF_NOT_APPLICABLE"):
        ur.render_report_pdf(clean_session, row)
