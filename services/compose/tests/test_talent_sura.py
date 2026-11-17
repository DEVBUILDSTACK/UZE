"""SURA — agentic guidance over the Talent marketplace
(owner directive, 2026-11-17 — see
docs/specifications/sura-agentic-guidance-v1.md).

Pins: provenance REQUIRED at feed ingestion; the
deterministic, bounded fit and switch-likelihood
heuristics (v1, published arithmetic); sourced candidates
flowing into the intents solver pool identically to
applied candidates, with provenance visible in offers;
demand and supply guidance; and geo-requirement filtering
(remote / hybrid / onsite). All fixtures synthetic — no
live signal source is touched or claimed anywhere here.
"""

from __future__ import annotations

import sura as sura_mod
import talent_profile as tp_mod

SOURCED_DEV = {
    "name": "Devika Rao", "role": "Software Engineer",
    "experience_years": 6,
    "skills": ["python", "react", "postgres"],
    "expected_rate_usd": 85, "certifications": [],
    "role_category": "SOFTWARE_ENGINEER",
    "engagement_class": "AFFILIATE_SOLOPRENEUR",
    "opportunity_category": "SOFTWARE_STACK",
}
PROVENANCE = {
    "source": "github",
    "source_ref": "github.com/devika-rao",
    "feed": "sura-dev-feed",
    "sourced_at": "2026-11-17T15:00:00+00:00",
    "basis": "sustained public commit activity on "
             "python services",
}
SIGNALS = {
    "last_activity_days": 6,
    "activity_events_90d": 48,
    "career_moves_5y": 2,
    "years_in_current_role": 3,
    "open_to_work": True,
}
APPLIED_PM = {
    "name": "Mara Quinn", "role": "Property Manager",
    "experience_years": 6, "skills": ["leasing", "budgets"],
    "expected_rate_usd": 40, "certifications": [],
    "engagement_class": "EMPLOYEE", "work_mode": "HYBRID",
    "opportunity_category": "HOSPITALITY",
}
SOURCED_PM = {
    "name": "Theo Lindqvist", "role": "Property Manager",
    "experience_years": 7, "skills": ["leasing"],
    "expected_rate_usd": 45, "certifications": [],
    "opportunity_category": "HOSPITALITY",
}


def _env(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "TALENT_PROFILES_PATH", str(tmp_path / "profiles.jsonl"))
    monkeypatch.setenv(
        "TALENT_SOURCED_PATH", str(tmp_path / "sourced.jsonl"))
    monkeypatch.setenv(
        "TALENT_APPLICATIONS_PATH", str(tmp_path / "apps.jsonl"))
    monkeypatch.setenv(
        "TALENT_ASSESSMENTS_PATH", str(tmp_path / "assess.jsonl"))
    monkeypatch.setenv(
        "TALENT_GUIDANCE_EVENTS_PATH",
        str(tmp_path / "guidance-events.jsonl"))


def _feed(profile, **overrides):
    body = {
        "profile": profile,
        "provenance": dict(PROVENANCE),
        "signals": dict(SIGNALS),
        "geo_availability": ["REMOTE", "HYBRID"],
    }
    body.update(overrides)
    return body


# --- Ingestion: provenance is required ---


def test_ingest_requires_complete_provenance(client):
    refused = client.post("/api/v1/talent/sura/sourced", json={
        "profile": SOURCED_DEV,
    })
    assert refused.status_code == 422
    fields = refused.json()["missing_fields"]
    for field in ("provenance.source", "provenance.source_ref",
                  "provenance.feed", "provenance.sourced_at",
                  "provenance.basis"):
        assert field in fields


def test_ingest_names_bad_provenance_and_signal_fields(client):
    bad = client.post("/api/v1/talent/sura/sourced", json=_feed(
        SOURCED_DEV,
        provenance=dict(PROVENANCE, source="carrier_pigeon"),
        signals={"activity_events_90d": -3},
    ))
    assert bad.status_code == 422
    fields = bad.json()["missing_fields"]
    assert "provenance.source" in fields
    assert "signals.activity_events_90d" in fields


def test_ingest_names_bad_profile_fields(client):
    bad = client.post("/api/v1/talent/sura/sourced", json=_feed(
        {"role": "Software Engineer"},
    ))
    assert bad.status_code == 422
    assert "profile.name" in bad.json()["missing_fields"]


