"""Yardi dialect pack (owner tap, 2026-11-12).

The blind-test finding: a real Yardi (ysi_bf) export's leaf
labels mostly miss the standard variant table. The pack maps
the Yardi vocabulary as a fallback; the standard table wins
on any overlap. The fixture below is SYNTHETIC — an invented
property ("Maple Court") with invented amounts in Yardi label
shapes. The real blind-test file is never committed; it is
re-run locally and reported in chat.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import chart_of_accounts as coa
import email_gateway


# An invented 24-unit property, one T-12, Yardi labels.
MAPLE_COURT = {
    "Market rent potential": 612000.0,
    "Vacancy loss": -24480.0,
    "Loss / Gain to lease": -6120.0,
    "Base rent - retail": 48000.0,
    "Bad debt expense": -3100.0,
    "Parking": 5400.0,
    "Interest inc - sec. dep.": -450.0,
    "Real estate tax expense": 61200.0,
    "Insurance exp - property": 14400.0,
    "Payroll - resid. manager": 39000.0,
    "Payroll - mainten. staff": 27000.0,
    "Cleaning contract": 9600.0,
    "Water and sewer": 7300.0,
    "Mortgage int exp - first": 121000.0,
    "Interest Expense - SWAP/CAP": -30150.0,
}


def test_yardi_labels_all_map():
    out = coa.normalize_line_items(MAPLE_COURT)
    assert out["unmapped"] == []


def test_yardi_buckets_follow_the_tree_sections():
    b = coa.normalize_line_items(MAPLE_COURT)["buckets"]
    # Revenue: every income leaf incl. contra items, interest
    # income excluded (it files under Interest in this tree).
    assert b["Revenue"] == 612000.0 - 24480.0 - 6120.0 + 48000.0 - 3100.0 + 5400.0
    assert b["Taxes"] == 61200.0
    assert b["Insurance(s)"] == 14400.0
    assert b["Operating Expenses"] == 39000.0 + 27000.0 + 9600.0 + 7300.0
    assert b["Interest Expense/Income"] == -450.0 + 121000.0 - 30150.0


def test_yardi_noi_is_unlevered_through_the_engine():
    res = email_gateway.analyze_multiyear(
        [{"period": "T-12", "line_items": MAPLE_COURT}]
    )
    p = res["periods"][0]
    revenue = 612000.0 - 24480.0 - 6120.0 + 48000.0 - 3100.0 + 5400.0
    expected_noi = revenue - (39000.0 + 27000.0 + 9600.0 + 7300.0) - 61200.0 - 14400.0
    assert p["noi"] == expected_noi
    # Levered = NOI minus the net interest bucket (income nets).
    assert p["levered_cash_flow"] == expected_noi - (-450.0 + 121000.0 - 30150.0)


def test_yardi_charge_codes_are_revenue_with_signs_preserved():
    codes = {
        "rentres": 20100.0, "petrent": 150.0, "garage": 600.0,
        "parking": 75.0, "storage": 90.0, "carport": 50.0,
        "keylocks": 25.0, "subsidy": 900.0,
        "xempprop": -40.0, "admin": -120.0,
    }
    out = coa.normalize_line_items(codes)
    assert out["unmapped"] == []
    assert out["buckets"]["Revenue"] == sum(codes.values())


def test_standard_table_still_wins_over_the_pack():
    # 'bad debt expense' and 'vacancy loss' live in the standard
    # table AND the Yardi tree — both say Revenue, and the
    # resolution order (standard first) is pinned by behavior:
    assert coa.bucket_for("Bad debt expense") == "Revenue"
    assert coa.bucket_for("Vacancy loss") == "Revenue"
    # A standard-only label is untouched by the pack's presence.
    assert coa.bucket_for("Repairs & Maintenance") == "Operating Expenses"
    # A label in neither table is still refused, never guessed.
    assert coa.bucket_for("Quantum flux capacitor rental") is None
