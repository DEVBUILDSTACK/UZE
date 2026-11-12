"""ASSURATIES — the claim > judge > resolved pipeline (spec 07).

Pins the lifecycle contract:
  - issue: the Intent must exist (404), claimantEntityId is
    required (422), period rules cut both ways (HICRE_PERIOD
    requires periodKind; other classes must not carry one, 422)
  - challenge: lawful only from ISSUED — a second challenge is 409
  - judge: a stubbed juror's UPHELD resolves TRUE and REFUTED
    resolves FALSE, with the report recorded verbatim; with no
    juror available the claim rests at UNDER_RESOLUTION with the
    reason recorded — no verdict is fabricated — and can be judged
    again from there
  - finalize: an authorization reference is required (422);
    RESOLVED_FALSE can never finalize (409); a challenged claim
    that was upheld finalizes with withstood=true
  - Reliance API: 401 without X-IDENTITY; returns ONLY
    ASSURATIZED claims, with the bond fields, the juror summary,
    and the EventLog resolution trail

The juror is stubbed at the module seam (juror.judge_claim) for
the API tests — and at juror.judge_panel for contested claims,
which route to the panel since spec 08 §9 — and exercised
structurally against a fake InferenceClient for its own tests —
the same discipline as test_inference.py. No test fabricates a
live attestation.
"""
from __future__ import annotations

import json

import pytest

import juror
import metering
import models
from db import session as db_session
from test_intents import _post_spec

CLAIMANT = "5e3532e9-aecc-47fb-a557-35804dd7f9e9"
CHALLENGER = "b1c2d3e4-1111-4222-8333-444455556666"


def _upheld(claim):
    return {
        "status": "ok",
        "verdict": "UPHELD",
        "rationale": "statement is specific and consistent",
        "confidence": 0.9,
        "model": "stub-juror-model",
        "completionId": "chatcmpl-stub-1",
        "verification": {"signatureKind": "gateway", "result": "verified"},
    }


def _refuted(claim):
    report = _upheld(claim)
    report["verdict"] = "REFUTED"
    report["rationale"] = "opex lines omit the brand fee"
    return report


def _panel_upheld(claim):
    """A panel report stub (spec 08 §9): contested claims are
    judged by juror.judge_panel, not judge_claim — two seats,
    both UPHELD, majority UPHELD."""
    seat = {
        "status": "ok",
        "verdict": "UPHELD",
        "rationale": "panel seat stub",
        "confidence": 0.9,
        "model": "stub-juror-model",
        "juror": "stub-juror-model",
        "completionId": "chatcmpl-stub-panel",
        "verification": {"signatureKind": "gateway", "result": "verified"},
        "precedentsUsed": [],
    }
    second = {
        **seat,
        "model": "stub-juror-model-b",
        "juror": "stub-juror-model-b",
    }
    return {
        "status": "ok",
        "verdict": "UPHELD",
        "panel": True,
        "panelVerdict": "UPHELD",
        "panelReports": [seat, second],
        "juror": "panel:stub-juror-model+stub-juror-model-b",
        "model": "panel:stub-juror-model+stub-juror-model-b",
        "precedentsUsed": [],
    }


@pytest.fixture()
def stub_juror(monkeypatch):
    def install(report_fn):
        monkeypatch.setattr(juror, "judge_claim", report_fn)

    return install


def _issue(client, spec_id, **overrides):
    body = {
        "intentId": spec_id,
        "claimClass": "HICRE_ASSET",
        "statement": "The property has 340 doors under the Aloft brand.",
        "claimedValue": {"doorCount": 340, "brandAffiliation": "Aloft"},
        "claimantEntityId": CLAIMANT,
        "bondAmount": 500,
    }
    body.update(overrides)
    return client.post("/api/v1/claims", json=body)


def _trail(claim_id):
    with db_session() as session:
        rows = (
            session.query(models.EventLog)
            .filter(
                models.EventLog.aggregate_type == "claim",
                models.EventLog.aggregate_id == claim_id,
            )
            .order_by(models.EventLog.id)
            .all()
        )
        return [(r.event_type, r.payload) for r in rows]


