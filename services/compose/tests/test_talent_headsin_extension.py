"""Talent extension v1 (owner rulings, 2026-11-17 — see
docs/specifications/talent-extension-headsin-v1.md).

Pins: the people-layer taxonomy (engagement class, employee-
only work mode, opportunity category, major-firm years);
the assessment object and its recording endpoint; the ATS
lifecycle state machine with its event record; category
routing (native vs labelled affiliate-expert route);
experience-segment routing (placement / intents marketplace
/ elite bypass); the scorecard (matcher + assessment); and
the intents solver endpoint with its NEAR AI honesty label.
All fixtures synthetic.
"""

from __future__ import annotations

import talent_ats as ats_mod
import talent_profile as tp_mod

EMPLOYEE = {
    "name": "Mara Quinn", "role": "Property Manager",
    "experience_years": 6, "skills": ["leasing", "budgets"],
    "expected_rate_usd": 40, "certifications": [],
    "talent_type": "HUMAN_EMPLOYEE",
    "asset_class_focus": "HOSPITALITY",
    "engagement_class": "EMPLOYEE",
    "work_mode": "HYBRID",
    "opportunity_category": "HOSPITALITY",
}
ASSESSMENT = {
    "role": "Property Manager",
    "score": 88,
    "duration_seconds": 243,
    "skills_proven": ["leasing", "budgets"],
    "completed_at": "2026-11-17T12:00:00+00:00",
}


def _validated(raw):
    profile, problems = tp_mod.validate_profile(raw)
    assert problems == []
    return profile


# --- People-layer taxonomy ---


def test_people_layer_fields_validate_and_normalize():
    profile = _validated(dict(EMPLOYEE, assessment=ASSESSMENT))
    assert profile["engagement_class"] == "EMPLOYEE"
    assert profile["work_mode"] == "HYBRID"
    assert profile["opportunity_category"] == "HOSPITALITY"
    assert profile["assessment"]["score"] == 88


def test_pre_extension_profiles_stay_valid():
    legacy = {
        "name": "Old Timer", "role": "Maintenance",
        "experience_years": 9, "skills": ["hvac"],
        "expected_rate_usd": 30,
    }
    profile = _validated(legacy)
    assert profile["engagement_class"] is None
    assert profile["work_mode"] is None
    assert profile["assessment"] is None


def test_work_mode_rejected_for_non_employees():
    for raw in (
        dict(EMPLOYEE, engagement_class="AFFILIATE_SOLOPRENEUR"),
        dict(EMPLOYEE, engagement_class="AFFILIATE_EXPERT"),
        dict(EMPLOYEE, engagement_class="AGENTIC_SERVICE"),
    ):
        profile, problems = tp_mod.validate_profile(raw)
        assert profile is None and problems == ["work_mode"]


def test_work_mode_rejected_without_employee_class():
    raw = dict(EMPLOYEE)
    del raw["engagement_class"]
    profile, problems = tp_mod.validate_profile(raw)
    assert profile is None and problems == ["work_mode"]


def test_bad_people_layer_values_are_named():
    raw = dict(EMPLOYEE, engagement_class="PARTNER",
               opportunity_category="SPACE_TRAVEL")
    profile, problems = tp_mod.validate_profile(raw)
    assert profile is None
    # The invalid class also trips the work-mode rule: a
    # profile not declared EMPLOYEE may not carry one.
    assert problems == [
        "engagement_class", "work_mode", "opportunity_category",
    ]


# --- Assessment object ---


def test_assessment_validation_names_inner_fields():
    good, problems = tp_mod.validate_assessment(ASSESSMENT)
    assert problems == [] and good["score"] == 88
    bad, problems = tp_mod.validate_assessment(
        {"role": "Property Manager", "score": 140}
    )
    assert bad is None
    assert problems == [
        "score", "duration_seconds", "skills_proven",
        "completed_at",
    ]


def test_profile_with_bad_assessment_names_assessment():
    raw = dict(EMPLOYEE, assessment={"role": "x", "score": -1})
    profile, problems = tp_mod.validate_profile(raw)
    assert profile is None and problems == ["assessment"]


# --- Category routing ---


def test_category_routing_native_vs_affiliate():
    for cat, klass in (("HOSPITALITY", "FOCUS"),
                       ("INCOME_CRE", "FOCUS"),
                       ("SOFTWARE_STACK", "EXPERTISE"),
                       ("BLOCKCHAIN_TECH", "EXPERTISE")):
        route = tp_mod.route_category(cat)
        assert route["routing"] == "native"
        assert route["category_class"] == klass
    route = tp_mod.route_category("OTHER")
    assert route["routing"] == "affiliate_expert"
    assert route["category_class"] == "OTHER"
    assert route["route_reason"]