def test_ingest_records_and_marks_provenance(
    client, monkeypatch, tmp_path
):
    _env(monkeypatch, tmp_path)
    ok = client.post(
        "/api/v1/talent/sura/sourced", json=_feed(SOURCED_DEV))
    assert ok.status_code == 200
    body = ok.json()
    assert body["status"] == "recorded"
    profile = body["profile"]
    assert profile["name"] == "Devika Rao"
    assert profile["provenance"]["source"] == "github"
    assert profile["provenance"]["feed"] == "sura-dev-feed"
    assert profile["geo_availability"] == ["REMOTE", "HYBRID"]
    # The maximal-signal fixture caps at 100 (spec §3.5).
    assert profile["sura"]["switch_likelihood"]["score"] == 100

    listed = client.get("/api/v1/talent/sura/sourced")
    assert listed.status_code == 200
    assert listed.json()["count"] == 1
    assert listed.json()["profiles"][0]["provenance"]["basis"]


# --- Switch-likelihood: deterministic, bounded, honest ---


def test_switch_likelihood_bands_and_missing_basis():
    mid = sura_mod.switch_likelihood({
        "years_in_current_role": 5,
        "career_moves_5y": 1,
        "activity_events_90d": 8,
        "last_activity_days": 60,
    })
    # 18 (tenure) + 15 (mobility) + 10 (activity)
    # + 6 (recency) = 49; openness undeclared.
    assert mid["score"] == 49
    assert mid["missing_signals"] == ["open_to_work"]
    assert mid["components"]["declared_openness"] is None
    assert mid["heuristic"] == "sura_switch_heuristic_v1"


def test_switch_likelihood_bounds_and_determinism():
    assert sura_mod.switch_likelihood({})["score"] == 0
    assert sura_mod.switch_likelihood(SIGNALS)["score"] == 100
    assert sura_mod.switch_likelihood(
        SIGNALS) == sura_mod.switch_likelihood(SIGNALS)
    quiet = sura_mod.switch_likelihood({
        "years_in_current_role": 9,
        "career_moves_5y": 0,
        "activity_events_90d": 0,
        "last_activity_days": 400,
        "open_to_work": False,
    })
    assert quiet["score"] == 13  # 8 + 5 + 0 + 0 + 0
    assert 0 <= quiet["score"] <= 100


# --- Fit score: deterministic, bounded, explained ---


def test_fit_score_components_and_explanation():
    record, problems = sura_mod.validate_feed_record(
        _feed(SOURCED_DEV))
    assert problems == []
    profile = record["profile"]
    need = {
        "role": "Software Engineer",
        "role_family": "software_development",
        "skills": ["python", "react", "go"],
        "min_experience_years": 4,
        "geo_requirement": "REMOTE",
    }
    fit = sura_mod.fit_score(need, profile)
    # skills 2/3 → 33.33/50; role 20/20; geo 20/20;
    # experience 10/10 → 83.33 over 100 available → 83.
    assert fit["score"] == 83
    assert fit["skills_covered"] == ["python", "react"]
    assert fit["skills_missing"] == ["go"]
    assert fit["components"]["skill_coverage"]["available"] == 50
    assert fit["heuristic"] == "sura_fit_heuristic_v1"
    assert sura_mod.fit_score(need, profile) == fit


def test_fit_score_bounds_on_mismatch():
    record, problems = sura_mod.validate_feed_record(
        _feed(SOURCED_DEV))
    assert problems == []
    fit = sura_mod.fit_score(
        {"role": "Oncologist", "skills": ["oncology"]},
        record["profile"],
    )
    assert 0 <= fit["score"] <= 100
    assert fit["skills_missing"] == ["oncology"]


# --- Sourced supply enters the solver pool, marked ---


def test_sourced_candidates_solve_with_provenance(
    client, monkeypatch, tmp_path
):
    _env(monkeypatch, tmp_path)
    applied, problems = tp_mod.validate_profile(APPLIED_PM)
    assert problems == []
    tp_mod.record_profile(applied, "mara@example.com")
    ingested = client.post(
        "/api/v1/talent/sura/sourced", json=_feed(SOURCED_PM))
    assert ingested.status_code == 200

    solved = client.post(
        "/api/v1/talent/intents/solve",
        json={"need": {"role": "Property Manager",
                       "opportunity_category": "HOSPITALITY"}},
    )
    assert solved.status_code == 200
    offers = solved.json()["offers"]
    names = [o["name"] for o in offers]
    assert names == ["Mara Quinn", "Theo Lindqvist"]
    by_name = {o["name"]: o for o in offers}
    # The sourced offer carries its provenance in band;
    # the applied offer carries none.
    assert by_name["Theo Lindqvist"]["provenance"]["source"] \
        == "github"
    assert "provenance" not in by_name["Mara Quinn"]


