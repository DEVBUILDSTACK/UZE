"""Platform extensions (owner tap, 2026-11-13 — James's own
words: build it all, as affiliate onboarding at Hack launch).

Pins: the embedded-expertise taxonomy (software + creative
categories and domains, routed by the matcher with no firm
names anywhere); the Project Side (lifecycle axis, execution
roster); the mock project-bid endpoint (budget check only,
labelled mock, awards nothing); and AffiliateProfile
onboarding validation with its portfolio structure and
sponsorship ordering. All fixtures synthetic.
"""

from __future__ import annotations

import json

import talent_profile as tp_mod
import affiliate_profile as af_mod

WEB_DEV = {
    "name": "Jo Park", "role": "Web Developer",
    "experience_years": 7, "skills": ["React", "booking flows"],
    "expected_rate_usd": 95, "certifications": [],
    "talent_type": "HUMAN_CONTRACTOR",
    "role_category": "WEB_DEVELOPER",
    "domain_focus": "TRADITIONAL_SOFTWARE_STACK",
}
DRONE_OP = {
    "name": "Sky Reyes", "role": "Drone Operator",
    "experience_years": 5, "skills": ["aerial footage", "site surveys"],
    "expected_rate_usd": 85, "certifications": ["FAA Part 107"],
    "talent_type": "HUMAN_CONTRACTOR",
    "role_category": "DRONE_OPERATOR",
    "domain_focus": "VISUAL_ASSETS",
}
GC = {
    "name": "Build Co", "role": "General Contractor",
    "experience_years": 18, "skills": ["resort construction"],
    "expected_rate_usd": 200, "certifications": ["CGC"],
    "talent_type": "HUMAN_CONTRACTOR",
    "role_category": "GENERAL_CONTRACTOR",
    "project_lifecycle_stage": "CONSTRUCTION_EXECUTION",
}
DEV_FIN = {
    "name": "Ana Ledger", "role": "Development Finance Analyst",
    "experience_years": 6, "skills": ["draw schedules", "yield on cost"],
    "expected_rate_usd": 105, "certifications": [],
    "talent_type": "HUMAN_CONTRACTOR",
    "role_category": "DEVELOPMENT_FINANCE_ANALYST",
    "project_lifecycle_stage": "ACQUISITION_ENTITLEMENT",
}


def test_embedded_expertise_taxonomy_validates():
    for raw, family in ((WEB_DEV, "software_development"),
                        (DRONE_OP, "creative_services")):
        profile, problems = tp_mod.validate_profile(raw)
        assert problems == []
        assert tp_mod.role_family(profile) == family


def test_matcher_routes_software_and_creative_by_domain():
    pool = [WEB_DEV, DRONE_OP]
    hits = tp_mod.match_profiles(
        {"role_family": "software_development",
         "domain_focus": "TRADITIONAL_SOFTWARE_STACK"}, pool)
    assert [h["name"] for h in hits] == ["Jo Park"]
    hits = tp_mod.match_profiles(
        {"role_family": "creative_services",
         "domain_focus": "VISUAL_ASSETS"}, pool)
    assert [h["name"] for h in hits] == ["Sky Reyes"]


def test_lifecycle_stage_validates_and_matches():
    profile, problems = tp_mod.validate_profile(GC)
    assert problems == []
    assert profile["project_lifecycle_stage"] == "CONSTRUCTION_EXECUTION"
    bad = dict(GC, project_lifecycle_stage="MOON_PHASE")
    profile, problems = tp_mod.validate_profile(bad)
    assert profile is None and problems == ["project_lifecycle_stage"]
    # A construction-stage need takes the GC, not the
    # acquisition-stage finance analyst.
    roster = tp_mod.assemble_project_side(
        {"project_lifecycle_stage": "CONSTRUCTION_EXECUTION"},
        [GC, DEV_FIN])
    assert [h["name"] for h in roster["GENERAL_CONTRACTOR"]] == ["Build Co"]
    assert "DEVELOPMENT_FINANCE_ANALYST" not in roster
    # A stageless need takes both.
    roster = tp_mod.assemble_project_side({}, [GC, DEV_FIN])
    assert "GENERAL_CONTRACTOR" in roster
    assert "DEVELOPMENT_FINANCE_ANALYST" in roster


