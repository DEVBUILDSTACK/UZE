"""Comp-set benchmarking (D5 directive, 2026-11-13).

Pins: profile normalization + vintage banding; canonical line
identity through the chart of accounts (R&M variants merge,
market rent per unit type stays separate, unmapped labels are
never guessed); per-unit median benchmarks against a comp set
matched in the subject's micro-region by type/vintage/class;
flag classification (revenue opportunity / expense opportunity
/ irregularity) with contra-revenue lines compared on loss
magnitude; ranking by annualized dollars; the value-creation
plan; the labelled no-comp-set and no-region-match states; and
the additive wiring into analyze_multiyear and the engine
endpoint. Taxes/Insurance are never benchmarked (directive
scope: revenue and operating expenses).
"""

from __future__ import annotations

import pytest

import comp_benchmark as cb
import underwrite_engine as ue
from email_gateway import analyze_multiyear

SUBJECT = {
    "property_type": "Garden Style",
    "year_built": 2005,
    "property_class": "B",
    "unit_count": 100,
    "micro_region": "baltimore-washington",
}

SUBJECT_ITEMS = {
    "Market Rent Potential": 1_200_000,
    "Parking": 10_000,
    "Vacancy Loss": -60_000,
    "Repairs & Maintenance": 150_000,
    "Property Taxes": 90_000,
    "Insurance": 30_000,
}


def _comp(name, units, items, *, year=2004, ptype="GARDEN_STYLE",
          pclass="B", region="baltimore-washington"):
    return {
        "name": name,
        "profile": {
            "property_type": ptype,
            "year_built": year,
            "property_class": pclass,
            "unit_count": units,
            "micro_region": region,
        },
        "line_items": items,
    }


COMPS = [
    _comp("Comp One", 80, {
        "Market Rent Potential": 1_040_000, "Parking": 16_000,
        "Vacancy Loss": -40_000, "R&M": 96_000,
    }),
    _comp("Comp Two", 120, {
        "Market Rent Potential": 1_560_000, "Parking": 24_000,
        "Vacancy Loss": -60_000, "Repairs and Maintenance": 144_000,
    }),
]


# ------------------------------------------------------------------
# Profiles and vintage bands
# ------------------------------------------------------------------


def test_vintage_bands_are_the_documented_ones():
    assert cb.vintage_band(1979) == "PRE_1980"
    assert cb.vintage_band(1980) == "VINTAGE_1980_1999"
    assert cb.vintage_band(1999) == "VINTAGE_1980_1999"
    assert cb.vintage_band(2000) == "VINTAGE_2000_2009"
    assert cb.vintage_band(2009) == "VINTAGE_2000_2009"
    assert cb.vintage_band(2010) == "VINTAGE_2010_2019"
    assert cb.vintage_band(2019) == "VINTAGE_2010_2019"
    assert cb.vintage_band(2020) == "VINTAGE_2020_PLUS"
    assert cb.vintage_band(None) is None
    assert cb.vintage_band("not a year") is None


def test_profile_normalizes_display_spellings():
    p = cb.normalize_profile(SUBJECT)
    assert p["property_type"] == "GARDEN_STYLE"
    assert p["property_class"] == "B"
    assert p["vintage_band"] == "VINTAGE_2000_2009"
    assert p["unit_count"] == 100
    assert cb.normalize_property_type("low-rise") == "LOW_RISE"
    assert cb.normalize_property_type("Townhouse Community") == "TOWNHOUSE_COMMUNITY"
    assert cb.normalize_property_type("castle") is None
    assert cb.normalize_property_class("class a") == "A"
    assert cb.normalize_property_class("D") is None


# ------------------------------------------------------------------
# Canonical lines
# ------------------------------------------------------------------


def test_canonical_lines_merge_label_variants():
    assert cb.canonical_line("R&M") == ("Repairs & Maintenance", "Operating Expenses")
    assert cb.canonical_line("Repairs & Maintenance")[0] == "Repairs & Maintenance"
    assert cb.canonical_line("Maintenance Expense")[0] == "Repairs & Maintenance"
    assert cb.canonical_line("Market Rent Potential") == ("Market Rent", "Revenue")
    assert cb.canonical_line("Parking") == ("Parking Income", "Revenue")
    assert cb.canonical_line("Vacancy Loss") == ("Vacancy Loss", "Revenue")
    assert cb.canonical_line("Bad Debt") == ("Bad Debt", "Revenue")


def test_market_rent_per_unit_type_stays_separate():
    name, bucket = cb.canonical_line("Market Rent — 1BR")
    assert name == "Market Rent (1BR)"
    assert bucket == "Revenue"
    assert cb.canonical_line("Market Rent — 2BR")[0] == "Market Rent (2BR)"


def test_unmapped_label_is_never_guessed():
    assert cb.canonical_line("Zebra Grooming Retainer") is None