def test_lifecycle_happy_path_to_assuratized(
    market_client, demo_fixture, stub_juror
):
    spec = _post_spec(market_client, demo_fixture)
    issued = _issue(market_client, spec["id"])
    assert issued.status_code == 201, issued.text
    claim = issued.json()
    assert claim["status"] == "ISSUED"
    assert claim["resolutionMark"] is None
    assert claim["withstood"] is False

    stub_juror(_upheld)
    judged = market_client.post(f"/api/v1/claims/{claim['id']}/judge")
    assert judged.status_code == 200, judged.text
    judged = judged.json()
    assert judged["status"] == "RESOLVED_TRUE"
    assert judged["resolvedAt"] is not None
    assert judged["jurorReport"]["verdict"] == "UPHELD"
    assert judged["jurorReport"]["completionId"] == "chatcmpl-stub-1"
    assert judged["jurorReport"]["verification"]["signatureKind"] == "gateway"

    finalized = market_client.post(
        f"/api/v1/claims/{claim['id']}/finalize",
        json={"authorizationReference": "credit-committee-2026-11-09-001"},
    )
    assert finalized.status_code == 200, finalized.text
    body = finalized.json()
    assert body["status"] == "ASSURATIZED"
    assert body["resolutionMark"] == "ASSURATIZED"
    assert body["withstood"] is False

    trail = _trail(claim["id"])
    assert [t[0] for t in trail] == [
        "claim.issued",
        "claim.judged",
        "claim.finalized",
    ]
    assert trail[2][1]["authorizationReferencePresent"] is True