def test_project_bid_endpoint_ranks_against_budget(client):
    r = client.post("/api/v1/talent/project-bid", json={
        "brief": "Resort lobby design",
        "budget_usd": 50000,
        "bids": [
            {"bidder": "Studio B", "amount_usd": 61000},
            {"bidder": "Studio A", "amount_usd": 42000,
             "role_category": "ARCHITECT"},
        ],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["mock"] is True and body["status"] == "mock_recorded"
    assert body["recommended_bidder"] == "Studio A"
    assert body["ranked_bids"][0]["within_budget"] is True
    assert body["ranked_bids"][1]["within_budget"] is False
    assert "yield" in body["evaluation_basis"]


def test_project_bid_endpoint_names_problems(client):
    r = client.post("/api/v1/talent/project-bid", json={
        "brief": "", "budget_usd": 0, "bids": [],
    })
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "INSUFFICIENT_DATA"
    assert set(body["missing_fields"]) == {"brief", "budget_usd", "bids"}


FULL_AFFILIATE = {
    "name": "Atelier Meridian",
    "creative_services": {"visualization": ["DRONE", "3D_RENDER"]},
    "software_development": {
        "app_types": ["BOOKING_ENGINE"], "stack_preference": "Next.js",
    },
    "portfolio": {
        "media_assets": ["https://example.com/drone.mp4"],
        "historical_projects": [{
            "project_name": "Casa Brisa Resort",
            "location": "Tamarindo, Costa Rica",
            "year": 2025, "asset_type": "Hospitality resort",
        }],
        "awards": [{
            "award_name": "Best Architectural Visualization",
            "year": 2025, "organization": "Americas Design Media Awards",
        }],
        "specialties": ["Oceanfront Resort"],
    },
    "sponsorship_status": True,
}


def test_affiliate_onboarding_validates_and_derives_slug():
    profile, problems = af_mod.validate_affiliate_profile(FULL_AFFILIATE)
    assert problems == []
    assert profile["slug"] == "atelier-meridian"
    assert profile["creative_services"]["visualization"] == [
        "DRONE", "3D_RENDER"]
    assert profile["sponsorship_status"] is True


def test_affiliate_onboarding_names_bad_fields_by_path():
    bad = dict(FULL_AFFILIATE, portfolio={
        "historical_projects": [{"project_name": "X"}]})
    profile, problems = af_mod.validate_affiliate_profile(bad)
    assert profile is None
    assert problems == ["portfolio.historical_projects[0]"]
    bad2 = dict(FULL_AFFILIATE,
                creative_services={"visualization": ["SMOKE_SIGNALS"]})
    profile, problems = af_mod.validate_affiliate_profile(bad2)
    assert profile is None
    assert problems == ["creative_services.visualization"]


def test_affiliate_record_and_sponsorship_ordering(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "AFFILIATE_PROFILES_PATH", str(tmp_path / "affiliates.jsonl"))
    plain, _ = af_mod.validate_affiliate_profile({"name": "Plain Studio"})
    sponsored, _ = af_mod.validate_affiliate_profile(FULL_AFFILIATE)
    af_mod.record_affiliate_profile(plain)
    af_mod.record_affiliate_profile(sponsored)
    rows = (tmp_path / "affiliates.jsonl").read_text().strip().splitlines()
    assert len(rows) == 2
    ordered = af_mod.order_affiliates([plain, sponsored])
    assert [p["name"] for p in ordered] == [
        "Atelier Meridian", "Plain Studio"]
    assert json.loads(rows[0])["profile"]["name"] == "Plain Studio"
