"""Three-tier underwriting engine (owner unfreeze tap, 2026-11-12).

Pins: Tier 1 trends in words; Tier 2 projections whose defaults
are the historical YoY rates, with labelled overrides and shocks,
and projected NOI strictly unlevered; Tier 3 variance scoring
with the methodology flag beyond threshold; Tier 4 valuation on
verified unlevered NOI only; Tier 5 GIRA yield valuation.
"""

from __future__ import annotations

import pytest

import underwrite_engine as ue

YEARS = [
    {"period": "2024", "line_items": {
        "Rental Income": 1000000, "Repairs & Maintenance": 100000,
        "Property Taxes": 80000, "Insurance": 40000,
        "Interest Expense": 100000,
    }},
    {"period": "2025", "line_items": {
        "Rental Income": 1100000, "Repairs & Maintenance": 110000,
        "Property Taxes": 88000, "Insurance": 60000,
        "Interest Expense": 100000,
    }},
]


def test_tier1_trends_state_bucket_movements_in_words():
    out = ue.tier1_historicals(YEARS)
    statements = {t["bucket"]: t["statement"] for t in out["trends"]}
    assert "Insurance(s)" in statements
    assert "risen 50.0%" in statements["Insurance(s)"]
    # NOI per year is unlevered: 2025 = 1,100,000 - 110,000 - 88,000 - 60,000.
    assert out["periods"][-1]["noi"] == 842000


def test_tier2_projection_defaults_to_historical_growth():
    p = ue.generate_projection(YEARS, cap_rate=0.055)
    b = p["projected_buckets"]
    assert b["Revenue"] == 1210000  # +10% historical
    assert b["Insurance(s)"] == 90000  # +50% historical
    assert b["Interest Expense/Income"] == 100000  # flat
    # Unlevered: interest is NOT subtracted into projected NOI.
    assert p["projected_noi"] == 902200
    assert p["projected_levered_cash_flow"] == 802200
    assert p["projected_cap_rate"] == 0.055
    assert p["projected_implied_value"] == round(902200 / 0.055, 2)
    assert any("historical latest YoY" in a for a in p["assumptions"])


def test_tier2_overrides_and_shocks_are_labelled():
    p = ue.generate_projection(
        YEARS, cap_rate=0.055, revenue_growth=0.05, shocks={"Taxes": 20000}
    )
    assert p["projected_buckets"]["Revenue"] == 1155000
    assert p["projected_buckets"]["Taxes"] == 116800  # 96,800 grown + 20,000 shock
    assert p["projected_noi"] == 827200  # 847,200 before the +20,000 tax shock
    assert any("explicit override" in a for a in p["assumptions"])
    assert any("known shock" in a for a in p["assumptions"])


def test_tier2_rejects_unknown_bucket_and_bad_cap_rate():
    with pytest.raises(ValueError):
        ue.generate_projection(YEARS, cap_rate=0.055, shocks={"Lobby Plants": 10})
    with pytest.raises(ValueError):
        ue.generate_projection(YEARS, cap_rate=0)


def test_tier3_within_threshold_scores_and_earns_precedent_event():
    v = ue.verify_projection(902200, 880000)
    assert v["variance_pct"] == -2.46
    assert v["accuracy_score"] == 97.54
    assert v["status"] == "VERIFIED_WITHIN_THRESHOLD"
    assert v["precedent_index"]["delta"] == 1


def test_tier3_beyond_threshold_flags_the_methodology():
    v = ue.verify_projection(902200, 700000)
    assert v["status"] == "FLAGGED_VARIANCE"
    assert v["juror_flag"]["flag"] == "UNDERWRITING_METHODOLOGY_FLAGGED"
    assert "precedent_index" not in v


def test_tier4_valuation_uses_verified_unlevered_noi():
    out = ue.income_valuation(504100, 0.055)
    assert out["noi_basis"] == "verified_unlevered"
    assert out["implied_value"] == 9165454.55


def test_tier5_gira_yield_valuation():
    out = ue.gira_yield_valuation(862400, 517900, acres=500, price_per_acre=12000)
    assert out["net_agricultural_income"] == 344500
    assert out["valuation_income_basis"] == 6890000  # 344,500 x default 20
    assert out["multiple_is_default"] is True
    assert out["valuation_acreage_basis"] == 6000000


def test_projection_endpoint_round_trip(client):
    r = client.post(
        "/api/v1/underwrite/projection",
        json={"years": YEARS, "cap_rate": 0.055},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["tier2_projection"]["projected_noi"] == 902200
    assert body["tier1_historicals"]["trends"]


def test_verify_and_anrd_endpoints(client):
    r = client.post(
        "/api/v1/underwrite/verify-projection",
        json={"projected_noi": 902200, "actual_noi": 700000},
    )
    assert r.status_code == 200 and r.json()["status"] == "FLAGGED_VARIANCE"
    r = client.post(
        "/api/v1/underwrite/anrd-valuation",
        json={"projected_revenue": 862400, "input_costs": 517900},
    )
    assert r.status_code == 200 and r.json()["net_agricultural_income"] == 344500