def test_other_category_is_a_labelled_route_not_a_match():
    pool = [_validated(EMPLOYEE)]
    result = tp_mod.scorecard_matches(
        {"role": "Property Manager", "opportunity_category": "OTHER"},
        pool,
    )
    assert result["status"] == "routed_to_affiliate_expert"
    assert result["routing"] == "affiliate_expert"
    assert result["matches"] == []


# --- Scorecard: matcher + assessment ---


def _pm(name, score):
    raw = {
        "name": name, "role": "Property Manager",
        "experience_years": 6, "skills": ["leasing"],
        "expected_rate_usd": 40, "certifications": [],
    }
    if score is not None:
        raw["assessment"] = dict(ASSESSMENT, score=score)
    return _validated(raw)


def test_scorecard_ranks_by_assessment_score():
    pool = [_pm("Low", 62), _pm("High", 91), _pm("None", None)]
    result = tp_mod.scorecard_matches(
        {"role": "Property Manager"}, pool
    )
    assert result["status"] == "matched"
    names = [m["name"] for m in result["matches"]]
    assert names == ["High", "Low", "None"]
    assert result["matches"][0]["scorecard"]["rank"] == 1
    assert result["matches"][0]["scorecard"]["assessment_score"] == 91


def test_scorecard_min_assessment_score_filters():
    pool = [_pm("Low", 62), _pm("High", 91), _pm("None", None)]
    result = tp_mod.scorecard_matches(
        {"role": "Property Manager", "min_assessment_score": 70},
        pool,
    )
    assert [m["name"] for m in result["matches"]] == ["High"]


# --- Experience segmentation ---

EARLY = {
    "name": "New Grad", "role": "Financial Analyst",
    "experience_years": 1, "skills": ["excel"],
    "expected_rate_usd": 25, "certifications": [],
}
ELITE = {
    "name": "Elite Dev", "role": "Machine Learning Engineer",
    "experience_years": 3,
    "skills": ["machine learning", "python"],
    "expected_rate_usd": 120, "certifications": [],
    "major_firm_years": 6,
}


def test_segments_derive_from_declared_fields():
    assert tp_mod.experience_segment(
        _validated(EMPLOYEE)) == "PLACEMENT_FOCUS"
    assert tp_mod.experience_segment(
        _validated(EARLY)) == "EARLY_CAREER"
    assert tp_mod.experience_segment(
        _validated(ELITE)) == "ELITE_EXCEPTION"


def test_experienced_role_routes_to_placement():
    need = {"target_segment": "PLACEMENT_FOCUS"}
    assert tp_mod.segment_route(need, _validated(EMPLOYEE)) == "placement"


def test_early_career_routes_to_intents_marketplace():
    early = _validated(EARLY)
    # An early-career-targeted (white-collar) need is served
    # by the autonomous marketplace, not the placement desk.
    assert tp_mod.segment_route(
        {"target_segment": "EARLY_CAREER"}, early
    ) == "intents_marketplace"
    # And early-career supply against a placement-focus need
    # routes the same way.
    assert tp_mod.segment_route(
        {"target_segment": "PLACEMENT_FOCUS"}, early
    ) == "intents_marketplace"


def test_elite_profile_bypasses_the_age_band():
    elite = _validated(ELITE)
    assert tp_mod.segment_route(
        {"target_segment": "EARLY_CAREER"}, elite
    ) == "placement"
    assert tp_mod.segment_route({}, elite) == "placement"


# --- ATS lifecycle (pure state machine) ---


def test_lifecycle_transitions_and_terminal_states():
    app = ats_mod.new_application("talent/mara", "role/pm-1")
    assert app["state"] == "RECOMMENDED"
    for target in ("APPLIED", "IN_PROGRESS", "ACCEPTED"):
        app, problems = ats_mod.apply_transition(app, target, "desk")
        assert problems == []
        assert app["state"] == target
    # ACCEPTED is terminal.
    app2, problems = ats_mod.apply_transition(app, "APPLIED")
    assert app2 is None and problems == ["transition"]
    states = [
        (e["from_state"], e["to_state"]) for e in app["events"]
    ]
    assert states == [
        (None, "RECOMMENDED"),
        ("RECOMMENDED", "APPLIED"),
        ("APPLIED", "IN_PROGRESS"),
        ("IN_PROGRESS", "ACCEPTED"),
    ]