# ------------------------------------------------------------------
# Benchmarking, flags, ranking
# ------------------------------------------------------------------


def test_per_unit_median_benchmarks_and_flag_classification():
    out = cb.analyze_comp_set(SUBJECT, SUBJECT_ITEMS, COMPS)
    assert out["status"] == "OK"
    assert out["match"]["tier"] == "A"
    lines = {row["line"]: row for row in out["lines"]}
    # Per-unit medians across two comps of different sizes:
    # market rent (13,000 and 13,000) -> 13,000; subject 12,000.
    assert lines["Market Rent"]["benchmark_per_unit"] == 13000
    assert lines["Market Rent"]["subject_per_unit"] == 12000
    assert lines["Market Rent"]["comp_count"] == 2
    # R&M variants from both spellings merge into one line.
    assert lines["Repairs & Maintenance"]["benchmark_per_unit"] == 1200

    findings = {f["line"]: f for f in out["findings"]}
    # Market rent is -7.7% vs benchmark: inside the 10% threshold.
    assert "Market Rent" not in findings
    rm = findings["Repairs & Maintenance"]
    assert rm["classification"] == "expense_opportunity"
    assert rm["subject_per_unit"] == 1500
    assert rm["benchmark_per_unit"] == 1200
    assert rm["variance_pct"] == 25.0
    assert rm["annualized_impact_usd"] == 30000  # 300/unit x 100 units
    assert rm["evidence"]["comp_count"] == 2
    assert "vintage band" in rm["evidence"]["match_basis"]
    assert rm["note"] == "for further analysis"

    parking = findings["Parking Income"]
    assert parking["classification"] == "revenue_opportunity"
    assert parking["annualized_impact_usd"] == 10000


def test_contra_revenue_compares_on_loss_magnitude():
    out = cb.analyze_comp_set(SUBJECT, SUBJECT_ITEMS, COMPS)
    vacancy = {f["line"]: f for f in out["findings"]}["Vacancy Loss"]
    # Subject loses 600/unit vs a 500/unit benchmark loss.
    assert vacancy["compared_on"] == "loss magnitude per unit"
    assert vacancy["variance_pct"] == 20.0
    assert vacancy["classification"] == "revenue_opportunity"


def test_findings_rank_by_annualized_dollars():
    out = cb.analyze_comp_set(SUBJECT, SUBJECT_ITEMS, COMPS)
    amounts = [f["annualized_impact_usd"] for f in out["findings"]]
    assert amounts == sorted(amounts, reverse=True)
    assert out["findings"][0]["line"] == "Repairs & Maintenance"


def test_favorable_divergence_is_an_irregularity_not_a_win():
    items = dict(SUBJECT_ITEMS)
    items["Repairs & Maintenance"] = 50_000  # 500/unit vs 1,200 benchmark
    out = cb.analyze_comp_set(SUBJECT, items, COMPS)
    rm = {f["line"]: f for f in out["findings"]}["Repairs & Maintenance"]
    assert rm["classification"] == "irregularity"
    plan = {p["line"]: p for p in out["value_creation_plan"]}
    assert "deferred maintenance" in plan["Repairs & Maintenance"]["action"]


def test_line_missing_from_subject_is_still_benchmarked():
    comps = [_comp("Fees Comp", 50, {"Resid Pet Fee": 5_000})]
    out = cb.analyze_comp_set(SUBJECT, {"Rental Income": 900_000}, comps)
    pet = {f["line"]: f for f in out["findings"]}["Resid Pet Fee"]
    assert pet["in_subject"] is False
    assert pet["subject_per_unit"] == 0
    assert pet["benchmark_per_unit"] == 100
    assert pet["classification"] == "revenue_opportunity"


def test_threshold_is_a_per_call_policy_knob():
    out = cb.analyze_comp_set(SUBJECT, SUBJECT_ITEMS, COMPS, threshold_pct=30.0)
    lines = {f["line"] for f in out["findings"]}
    assert "Repairs & Maintenance" not in lines  # +25% inside a 30% threshold
    assert "Parking Income" in lines  # -50% still flagged


def test_taxes_and_insurance_are_never_benchmarked():
    out = cb.analyze_comp_set(SUBJECT, SUBJECT_ITEMS, COMPS)
    lines = {row["line"] for row in out["lines"]}
    assert all(
        row["bucket"] in ("Revenue", "Operating Expenses") for row in out["lines"]
    )
    assert "Property Taxes" not in str(lines)


def test_unmapped_lines_are_surfaced_not_dropped():
    items = dict(SUBJECT_ITEMS)
    items["Zebra Grooming Retainer"] = 1_000
    out = cb.analyze_comp_set(SUBJECT, items, COMPS)
    assert out["unmapped"]["subject"] == [
        {"label": "Zebra Grooming Retainer", "amount": 1000}
    ]


