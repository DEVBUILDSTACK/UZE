"""Development context routing (owner tap, 2026-11-13).

Pins: without a declared context the development path is
the standing offer, unchanged; with a declared stage it
names that stage's categories; a resort/wellness design
domain adds the wellness consultant and a commercial one
does not; the operations stage routes no development team;
and the context flows through analyze_multiyear untouched
by the financials.
"""

from __future__ import annotations

from email_gateway import analyze_multiyear
from talent_profile import derive_talent_placement

YEARS = [{
    "line_items": {
        "Rental Revenue": 1_000_000,
        "Payroll - Property Manager": -60_000,
        "Payroll - Maintenance": -45_000,
    }
}]


def _dev_path(out):
    return next(p for p in out["paths"] if p["kind"] == "development_design")


def test_no_context_is_the_standing_offer():
    dev = _dev_path(derive_talent_placement(YEARS))
    assert dev["mode"] == "standing_offer"
    assert dev["requirements"] == []
    assert "Architect" in dev["roles"]
    assert "General Contractor" not in dev["roles"]


def test_design_stage_routes_the_design_team():
    dev = _dev_path(derive_talent_placement(YEARS, {
        "project_lifecycle_stage": "DESIGN_ARCHITECTURE",
        "domain_focus": "COMMERCIAL_ARCHITECTURE",
        "asset_class_focus": "RESIDENTIAL",
    }))
    assert dev["mode"] == "context_routed"
    cats = [r["role_category"] for r in dev["requirements"]]
    assert cats == [
        "ARCHITECT", "INTERIOR_DESIGNER",
        "LIGHTING_TECHNOLOGY_INTEGRATOR", "CAD_DRAFTER",
        "PRE_SALES_BROKER",
    ]
    assert all(
        r["domain_focus"] == "COMMERCIAL_ARCHITECTURE"
        for r in dev["requirements"]
    )
    # Operations derivation is untouched by the context.
    ops = next(
        p for p in derive_talent_placement(YEARS)["paths"]
        if p["kind"] == "operations"
    )
    assert "Property Manager" in ops["roles"]


def test_resort_domain_adds_wellness_commercial_does_not():
    resort = _dev_path(derive_talent_placement(YEARS, {
        "project_lifecycle_stage": "DESIGN_ARCHITECTURE",
        "domain_focus": "HOSPITALITY_RESORT_DESIGN",
    }))
    assert "WELLNESS_SPA_CONSULTANT" in [
        r["role_category"] for r in resort["requirements"]
    ]
    assert "Wellness Spa Consultant" in resort["roles"]


def test_construction_stage_routes_project_side():
    dev = _dev_path(derive_talent_placement(YEARS, {
        "project_lifecycle_stage": "CONSTRUCTION_EXECUTION",
    }))
    cats = [r["role_category"] for r in dev["requirements"]]
    assert cats == [
        "GENERAL_CONTRACTOR", "CONSTRUCTION_PROJECT_MANAGER",
        "DEVELOPMENT_MANAGER",
    ]
    assert "Architect" not in dev["roles"]


def test_operations_stage_routes_no_development_team():
    dev = _dev_path(derive_talent_placement(YEARS, {
        "project_lifecycle_stage": "OPERATIONS_STABILIZATION",
    }))
    assert dev["mode"] == "context_routed"
    assert dev["requirements"] == [] and dev["roles"] == []


def test_context_flows_through_analyze_multiyear():
    out = analyze_multiyear(YEARS, {
        "project_lifecycle_stage": "ACQUISITION_ENTITLEMENT",
    })
    dev = _dev_path(out["talent_placement"])
    assert [r["role_category"] for r in dev["requirements"]] == [
        "ENTITLEMENT_CONSULTANT", "DEVELOPMENT_FINANCE_ANALYST",
        "DEVELOPMENT_MANAGER",
    ]
