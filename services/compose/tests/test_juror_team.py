"""The Agentic Juror Team + Learning Loop (spec 08).

Pins:
  - precedent-aware judging: before the juror runs, Assuratized
    claims in the claim's micro-region are rendered into its
    prompt in a PRECEDENTS block and recorded on the report as
    precedentsUsed; a different micro-region yields no precedents
  - juror scorecards: GET /api/v1/jurors derives judged / upheld /
    refuted / withstood counts per juror identity from finalized
    outcomes — nothing stored, nothing invented
  - the learning feed: GET /api/v1/learning/recent is the
    terminal-event stream (finalized ASSURATIZED + judged
    RESOLVED_FALSE), newest first, limit respected, and an
    ASSURATIZED entry is the one that adds a comparable
  - the unavailable path stays honest under the team surfaces:
    no verdict, no scorecard entry

Discipline matches test_assuraties.py: API tests stub the juror
at the module seam (juror.judge_claim); the precedent test drives
the REAL juror against a capturing fake InferenceClient so the
assertion is about the prompt actually sent. No test fabricates
a live attestation.
"""
from __future__ import annotations

import copy
import json

import pytest

import juror
from test_intents import _post_spec

CLAIMANT = "5e3532e9-aecc-47fb-a557-35804dd7f9e9"
OTHER_CLAIMANT = "7a8b9c0d-2222-4333-8444-555566667777"
THIRD_CLAIMANT = "c3d4e5f6-3333-4444-8555-666677778888"
CHALLENGER = "b1c2d3e4-1111-4222-8333-444455556666"
SCORECARD_JUROR = "team-scorecard-juror-v1"
SEED_STATEMENT = (
    "Total operating expenses for calendar 2024 were $3.9M "
    "across all lines, brand fees included."
)

_REAL_JUDGE = juror.judge_claim


def _report(verdict, model=SCORECARD_JUROR):
    def fn(claim):
        return {
            "status": "ok",
            "verdict": verdict,
            "rationale": "stubbed for the team tests",
            "confidence": 0.9,
            "model": model,
            "completionId": "chatcmpl-team-stub",
            "verification": {"signatureKind": "gateway", "result": "verified"},
        }

    return fn


@pytest.fixture()
def stub_juror(monkeypatch):
    def install(report_fn):
        monkeypatch.setattr(juror, "judge_claim", report_fn)

    return install


