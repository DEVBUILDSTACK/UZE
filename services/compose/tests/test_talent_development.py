"""Development, Design & Wellness talent expansion (owner
tap, 2026-11-13 — James's own override of recording standby
and the hackathon scope ruling).

Pins: the new taxonomy fields (role_category, domain_focus)
validate as OPTIONAL and strict-when-present, with `role`
itself staying free text; the matcher routes a Resort
Development need to a project team (Architect, Interior
Designer, Spa Consultant); operations profiles never leak
into the team; and referral edges validate, record, and walk
as a chain (Architect → Interior Designer → Spa Consultant).
All fixtures are synthetic.
"""

from __future__ import annotations

import json

import talent_profile as tp_mod

ARCHITECT_RESORT = {
    "name": "Ana Duarte", "role": "Resort Architect",
    "experience_years": 14,
    "skills": ["resort master planning", "commercial architecture"],
    "expected_rate_usd": 160, "certifications": ["AIA"],
    "asset_class_focus": "HOSPITALITY",
    "talent_type": "HUMAN_CONTRACTOR",
    "role_category": "ARCHITECT",
    "domain_focus": "HOSPITALITY_RESORT_DESIGN",
}
INTERIOR_DESIGNER = {
    "name": "Mia Chen", "role": "Interior Designer",
    "experience_years": 9,
    "skills": ["flooring", "wallcoverings", "furnishings", "appointments"],
    "expected_rate_usd": 120, "certifications": ["NCIDQ"],
    "asset_class_focus": "HOSPITALITY",
    "talent_type": "HUMAN_CONTRACTOR",
    "role_category": "INTERIOR_DESIGNER",
    "domain_focus": "HOSPITALITY_RESORT_DESIGN",
}
SPA_CONSULTANT = {
    "name": "Rafael Ortiz", "role": "Wellness Spa Consultant",
    "experience_years": 8,
    "skills": ["spa planning", "wellness programming", "rejuvenation"],
    "expected_rate_usd": 110, "certifications": [],
    "asset_class_focus": "HOSPITALITY",
    "talent_type": "HUMAN_CONTRACTOR",
    "role_category": "WELLNESS_SPA_CONSULTANT",
    "domain_focus": "HOSPITALITY_RESORT_DESIGN",
}
OPS_GM = {
    "name": "Pat Morgan", "role": "General Manager",
    "experience_years": 11, "skills": ["hotel operations"],
    "expected_rate_usd": 118000, "certifications": [],
    "asset_class_focus": "HOSPITALITY", "talent_type": "HUMAN_EMPLOYEE",
}
POOL = [ARCHITECT_RESORT, INTERIOR_DESIGNER, SPA_CONSULTANT, OPS_GM]

BASE = {
    "name": "Sam Field", "role": "Lighting Designer",
    "experience_years": 4, "skills": ["lighting design"],
    "expected_rate_usd": 90,
}


def test_dev_taxonomy_fields_validate_and_canonicalize():
    raw = dict(BASE, role_category="architect",
               domain_focus="hospitality_resort_design")
    profile, problems = tp_mod.validate_profile(raw)
    assert problems == []
    assert profile["role_category"] == "ARCHITECT"
    assert profile["domain_focus"] == "HOSPITALITY_RESORT_DESIGN"


def test_dev_taxonomy_fields_are_optional_but_strict():
    profile, problems = tp_mod.validate_profile(BASE)
    assert problems == []
    assert profile["role_category"] is None
    assert profile["domain_focus"] is None
    bad = dict(BASE, role_category="ASTROLOGER")
    profile, problems = tp_mod.validate_profile(bad)
    assert profile is None and problems == ["role_category"]
    bad = dict(BASE, domain_focus="MARS")
    profile, problems = tp_mod.validate_profile(bad)
    assert profile is None and problems == ["domain_focus"]


def test_role_stays_free_text():
    # No closed role enum: a role nobody enumerated still
    # validates — the taxonomy rides in role_category.
    raw = dict(BASE, role="Underwater Basket Weaver")
    profile, problems = tp_mod.validate_profile(raw)
    assert problems == [] and profile["role"] == "Underwater Basket Weaver"


def test_role_family_recognizes_development_design():
    assert tp_mod.role_family(ARCHITECT_RESORT) == "development_design"
    assert tp_mod.role_family(INTERIOR_DESIGNER) == "development_design"
    # Even without a declared category, the role text routes.
    assert tp_mod.role_family(BASE) == "development_design"
    assert tp_mod.role_family(OPS_GM) == "operations"


def test_resort_development_need_assembles_the_project_team():
    need = {
        "asset_class_focus": "HOSPITALITY",
        "domain_focus": "HOSPITALITY_RESORT_DESIGN",
    }
    team = tp_mod.assemble_project_team(need, POOL)
    assert [h["name"] for h in team["ARCHITECT"]] == ["Ana Duarte"]
    assert [h["name"] for h in team["INTERIOR_DESIGNER"]] == ["Mia Chen"]
    assert [h["name"] for h in team["WELLNESS_SPA_CONSULTANT"]] == ["Rafael Ortiz"]
    # The operations GM is never part of a project team.
    assert all(
        h["name"] != "Pat Morgan"
        for hits in team.values() for h in hits
    )


def test_matcher_development_design_single_role():
    need = {"role_family": "development_design",
            "role_category": "INTERIOR_DESIGNER",
            "asset_class_focus": "HOSPITALITY"}
    hits = tp_mod.match_profiles(need, POOL)
    assert [h["name"] for h in hits] == ["Mia Chen"]
    # A residential need does not take the hospitality team.
    need_res = dict(need, asset_class_focus="RESIDENTIAL")
    assert tp_mod.match_profiles(need_res, POOL) == []


def test_referral_edges_validate_record_and_chain(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "TALENT_REFERRALS_PATH", str(tmp_path / "referrals.jsonl"))
    e1, p1 = tp_mod.validate_referral({
        "referrer_name": "Ana Duarte",
        "referred_name": "Mia Chen",
        "referred_role_category": "interior_designer",
        "context_ref": "resort-development-1",
    })
    assert p1 == [] and e1["referred_role_category"] == "INTERIOR_DESIGNER"
    e2, p2 = tp_mod.validate_referral({
        "referrer_name": "Mia Chen",
        "referred_name": "Rafael Ortiz",
        "referred_role_category": "WELLNESS_SPA_CONSULTANT",
    })
    assert p2 == []
    tp_mod.record_referral(e1)
    tp_mod.record_referral(e2)
    rows = (tmp_path / "referrals.jsonl").read_text().strip().splitlines()
    assert len(rows) == 2
    edges = [json.loads(r)["edge"] for r in rows]
    assert tp_mod.referral_chain(edges, "Ana Duarte") == [
        "Mia Chen", "Rafael Ortiz",
    ]
    # A self-referral is refused by name.
    bad, problems = tp_mod.validate_referral({
        "referrer_name": "Ana Duarte", "referred_name": "Ana Duarte"})
    assert bad is None and problems == ["referred_name"]