def test_applied_profiles_have_no_switch_likelihood():
    applied, problems = tp_mod.validate_profile(APPLIED_PM)
    assert problems == []
    # No signals were ever supplied for an applied profile:
    # SURA returns None rather than inventing a score.
    assert sura_mod.profile_switch_likelihood(applied) is None


# --- Demand guidance ---


def test_demand_guidance_pool_split_and_provenance(
    client, monkeypatch, tmp_path
):
    _env(monkeypatch, tmp_path)
    applied, problems = tp_mod.validate_profile(APPLIED_PM)
    assert problems == []
    tp_mod.record_profile(applied, "mara@example.com")
    client.post(
        "/api/v1/talent/sura/sourced", json=_feed(SOURCED_PM))

    guided = client.post(
        "/api/v1/talent/sura/guidance/demand",
        json={"need": {"role": "Property Manager",
                       "opportunity_category": "HOSPITALITY"}},
    )
    assert guided.status_code == 200
    body = guided.json()
    assert body["kind"] == "DEMAND_GUIDANCE"
    assert body["pool"]["total"] == 2
    assert body["pool"]["applied"] == 1
    assert body["pool"]["sourced"] == 1
    sourced = [c for c in body["candidates"] if c["sourced"]]
    assert len(sourced) == 1
    assert sourced[0]["provenance"]["feed"] == "sura-dev-feed"
    assert sourced[0]["switch_likelihood"]["score"] == 100
    applied_c = [c for c in body["candidates"] if not c["sourced"]]
    assert applied_c[0]["switch_likelihood"] is None


def test_demand_guidance_empty_pool_and_other_route(
    monkeypatch, tmp_path
):
    _env(monkeypatch, tmp_path)
    empty = sura_mod.demand_guidance(
        {"role": "Property Manager"}, [])
    assert empty["status"] == "no_supply"
    assert any("feed" in r for r in empty["recommendations"])

    routed = sura_mod.demand_guidance(
        {"role": "Oncologist", "opportunity_category": "OTHER"},
        [],
    )
    assert routed["status"] == "routed_to_affiliate_expert"
    assert routed["routing"] == "affiliate_expert"
    assert routed["candidates"] == []


# --- Supply guidance: geo filtering + fit explanation ---


def test_supply_guidance_filters_by_geo_requirement(
    client, monkeypatch, tmp_path
):
    _env(monkeypatch, tmp_path)
    client.post(
        "/api/v1/talent/sura/sourced", json=_feed(SOURCED_DEV))
    needs = [
        {"role": "Software Engineer",
         "role_family": "software_development",
         "skills": ["python"], "geo_requirement": "REMOTE"},
        {"role": "Software Engineer",
         "role_family": "software_development",
         "skills": ["python"], "geo_requirement": "ONSITE"},
    ]
    guided = client.post(
        "/api/v1/talent/sura/guidance/supply",
        json={"profile_name": "Devika Rao", "needs": needs},
    )
    assert guided.status_code == 200
    body = guided.json()
    # The fixture declares REMOTE + HYBRID availability:
    # the REMOTE role surfaces; the ONSITE role is excluded
    # by geo and counted, never silently dropped.
    assert [r["geo_requirement"] for r in body["roles"]] == [
        "REMOTE"]
    assert body["excluded_by_geo"] == 1
    fit = body["roles"][0]["fit"]
    assert fit["skills_covered"] == ["python"]
    assert fit["skills_missing"] == []
    assert any("geo" in n for n in body["notes"])


def test_supply_guidance_profile_object_and_notes():
    profile, problems = tp_mod.validate_profile({
        "name": "Sam Ortiz", "role": "Financial Analyst",
        "experience_years": 6, "skills": ["excel"],
        "expected_rate_usd": 55, "certifications": [],
    })
    assert problems == []
    guided = sura_mod.supply_guidance(profile, [
        {"role": "Financial Analyst",
         "role_family": "knowledge_work", "skills": ["excel"]},
    ])
    assert guided["candidate"]["name"] == "Sam Ortiz"
    assert guided["roles"][0]["fit"]["score"] > 0
    # No assessment on file → the guidance says so.
    assert any("assessment" in n for n in guided["notes"])


def test_supply_guidance_unknown_profile_404s(
    client, monkeypatch, tmp_path
):
    _env(monkeypatch, tmp_path)
    missing = client.post(
        "/api/v1/talent/sura/guidance/supply",
        json={"profile_name": "Nobody Here", "needs": []},
    )
    assert missing.status_code == 404
    assert missing.json()["error"] == "PROFILE_NOT_FOUND"