def _post_spec_in_region(client, fixture, region):
    body = copy.deepcopy(fixture["spec"])
    body["microRegionId"] = region
    resp = client.post("/api/v1/specs", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


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
    resp = client.post("/api/v1/claims", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _finalize(client, claim_id, ref):
    return client.post(
        f"/api/v1/claims/{claim_id}/finalize",
        json={"authorizationReference": ref},
    )


# ---------------------------------------------------------------------
# (a) Precedent injection — the real juror, a capturing client.
# ---------------------------------------------------------------------


class _CaptureMessage:
    content = json.dumps(
        {
            "verdict": "UPHELD",
            "rationale": "specific and consistent with the precedent",
            "confidence": 0.8,
        }
    )


class _CaptureChoice:
    message = _CaptureMessage()


class _CaptureCompletion:
    id = "chatcmpl-capture-1"
    choices = [_CaptureChoice()]


class _CaptureVerified:
    signature_kind = "enclave"


class _CaptureCompletions:
    def __init__(self, sink):
        self.sink = sink

    async def create(self, **kwargs):
        self.sink.append(kwargs)
        return _CaptureCompletion()


class _CaptureChat:
    def __init__(self, sink):
        self.completions = _CaptureCompletions(sink)


class CaptureClient:
    """A fake InferenceClient that records what it was sent."""

    def __init__(self):
        self.calls = []
        self.chat = _CaptureChat(self.calls)

    async def verify_response(self, completion_id):
        assert completion_id == "chatcmpl-capture-1"
        return _CaptureVerified()

    def last_prompt(self):
        messages = self.calls[-1]["messages"]
        return [m["content"] for m in messages if m["role"] == "user"][0]


def test_precedent_injection_same_micro_region(
    market_client, demo_fixture, stub_juror, monkeypatch
):
    spec_a = _post_spec(market_client, demo_fixture)  # miami-brickell
    spec_b = _post_spec_in_region(
        market_client, demo_fixture, "miami-brickell"
    )
    spec_c = _post_spec_in_region(
        market_client, demo_fixture, "bethesda-cbd"
    )

    # Seed the precedent: an ASSURATIZED claim in miami-brickell.
    seed = _issue(
        market_client,
        spec_a["id"],
        statement=SEED_STATEMENT,
        claimedValue={"totalOperatingExpenses": 3900000},
    )
    stub_juror(_report("UPHELD", model="stub-juror-model"))
    market_client.post(f"/api/v1/claims/{seed['id']}/judge")
    finalized = _finalize(
        market_client, seed["id"], "credit-committee-team-001"
    )
    assert finalized.json()["status"] == "ASSURATIZED"

    # Judge a new claim on a second Brickell intent through the
    # REAL juror with a capturing client. The target's claimant
    # differs from the seed's: since the self-dealing exclusion
    # (spec 08 §2, Q2(a)) a claimant's own record is never a
    # precedent for their own claims, so cross-claimant is the
    # only way a precedent can be used at all.
    capture = CaptureClient()
    monkeypatch.setattr(
        juror,
        "judge_claim",
        lambda claim: _REAL_JUDGE(claim, client=capture),
    )
    target = _issue(
        market_client, spec_b["id"], claimantEntityId=OTHER_CLAIMANT
    )
    judged = market_client.post(f"/api/v1/claims/{target['id']}/judge")
    assert judged.status_code == 200, judged.text
    assert judged.json()["status"] == "RESOLVED_TRUE"

    prompt = capture.last_prompt()
    assert "PRECEDENTS" in prompt
    assert SEED_STATEMENT in prompt
    assert "3900000" in prompt

    view = market_client.get(f"/api/v1/claims/{target['id']}").json()
    assert view["jurorReport"]["precedentsUsed"] == [seed["id"]]
    assert view["jurorReport"]["juror"] == juror.MODEL
    assert view["jurorReport"]["precedentsExcludedSelfDealing"] == 0

    # A claim in a DIFFERENT micro-region gets no precedents.
    capture_c = CaptureClient()
    monkeypatch.setattr(
        juror,
        "judge_claim",
        lambda claim: _REAL_JUDGE(claim, client=capture_c),
    )
    other = _issue(
        market_client, spec_c["id"], claimantEntityId=OTHER_CLAIMANT
    )
    judged_c = market_client.post(f"/api/v1/claims/{other['id']}/judge")
    assert judged_c.json()["status"] == "RESOLVED_TRUE"
    prompt_c = capture_c.last_prompt()
    assert "PRECEDENTS" not in prompt_c
    assert SEED_STATEMENT not in prompt_c
    view_c = market_client.get(f"/api/v1/claims/{other['id']}").json()
    assert view_c["jurorReport"]["precedentsUsed"] == []


def test_self_dealing_precedents_excluded(
    market_client, demo_fixture, stub_juror, monkeypatch
):
    """Q2(a): a claimant's own Assuratized record never informs
    judgments on their own claims, and a claim's same-Intent
    siblings are excluded whoever claimed them. The exclusion is
    counted on the juror report; other claimants' claims in the
    micro-region still see the precedent."""
    spec_a = _post_spec(market_client, demo_fixture)  # miami-brickell
    spec_b = _post_spec_in_region(
        market_client, demo_fixture, "miami-brickell"
    )

    seed = _issue(
        market_client,
        spec_a["id"],
        statement=SEED_STATEMENT,
        claimedValue={"totalOperatingExpenses": 3900000},
    )
    stub_juror(_report("UPHELD", model="stub-juror-model"))
    market_client.post(f"/api/v1/claims/{seed['id']}/judge")
    finalized = _finalize(
        market_client, seed["id"], "credit-committee-team-010"
    )
    assert finalized.json()["status"] == "ASSURATIZED"

    def judge_with_capture(claim_id):
        capture = CaptureClient()
        monkeypatch.setattr(
            juror,
            "judge_claim",
            lambda claim: _REAL_JUDGE(claim, client=capture),
        )
        resp = market_client.post(f"/api/v1/claims/{claim_id}/judge")
        assert resp.status_code == 200, resp.text
        view = market_client.get(f"/api/v1/claims/{claim_id}").json()
        return capture.last_prompt(), view["jurorReport"]

    # Same claimant, different intent: excluded by claimant.
    own = _issue(market_client, spec_b["id"])  # CLAIMANT, as the seed
    prompt, report = judge_with_capture(own["id"])
    assert "PRECEDENTS" not in prompt
    assert report["precedentsUsed"] == []
    assert report["precedentsExcludedSelfDealing"] == 1

    # Different claimant, SAME intent as the seed: excluded by
    # intent — siblings never judge each other either.
    sibling = _issue(
        market_client, spec_a["id"], claimantEntityId=OTHER_CLAIMANT
    )
    prompt, report = judge_with_capture(sibling["id"])
    assert "PRECEDENTS" not in prompt
    assert report["precedentsUsed"] == []
    assert report["precedentsExcludedSelfDealing"] == 1

    # Different claimant, different intent: the precedent is used
    # and nothing is held back.
    clean = _issue(
        market_client, spec_b["id"], claimantEntityId=OTHER_CLAIMANT
    )
    prompt, report = judge_with_capture(clean["id"])
    assert SEED_STATEMENT in prompt
    assert report["precedentsUsed"] == [seed["id"]]
    assert report["precedentsExcludedSelfDealing"] == 0


def test_render_precedents_block_unit():
    base = {
        "claimClass": "HICRE_ASSET",
        "periodKind": None,
        "statement": "Occupancy averaged 71% across 2025.",
        "claimedValue": {"occupancyPct": 71},
        "claimantEntityId": CLAIMANT,
        "bondAmount": 500,
        "challenge": None,
    }
    assert "PRECEDENTS" not in juror.render_claim_as_prompt(base)

    with_precedents = {
        **base,
        "precedents": [
            {
                "id": "claim-seed-1",
                "statement": SEED_STATEMENT,
                "claimedValue": {"totalOperatingExpenses": 3900000},
                "outcome": "ASSURATIZED",
                "withstood": True,
            }
        ],
    }
    prompt = juror.render_claim_as_prompt(with_precedents)
    assert "PRECEDENTS" in prompt
    assert SEED_STATEMENT in prompt
    assert "challenge withstood: yes" in prompt
    # The claim under judgment still renders after the block's
    # evidence standard — precedents inform, they do not replace.
    assert "Occupancy averaged 71%" in prompt


# ---------------------------------------------------------------------
# (b) Scorecard math.
# ---------------------------------------------------------------------


def test_juror_scorecard_math(
    market_client, demo_fixture, stub_juror, monkeypatch
):
    spec = _post_spec(market_client, demo_fixture)

    upheld = _issue(market_client, spec["id"])
    stub_juror(_report("UPHELD"))
    market_client.post(f"/api/v1/claims/{upheld['id']}/judge")
    _finalize(market_client, upheld["id"], "credit-committee-team-002")

    refuted = _issue(
        market_client,
        spec["id"],
        statement="Occupancy averaged 96% across 2025.",
        claimedValue={"occupancyPct": 96},
    )
    stub_juror(_report("REFUTED"))
    market_client.post(f"/api/v1/claims/{refuted['id']}/judge")
    refused = _finalize(
        market_client, refuted["id"], "credit-committee-team-003"
    )
    assert refused.status_code == 409  # RESOLVED_FALSE never finalizes

    resp = market_client.get("/api/v1/jurors")
    assert resp.status_code == 200, resp.text
    jurors = resp.json()["jurors"]
    assert len(jurors) == 1
    card = jurors[0]
    assert card["juror"] == SCORECARD_JUROR
    assert card["judgedCount"] == 2
    assert card["upheldCount"] == 1
    assert card["refutedCount"] == 1
    assert card["withstoodCount"] == 0
    assert card["unavailableCount"] == 0

    # A challenged claim upheld, then finalized, adds the
    # withstood count. Contested claims route to the PANEL
    # (spec 08 §9): the panel stub seats SCORECARD_JUROR and a
    # second seat, both UPHELD — the panel credits each seat
    # whose verdict matched the panel verdict.
    challenged = _issue(
        market_client,
        spec["id"],
        statement="The 2025 brand fee was 4.1% of rooms revenue.",
        claimedValue={"brandFeePct": 4.1},
    )
    market_client.post(
        f"/api/v1/claims/{challenged['id']}/challenge",
        json={"challengerEntityId": CHALLENGER, "bondAmount": 750},
    )

    def panel_upheld(claim):
        seats = []
        for model in (SCORECARD_JUROR, "zz-second-seat"):
            seats.append(
                {
                    "status": "ok",
                    "verdict": "UPHELD",
                    "rationale": "panel seat stub",
                    "confidence": 0.9,
                    "model": model,
                    "juror": model,
                    "completionId": f"chatcmpl-{model}",
                    "verification": {
                        "signatureKind": "gateway",
                        "result": "verified",
                    },
                    "precedentsUsed": [],
                }
            )
        return {
            "status": "ok",
            "verdict": "UPHELD",
            "panel": True,
            "panelVerdict": "UPHELD",
            "panelReports": seats,
            "juror": f"panel:{SCORECARD_JUROR}+zz-second-seat",
            "model": f"panel:{SCORECARD_JUROR}+zz-second-seat",
            "precedentsUsed": [],
        }

    monkeypatch.setattr(juror, "judge_panel", panel_upheld)
    market_client.post(f"/api/v1/claims/{challenged['id']}/judge")
    _finalize(market_client, challenged["id"], "credit-committee-team-004")

    cards = market_client.get("/api/v1/jurors").json()["jurors"]
    card = [c for c in cards if c["juror"] == SCORECARD_JUROR][0]
    assert card["judgedCount"] == 3
    assert card["upheldCount"] == 2
    assert card["refutedCount"] == 1
    assert card["withstoodCount"] == 1
    # The second seat was credited alongside, with no dissent.
    second = [c for c in cards if c["juror"] == "zz-second-seat"][0]
    assert second["judgedCount"] == 1
    assert second["upheldCount"] == 1
    assert second["panelDissents"] == 0


def test_scorecard_counts_superseded_attempts(
    market_client, demo_fixture, stub_juror, monkeypatch
):
    """Q4: scorecards are event-sourced. A claim judged twice —
    first unavailable (the real juror, no key), then ok under the
    SAME juror identity — must show BOTH the unavailable attempt
    and the terminal outcome on that juror's card. The pre-fix
    derivation read the claim's current jurorReport, so the
    superseded attempt vanished."""
    monkeypatch.delenv("NEARAI_API_KEY", raising=False)
    # A dedicated juror identity for this test: the unavailable
    # path attributes to juror.MODEL, so point MODEL at a fresh
    # identity — the EventLog is append-only across the session
    # and the real MODEL already has attempts from other tests.
    es_juror = "event-sourced-juror-v1"
    monkeypatch.setattr(juror, "MODEL", es_juror)
    spec = _post_spec(market_client, demo_fixture)
    claim = _issue(market_client, spec["id"])

    # Attempt 1: no stub, no key — the real juror honestly
    # reports unavailable under the dedicated identity.
    first = market_client.post(f"/api/v1/claims/{claim['id']}/judge")
    assert first.json()["status"] == "UNDER_RESOLUTION"
    assert first.json()["jurorReport"]["status"] == "unavailable"
    assert first.json()["jurorReport"]["juror"] == es_juror

    # Attempt 2: the same juror identity now answers UPHELD.
    stub_juror(_report("UPHELD", model=es_juror))
    second = market_client.post(f"/api/v1/claims/{claim['id']}/judge")
    assert second.json()["status"] == "RESOLVED_TRUE"
    _finalize(market_client, claim["id"], "credit-committee-team-007")

    cards = market_client.get("/api/v1/jurors").json()["jurors"]
    mine = [c for c in cards if c["juror"] == es_juror]
    assert len(mine) == 1
    card = mine[0]
    assert card["attemptCount"] == 2
    assert card["unavailableCount"] == 1
    assert card["judgedCount"] == 1
    assert card["upheldCount"] == 1
    assert card["refutedCount"] == 0


# ---------------------------------------------------------------------
# (c) The learning feed.
# ---------------------------------------------------------------------


def test_learning_feed(market_client, demo_fixture, stub_juror):
    # Three Brickell specs and three distinct claimants: under
    # the self-dealing exclusion (Q2(a)), precedents accumulate
    # across claims only when neither the claimant nor the
    # Intent repeats — which is the honest shape of the ledger
    # (a market learning from OTHER parties' settled record).
    spec_a = _post_spec(market_client, demo_fixture)
    spec_b = _post_spec_in_region(
        market_client, demo_fixture, "miami-brickell"
    )
    spec_c = _post_spec_in_region(
        market_client, demo_fixture, "miami-brickell"
    )

    first = _issue(market_client, spec_a["id"])
    stub_juror(_report("UPHELD"))
    market_client.post(f"/api/v1/claims/{first['id']}/judge")
    _finalize(market_client, first["id"], "credit-committee-team-005")

    second = _issue(
        market_client,
        spec_b["id"],
        statement="Payroll ran 31% of total revenue in 2025.",
        claimedValue={"payrollPctOfRevenue": 31},
        claimantEntityId=OTHER_CLAIMANT,
    )
    stub_juror(_report("UPHELD"))
    market_client.post(f"/api/v1/claims/{second['id']}/judge")
    _finalize(market_client, second["id"], "credit-committee-team-006")

    third = _issue(
        market_client,
        spec_c["id"],
        statement="Occupancy averaged 99% across 2025.",
        claimedValue={"occupancyPct": 99},
        claimantEntityId=THIRD_CLAIMANT,
    )
    stub_juror(_report("REFUTED"))
    market_client.post(f"/api/v1/claims/{third['id']}/judge")

    resp = market_client.get("/api/v1/learning/recent")
    assert resp.status_code == 200, resp.text
    entries = resp.json()["entries"]
    mine = [
        e
        for e in entries
        if e["claimId"] in {first["id"], second["id"], third["id"]}
    ]
    # Newest first: the refutation (latest event), then the two
    # finalizations in reverse order.
    assert [e["claimId"] for e in mine] == [
        third["id"],
        second["id"],
        first["id"],
    ]
    by_id = {e["claimId"]: e for e in mine}
    assert by_id[first["id"]]["outcome"] == "ASSURATIZED"
    assert by_id[first["id"]]["comparableAdded"] is True
    assert by_id[second["id"]]["comparableAdded"] is True
    assert by_id[third["id"]]["outcome"] == "RESOLVED_FALSE"
    assert by_id[third["id"]]["comparableAdded"] is False
    expected_claimants = {
        first["id"]: CLAIMANT,
        second["id"]: OTHER_CLAIMANT,
        third["id"]: THIRD_CLAIMANT,
    }
    for entry in mine:
        assert entry["juror"] == SCORECARD_JUROR
        assert entry["claimantEntityId"] == expected_claimants[entry["claimId"]]
        assert entry["resolvedAt"] is not None
    # Precedents accumulate as the ledger grows: the first claim
    # had none, the second saw the first, the third saw both.
    assert by_id[first["id"]]["precedentsUsedCount"] == 0
    assert by_id[second["id"]]["precedentsUsedCount"] == 1
    assert by_id[third["id"]]["precedentsUsedCount"] == 2

    limited = market_client.get(
        "/api/v1/learning/recent", params={"limit": 1}
    )
    limited_entries = limited.json()["entries"]
    assert len(limited_entries) == 1
    assert limited_entries[0]["claimId"] == third["id"]

    capped = market_client.get(
        "/api/v1/learning/recent", params={"limit": 500}
    )
    assert capped.status_code == 200  # cap clamps, never errors


# ---------------------------------------------------------------------
# (d) The unavailable path adds no scorecard entry.
# ---------------------------------------------------------------------


def test_unavailable_judge_adds_no_scorecard_entry(
    market_client, demo_fixture, monkeypatch
):
    monkeypatch.delenv("NEARAI_API_KEY", raising=False)
    spec = _post_spec(market_client, demo_fixture)
    claim = _issue(market_client, spec["id"])

    # No stub: the real juror honestly reports unavailable.
    judged = market_client.post(f"/api/v1/claims/{claim['id']}/judge")
    body = judged.json()
    assert body["status"] == "UNDER_RESOLUTION"
    assert body["jurorReport"]["status"] == "unavailable"
    assert body["jurorReport"]["precedentsUsed"] == []

    resp = market_client.get("/api/v1/jurors")
    assert resp.status_code == 200, resp.text
    assert resp.json()["jurors"] == []

    feed = market_client.get("/api/v1/learning/recent").json()
    assert all(
        e["claimId"] != claim["id"] for e in feed["entries"]
    )


# ---------------------------------------------------------------------
# (e) Panels for contested claims (spec 08 §9): a challenged
# claim is judged by up to three seats with the same prompt;
# the strict majority of returned verdicts decides; dissent is
# recorded per seat; no majority means no verdict. Seats are
# stubbed at juror.judge_claim_for_model — deterministic, no
# inference fabricated.
# ---------------------------------------------------------------------

SEATS = ("seat-a", "seat-b", "seat-c")


def _seat_fn(verdicts):
    """verdicts: seat model -> verdict, or None for a seat that
    cannot run (unavailable)."""

    def fn(claim, model, client=None):
        verdict = verdicts.get(model)
        if verdict is None:
            return {
                "status": "unavailable",
                "reason": "seat is down (stub)",
                "model": model,
                "juror": model,
                "precedentsUsed": [],
            }
        return {
            "status": "ok",
            "verdict": verdict,
            "rationale": f"{model} seat stub",
            "confidence": 0.9,
            "model": model,
            "juror": model,
            "completionId": f"chatcmpl-{model}",
            "verification": {
                "signatureKind": "gateway",
                "result": "verified",
            },
            "precedentsUsed": [],
        }

    return fn


@pytest.fixture()
def stub_seats(monkeypatch):
    def install(verdicts, seats=SEATS):
        monkeypatch.setenv("JUROR_PANEL_MODELS", ",".join(seats))
        monkeypatch.setattr(
            juror, "judge_claim_for_model", _seat_fn(verdicts)
        )

    return install


def _issue_challenged(client, spec_id):
    claim = _issue(client, spec_id)
    resp = client.post(
        f"/api/v1/claims/{claim['id']}/challenge",
        json={"challengerEntityId": CHALLENGER, "bondAmount": 750},
    )
    assert resp.status_code == 200, resp.text
    return claim


def test_panel_majority_upheld_and_dissent_recorded(
    market_client, demo_fixture, stub_seats
):
    spec = _post_spec(market_client, demo_fixture)
    claim = _issue_challenged(market_client, spec["id"])
    stub_seats({"seat-a": "UPHELD", "seat-b": "UPHELD", "seat-c": "REFUTED"})

    judged = market_client.post(f"/api/v1/claims/{claim['id']}/judge")
    assert judged.status_code == 200, judged.text
    body = judged.json()
    assert body["status"] == "RESOLVED_TRUE"
    report = body["jurorReport"]
    assert report["panel"] is True
    assert report["panelVerdict"] == "UPHELD"
    assert report["verdict"] == "UPHELD"
    assert len(report["panelReports"]) == 3
    by_seat = {r["juror"]: r for r in report["panelReports"]}
    assert by_seat["seat-c"]["verdict"] == "REFUTED"

    finalized = _finalize(
        market_client, claim["id"], "credit-committee-team-008"
    )
    assert finalized.json()["status"] == "ASSURATIZED"
    assert finalized.json()["withstood"] is True

    cards = {
        c["juror"]: c
        for c in market_client.get("/api/v1/jurors").json()["jurors"]
    }
    # Majority seats are credited with the terminal outcome.
    assert cards["seat-a"]["judgedCount"] == 1
    assert cards["seat-a"]["upheldCount"] == 1
    assert cards["seat-a"]["withstoodCount"] == 1
    assert cards["seat-a"]["panelDissents"] == 0
    assert cards["seat-b"]["upheldCount"] == 1
    # The dissenting seat is credited with nothing — but its
    # dissent is on its record.
    assert cards["seat-c"]["judgedCount"] == 0
    assert cards["seat-c"]["upheldCount"] == 0
    assert cards["seat-c"]["panelDissents"] == 1


def test_panel_no_majority_rests_under_resolution(
    market_client, demo_fixture, stub_seats
):
    spec = _post_spec(market_client, demo_fixture)
    claim = _issue_challenged(market_client, spec["id"])
    # 1 UPHELD, 1 REFUTED, 1 abstention: no strict majority.
    stub_seats({"seat-a": "UPHELD", "seat-b": "REFUTED", "seat-c": None})

    judged = market_client.post(f"/api/v1/claims/{claim['id']}/judge")
    body = judged.json()
    assert body["status"] == "UNDER_RESOLUTION"
    report = body["jurorReport"]
    assert report["panel"] is True
    assert report["panelVerdict"] is None
    assert report["status"] == "error"
    assert report["reason"] == "panel_no_majority"
    assert "verdict" not in report
    assert len(report["panelReports"]) == 3

    # Not finalized, not resolvable by fiat: finalize refuses.
    refused = _finalize(
        market_client, claim["id"], "credit-committee-team-009"
    )
    assert refused.status_code == 409


def test_panel_fallback_with_fewer_than_two_seats(
    market_client, demo_fixture, stub_juror, monkeypatch
):
    spec = _post_spec(market_client, demo_fixture)
    claim = _issue_challenged(market_client, spec["id"])
    monkeypatch.setenv("JUROR_PANEL_MODELS", "solo-seat")
    # The fallback IS the single-juror path — stubbed as usual.
    stub_juror(_report("UPHELD", model="solo-seat"))

    judged = market_client.post(f"/api/v1/claims/{claim['id']}/judge")
    body = judged.json()
    assert body["status"] == "RESOLVED_TRUE"
    assert body["jurorReport"]["panelNote"] == (
        "panel unavailable: fewer than two seats configured"
    )
    assert "panelReports" not in body["jurorReport"]