# ------------------------------------------------------------------
# Matching discipline and the honesty states
# ------------------------------------------------------------------


def test_highest_available_tier_wins_and_lower_tiers_are_named():
    region_only = _comp("Region Only", 60, {"Parking": 12_000},
                        year=1990, ptype="HIGH_RISE", pclass="A")
    out = cb.analyze_comp_set(SUBJECT, SUBJECT_ITEMS, COMPS + [region_only])
    assert out["match"]["tier"] == "A"
    assert out["match"]["lower_tier_region_comps_not_used"] == ["Region Only"]
    # Benchmark unchanged: the tier-C comp did not enter the median.
    lines = {row["line"]: row for row in out["lines"]}
    assert lines["Parking Income"]["comp_count"] == 2


def test_no_comp_set_is_a_labelled_state_not_a_benchmark():
    for comps in (None, []):
        out = cb.analyze_comp_set(SUBJECT, SUBJECT_ITEMS, comps)
        assert out["status"] == "NO_COMP_SET_SUPPLIED"
        assert out["findings"] == []
        assert out["value_creation_plan"] == []
        assert "No comparable set was supplied" in out["note"]


def test_cross_region_comps_never_substitute():
    far = [_comp("Far Away", 100, {"Parking": 20_000}, region="miami")]
    out = cb.analyze_comp_set(SUBJECT, SUBJECT_ITEMS, far)
    assert out["status"] == "NO_REGION_MATCHES"
    assert out["findings"] == []
    assert "micro-region" in out["excluded_comps"][0]["reason"]


def test_subject_profile_and_units_are_required():
    out = cb.analyze_comp_set(None, SUBJECT_ITEMS, COMPS)
    assert out["status"] == "SUBJECT_PROFILE_REQUIRED"
    with pytest.raises(ValueError, match="unit_count"):
        cb.analyze_comp_set({**SUBJECT, "unit_count": None}, SUBJECT_ITEMS, COMPS)


# ------------------------------------------------------------------
# The value-creation plan
# ------------------------------------------------------------------


def test_value_creation_plan_shape_and_evidence():
    out = cb.analyze_comp_set(SUBJECT, SUBJECT_ITEMS, COMPS)
    assert out["value_creation_plan"]
    for entry in out["value_creation_plan"]:
        assert entry["annualized_value_at_stake_usd"] > 0
        assert "comp-set median" in entry["evidence_basis"]
        assert entry["action"]
        assert entry["note"] == "for further analysis"
    plan_lines = [p["line"] for p in out["value_creation_plan"]]
    finding_lines = [f["line"] for f in out["findings"]]
    assert plan_lines == finding_lines  # same ranking, one entry per finding


# ------------------------------------------------------------------
# Wiring: analyze_multiyear + the engine endpoint
# ------------------------------------------------------------------

YEARS = [
    {"period": "2024", "line_items": {
        "Rental Income": 900_000, "Repairs & Maintenance": 120_000,
    }},
    {"period": "2025", "line_items": SUBJECT_ITEMS},
]


def test_analyze_multiyear_without_comp_inputs_is_unchanged():
    out = analyze_multiyear(YEARS)
    assert "comp_benchmark" not in out
    assert out["periods"][-1]["noi"] == round(
        1_200_000 + 10_000 - 60_000 - 150_000 - 90_000 - 30_000, 2
    )


def test_analyze_multiyear_gains_comp_section_when_inputs_supplied():
    out = analyze_multiyear(YEARS, subject_profile=SUBJECT, comps=COMPS)
    section = out["comp_benchmark"]
    assert section["status"] == "OK"
    # The LATEST period (2025) is the benchmarked one.
    assert section["subject"]["unit_count"] == 100
    assert section["findings"][0]["line"] == "Repairs & Maintenance"


def test_analyze_multiyear_profile_without_comps_labels_the_state():
    out = analyze_multiyear(YEARS, subject_profile=SUBJECT)
    assert out["comp_benchmark"]["status"] == "NO_COMP_SET_SUPPLIED"


def test_comp_benchmark_endpoint_accepts_years_or_line_items():
    by_items = ue.comp_benchmark_endpoint(ue.CompBenchmarkIn(
        subject_profile=SUBJECT, line_items=SUBJECT_ITEMS, comps=COMPS,
    ))
    by_years = ue.comp_benchmark_endpoint(ue.CompBenchmarkIn(
        subject_profile=SUBJECT, years=YEARS, comps=COMPS,
    ))
    assert by_items["status"] == by_years["status"] == "OK"
    assert by_items["findings"] == by_years["findings"]


def test_comp_benchmark_endpoint_requires_subject_financials():
    with pytest.raises(Exception):
        ue.comp_benchmark_endpoint(ue.CompBenchmarkIn(
            subject_profile=SUBJECT, comps=COMPS,
        ))