# --- Guidance events: the RL talent environment's feed ---


def _guided_pool(client, monkeypatch, tmp_path):
    """Ingest the sourced PM and take demand guidance on
    the PM need; returns the recorded guidance event."""
    _env(monkeypatch, tmp_path)
    client.post(
        "/api/v1/talent/sura/sourced", json=_feed(SOURCED_PM))
    guided = client.post(
        "/api/v1/talent/sura/guidance/demand",
        json={"need": {"role": "Property Manager",
                       "opportunity_category": "HOSPITALITY",
                       "skills": ["leasing"],
                       "geo_requirement": "REMOTE"}},
    )
    assert guided.status_code == 200
    assert guided.json()["recorded_event_id"]
    events = sura_mod.load_guidance_events()
    assert len(events) == 1
    return events[0]


def test_guidance_events_recorded_episode_ready(
    client, monkeypatch, tmp_path
):
    event = _guided_pool(client, monkeypatch, tmp_path)
    # The guidance given: side, subject, recommendations,
    # scores — under the incumbent heuristic policy.
    assert event["side"] == "demand"
    assert event["subject"] == "Property Manager"
    assert event["policy"] == "sura_fit_heuristic_v1"
    assert event["guidance"]["status"] == "guided"
    assert event["guidance"]["top_fit_score"] is not None
    assert event["guidance"]["notes"]
    # The context: role/candidate, skills, geo-requirement.
    assert event["context"]["candidate"] == "Theo Lindqvist"
    assert event["context"]["skills"] == ["leasing"]
    assert event["context"]["geo_requirement"] == "REMOTE"
    # The outcome fields exist and are open — nothing is
    # claimed settled before the lifecycle settles it.
    outcome = event["outcome"]
    assert outcome["status"] == "open"
    assert outcome["matched"] is None
    assert outcome["placed"] is None
    assert outcome["accepted"] is None
    assert outcome["rejected"] is None
    assert outcome["application_ref"] is None


def test_guidance_outcomes_settle_with_the_lifecycle(
    client, monkeypatch, tmp_path
):
    _guided_pool(client, monkeypatch, tmp_path)
    created = client.post(
        "/api/v1/talent/applications",
        json={"profile_ref": "Theo Lindqvist",
              "role_ref": "Property Manager"},
    )
    assert created.status_code == 200
    app_id = created.json()["application_id"]

    # Entering the lifecycle links and marks matched.
    event = sura_mod.load_guidance_events()[0]
    assert event["outcome"]["application_ref"] == app_id
    assert event["outcome"]["matched"] is True
    assert event["outcome"]["status"] == "in_progress"
    assert event["outcome"]["accepted"] is None

    for target in ("APPLIED", "IN_PROGRESS", "ACCEPTED"):
        moved = client.post(
            f"/api/v1/talent/applications/{app_id}/transition",
            json={"to_state": target, "actor": "desk"},
        )
        assert moved.status_code == 200

    # ACCEPTED settles the outcome: placed + accepted.
    event = sura_mod.load_guidance_events()[0]
    outcome = event["outcome"]
    assert outcome["status"] == "settled_accepted"
    assert outcome["placed"] is True
    assert outcome["accepted"] is True
    assert outcome["rejected"] is False
    assert outcome["settled_at"] is not None


def test_guidance_outcomes_settle_rejected(
    client, monkeypatch, tmp_path
):
    _guided_pool(client, monkeypatch, tmp_path)
    created = client.post(
        "/api/v1/talent/applications",
        json={"profile_ref": "Theo Lindqvist",
              "role_ref": "Property Manager"},
    )
    app_id = created.json()["application_id"]
    for target in ("APPLIED", "REJECTED"):
        moved = client.post(
            f"/api/v1/talent/applications/{app_id}/transition",
            json={"to_state": target, "actor": "desk"},
        )
        assert moved.status_code == 200
    outcome = sura_mod.load_guidance_events()[0]["outcome"]
    assert outcome["status"] == "settled_rejected"
    assert outcome["rejected"] is True
    assert outcome["accepted"] is False
    assert outcome["placed"] is False


def test_unlinked_applications_do_not_settle_events(
    client, monkeypatch, tmp_path
):
    _guided_pool(client, monkeypatch, tmp_path)
    created = client.post(
        "/api/v1/talent/applications",
        json={"profile_ref": "Someone Else",
              "role_ref": "Property Manager"},
    )
    assert created.status_code == 200
    outcome = sura_mod.load_guidance_events()[0]["outcome"]
    assert outcome["status"] == "open"
    assert outcome["application_ref"] is None