def test_lifecycle_rejects_skips_and_unknown_states():
    app = ats_mod.new_application("talent/mara", "role/pm-1")
    skipped, problems = ats_mod.apply_transition(app, "ACCEPTED")
    assert skipped is None and problems == ["transition"]
    unknown, problems = ats_mod.apply_transition(app, "HIRED")
    assert unknown is None and problems == ["to_state"]


# --- Endpoints (headless plane) ---


def _env(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "TALENT_APPLICATIONS_PATH", str(tmp_path / "apps.jsonl"))
    monkeypatch.setenv(
        "TALENT_ASSESSMENTS_PATH", str(tmp_path / "assess.jsonl"))
    monkeypatch.setenv(
        "TALENT_PROFILES_PATH", str(tmp_path / "profiles.jsonl"))


def test_application_endpoints_record_events(client, monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    created = client.post(
        "/api/v1/talent/applications",
        json={"profile_ref": "talent/mara", "role_ref": "role/pm-1"},
    )
    assert created.status_code == 200
    app = created.json()
    assert app["state"] == "RECOMMENDED"
    app_id = app["application_id"]

    illegal = client.post(
        f"/api/v1/talent/applications/{app_id}/transition",
        json={"to_state": "ACCEPTED"},
    )
    assert illegal.status_code == 422
    assert illegal.json()["error"] == "ILLEGAL_TRANSITION"

    for target in ("APPLIED", "IN_PROGRESS"):
        moved = client.post(
            f"/api/v1/talent/applications/{app_id}/transition",
            json={"to_state": target, "actor": "candidate"},
        )
        assert moved.status_code == 200
        assert moved.json()["state"] == target

    said = client.post(
        f"/api/v1/talent/applications/{app_id}/messages",
        json={"author": "employer", "body": "Can you start Monday?"},
    )
    assert said.status_code == 200

    view = client.get(f"/api/v1/talent/applications/{app_id}")
    assert view.status_code == 200
    body = view.json()
    assert body["state"] == "IN_PROGRESS"
    assert [e["to_state"] for e in body["events"]] == [
        "RECOMMENDED", "APPLIED", "IN_PROGRESS",
    ]
    assert body["messages"][0]["body"] == "Can you start Monday?"

    missing = client.get("/api/v1/talent/applications/app_nope")
    assert missing.status_code == 404
    assert missing.json()["error"] == "APPLICATION_NOT_FOUND"


def test_assessment_endpoint_records_and_names_problems(
    client, monkeypatch, tmp_path
):
    _env(monkeypatch, tmp_path)
    ok = client.post(
        "/api/v1/talent/assessments",
        json={"profile_name": "Mara Quinn", "assessment": ASSESSMENT},
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "recorded"
    bad = client.post(
        "/api/v1/talent/assessments",
        json={"profile_name": "Mara Quinn",
              "assessment": {"score": 900}},
    )
    assert bad.status_code == 422
    fields = bad.json()["missing_fields"]
    assert "assessment.score" in fields
    assert "assessment.role" in fields


def test_solver_endpoint_labels_solver_and_inference(
    client, monkeypatch, tmp_path
):
    _env(monkeypatch, tmp_path)
    tp_mod.record_profile(_validated(EMPLOYEE), "mara@example.com")
    solved = client.post(
        "/api/v1/talent/intents/solve",
        json={"need": {"role": "Property Manager",
                       "opportunity_category": "HOSPITALITY"}},
    )
    assert solved.status_code == 200
    body = solved.json()
    assert body["intent"]["kind"] == "ROLE_REQUIREMENT"
    assert body["solver"] == "deterministic_matcher_v1"
    # The honesty label: NEAR AI inference is NOT live.
    assert body["inference"]["provider"] == "NEAR AI"
    assert body["inference"]["status"] == "unavailable"
    assert "402" in body["inference"]["detail"]
    assert body["routing"] == "native"
    assert [o["name"] for o in body["offers"]] == ["Mara Quinn"]

    routed = client.post(
        "/api/v1/talent/intents/solve",
        json={"need": {"role": "Oncologist",
                       "opportunity_category": "OTHER"}},
    )
    body = routed.json()
    assert body["status"] == "routed_to_affiliate_expert"
    assert body["offers"] == []