def test_period_claim_validation_both_ways(market_client, demo_fixture):
    spec = _post_spec(market_client, demo_fixture)

    missing = _issue(
        market_client,
        spec["id"],
        claimClass="HICRE_PERIOD",
        statement="Total operating expenses for 2025.",
        claimedValue={"totalOperatingExpenses": 4200000},
    )
    assert missing.status_code == 422

    ok = _issue(
        market_client,
        spec["id"],
        claimClass="HICRE_PERIOD",
        periodKind="ANNUAL",
        statement="Total operating expenses for calendar 2025.",
        claimedValue={"totalOperatingExpenses": 4200000, "currency": "USDC"},
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["periodKind"] == "ANNUAL"

    stray = _issue(
        market_client, spec["id"], claimClass="RWA", periodKind="MONTHLY"
    )
    assert stray.status_code == 422


def test_issue_validation_edges(market_client, demo_fixture):
    spec = _post_spec(market_client, demo_fixture)

    unknown = _issue(market_client, "no-such-intent")
    assert unknown.status_code == 404

    no_claimant = market_client.post(
        "/api/v1/claims",
        json={
            "intentId": spec["id"],
            "claimClass": "RWA",
            "statement": "The parcel's water rights are registered.",
            "claimedValue": {"registered": True},
            "bondAmount": 10,
        },
    )
    assert no_claimant.status_code == 422

    negative_bond = _issue(market_client, spec["id"], bondAmount=-5)
    assert negative_bond.status_code == 422

    assert market_client.get("/api/v1/claims/nope").status_code == 404


def test_challenge_state_guard(market_client, demo_fixture):
    spec = _post_spec(market_client, demo_fixture)
    claim = _issue(market_client, spec["id"]).json()

    challenged = market_client.post(
        f"/api/v1/claims/{claim['id']}/challenge",
        json={"challengerEntityId": CHALLENGER, "bondAmount": 750},
    )
    assert challenged.status_code == 200, challenged.text
    body = challenged.json()
    assert body["status"] == "CHALLENGED"
    assert body["challenge"]["challengerEntityId"] == CHALLENGER
    assert body["challenge"]["bondAmount"] == 750

    second = market_client.post(
        f"/api/v1/claims/{claim['id']}/challenge",
        json={"challengerEntityId": CHALLENGER, "bondAmount": 1500},
    )
    assert second.status_code == 409

    missing = market_client.post(
        "/api/v1/claims/nope/challenge",
        json={"challengerEntityId": CHALLENGER, "bondAmount": 1},
    )
    assert missing.status_code == 404


def test_judge_unavailable_leaves_under_resolution(
    market_client, demo_fixture, stub_juror, monkeypatch
):
    monkeypatch.delenv("NEARAI_API_KEY", raising=False)
    spec = _post_spec(market_client, demo_fixture)
    claim = _issue(market_client, spec["id"]).json()

    # No stub installed: the real juror runs and honestly reports
    # unavailable (no key in the test environment).
    judged = market_client.post(f"/api/v1/claims/{claim['id']}/judge")
    assert judged.status_code == 200, judged.text
    body = judged.json()
    assert body["status"] == "UNDER_RESOLUTION"
    assert body["resolvedAt"] is None
    assert body["jurorReport"]["status"] == "unavailable"
    assert "NEARAI_API_KEY" in body["jurorReport"]["reason"]

    # Re-judging from UNDER_RESOLUTION is lawful: once the juror
    # can run, the same claim resolves.
    stub_juror(_upheld)
    rejudged = market_client.post(f"/api/v1/claims/{claim['id']}/judge")
    assert rejudged.json()["status"] == "RESOLVED_TRUE"


def test_finalize_requires_authorization_reference(
    market_client, demo_fixture, stub_juror
):
    spec = _post_spec(market_client, demo_fixture)
    claim = _issue(market_client, spec["id"]).json()
    stub_juror(_upheld)
    market_client.post(f"/api/v1/claims/{claim['id']}/judge")

    missing = market_client.post(
        f"/api/v1/claims/{claim['id']}/finalize", json={}
    )
    assert missing.status_code == 422
    empty = market_client.post(
        f"/api/v1/claims/{claim['id']}/finalize",
        json={"authorizationReference": ""},
    )
    assert empty.status_code == 422

    view = market_client.get(f"/api/v1/claims/{claim['id']}").json()
    assert view["status"] == "RESOLVED_TRUE"


def test_resolved_false_never_assuratizes(
    market_client, demo_fixture, stub_juror
):
    spec = _post_spec(market_client, demo_fixture)
    claim = _issue(market_client, spec["id"]).json()
    stub_juror(_refuted)
    judged = market_client.post(f"/api/v1/claims/{claim['id']}/judge")
    assert judged.json()["status"] == "RESOLVED_FALSE"
    assert judged.json()["jurorReport"]["verdict"] == "REFUTED"

    finalized = market_client.post(
        f"/api/v1/claims/{claim['id']}/finalize",
        json={"authorizationReference": "credit-committee-2026-11-09-002"},
    )
    assert finalized.status_code == 409
    view = market_client.get(f"/api/v1/claims/{claim['id']}").json()
    assert view["status"] == "RESOLVED_FALSE"
    assert view["resolutionMark"] is None


def test_challenged_claim_finalizes_withstood(
    market_client, demo_fixture, monkeypatch
):
    spec = _post_spec(market_client, demo_fixture)
    claim = _issue(market_client, spec["id"]).json()
    market_client.post(
        f"/api/v1/claims/{claim['id']}/challenge",
        json={"challengerEntityId": CHALLENGER, "bondAmount": 750},
    )
    # Contested claims route to the panel (spec 08 §9): the
    # stub seam for a challenged claim is juror.judge_panel.
    monkeypatch.setattr(juror, "judge_panel", _panel_upheld)
    market_client.post(f"/api/v1/claims/{claim['id']}/judge")
    finalized = market_client.post(
        f"/api/v1/claims/{claim['id']}/finalize",
        json={"authorizationReference": "credit-committee-2026-11-09-003"},
    )
    body = finalized.json()
    assert body["status"] == "ASSURATIZED"
    assert body["withstood"] is True
    assert body["challenge"]["withstood"] is True

    trail = _trail(claim["id"])
    assert [t[0] for t in trail] == [
        "claim.issued",
        "claim.challenged",
        "claim.judged",
        "claim.finalized",
    ]
    assert trail[3][1]["withstood"] is True


def test_arcium_tier_flag_and_mark(market_client, demo_fixture, stub_juror):
    spec = _post_spec(market_client, demo_fixture)
    issued = _issue(
        market_client, spec["id"], confidentialTier="ARCIUM"
    )
    assert issued.status_code == 201, issued.text
    claim = issued.json()
    assert claim["confidentialTier"] == "ARCIUM"
    assert claim["resolutionMark"] is None

    stub_juror(_upheld)
    market_client.post(f"/api/v1/claims/{claim['id']}/judge")
    finalized = market_client.post(
        f"/api/v1/claims/{claim['id']}/finalize",
        json={"authorizationReference": "sealed-sale-2026-11-09-001"},
    )
    assert finalized.json()["resolutionMark"] == "ASSURATIZED @ARCIUM"


def test_reliance_api(market_client, demo_fixture, stub_juror):
    spec = _post_spec(market_client, demo_fixture)
    winner = _issue(market_client, spec["id"]).json()
    open_claim = _issue(
        market_client,
        spec["id"],
        statement="Occupancy averaged 71% across 2025.",
        claimedValue={"occupancyPct": 71},
    ).json()
    stub_juror(_upheld)
    market_client.post(f"/api/v1/claims/{winner['id']}/judge")
    market_client.post(
        f"/api/v1/claims/{winner['id']}/finalize",
        json={"authorizationReference": "credit-committee-2026-11-09-004"},
    )

    no_identity = market_client.get("/api/v1/reliance/claims")
    assert no_identity.status_code == 401

    headers = {"X-IDENTITY": metering.build_mock_identity("lender:bank-1")}
    resp = market_client.get(
        "/api/v1/reliance/claims",
        params={"intentId": spec["id"]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["surface"] == "reliance"
    assert body["identity"]["subject"] == "lender:bank-1"
    ids = [c["id"] for c in body["claims"]]
    assert ids == [winner["id"]]  # the ISSUED claim is excluded
    assert open_claim["id"] not in ids

    item = body["claims"][0]
    assert item["status"] == "ASSURATIZED"
    assert item["claimantEntityId"] == CLAIMANT
    assert item["bond"] == {"claimantBond": 500, "challengeBond": None}
    assert item["jurorReportSummary"]["verdict"] == "UPHELD"
    assert item["jurorReportSummary"]["completionId"] == "chatcmpl-stub-1"
    assert [e["eventType"] for e in item["resolutionTrail"]] == [
        "claim.issued",
        "claim.judged",
        "claim.finalized",
    ]

    other = market_client.get(
        "/api/v1/reliance/claims",
        params={"intentId": "another-intent"},
        headers=headers,
    )
    assert other.json()["claims"] == []


# ---------------------------------------------------------------------
# The juror itself — structural tests against a fake InferenceClient
# (the test_inference.py discipline).
# ---------------------------------------------------------------------


class _FakeMessage:
    content = json.dumps(
        {
            "verdict": "REFUTED",
            "rationale": "opex lines omit the brand fee",
            "confidence": 0.7,
        }
    )


class _FakeChoice:
    message = _FakeMessage()


class _FakeCompletion:
    id = "chatcmpl-juror-1"
    choices = [_FakeChoice()]


class _FakeVerified:
    signature_kind = "enclave"


class _FakeCompletions:
    async def create(self, **kwargs):
        return _FakeCompletion()


class _FakeChat:
    completions = _FakeCompletions()


class FakeJurorClient:
    chat = _FakeChat()

    async def verify_response(self, completion_id):
        assert completion_id == "chatcmpl-juror-1"
        return _FakeVerified()


_CLAIM_DICT = {
    "claimClass": "HICRE_PERIOD",
    "periodKind": "ANNUAL",
    "statement": "Total operating expenses for calendar 2025 were $4.2M.",
    "claimedValue": {"totalOperatingExpenses": 4200000},
    "claimantEntityId": CLAIMANT,
    "bondAmount": 500,
    "challenge": None,
}


def test_juror_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("NEARAI_API_KEY", raising=False)
    result = juror.judge_claim(_CLAIM_DICT)
    assert result["status"] == "unavailable"
    assert "NEARAI_API_KEY" in result["reason"]


def test_juror_structural_flow_with_fake_client():
    result = juror.judge_claim(_CLAIM_DICT, client=FakeJurorClient())
    assert result["status"] == "ok"
    assert result["verdict"] == "REFUTED"
    assert result["completionId"] == "chatcmpl-juror-1"
    assert result["verification"]["signatureKind"] == "enclave"


def test_juror_prompt_renders_the_claim():
    prompt = juror.render_claim_as_prompt(_CLAIM_DICT)
    assert "HICRE_PERIOD" in prompt
    assert "ANNUAL" in prompt
    assert "4200000" in prompt
    assert CLAIMANT in prompt


class _NarrativeMessage:
    content = "The claim looks plausible to me."


class _NarrativeChoice:
    message = _NarrativeMessage()


class _NarrativeCompletion:
    id = "chatcmpl-juror-2"
    choices = [_NarrativeChoice()]


class _NarrativeCompletions:
    async def create(self, **kwargs):
        return _NarrativeCompletion()


class _NarrativeChat:
    completions = _NarrativeCompletions()


class NarrativeClient:
    chat = _NarrativeChat()

    async def verify_response(self, completion_id):
        return _FakeVerified()


def test_juror_non_verdict_response_is_error_not_a_verdict():
    result = juror.judge_claim(_CLAIM_DICT, client=NarrativeClient())
    assert result["status"] == "error"
    assert "verdict" in result["reason"]
