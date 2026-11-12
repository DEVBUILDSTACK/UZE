"""StandardChartOfAccounts — the taxonomy-safety pins.

The load-bearing rule (ratified 2026-11-10): Operating
Expenses NEVER absorb Taxes, Insurance, or Interest. These
tests fail if any variant of those families ever maps into
Operating Expenses."""
import chart_of_accounts as coa


def test_all_seven_buckets_present_in_order():
    out = coa.normalize_line_items({"Revenue": 1})
    assert list(out["buckets"].keys()) == list(coa.BUCKETS)
    assert len(coa.BUCKETS) == 7


def test_inconsistent_labels_normalize_to_the_same_bucket():
    # The multi-year T-12 problem: same line, three spellings.
    for label in ("Repairs & Maintenance", "R&M", "Maintenance Expense"):
        assert coa.bucket_for(label) == "Operating Expenses"


def test_taxes_insurance_interest_never_land_in_opex():
    families = {
        "Taxes": ["Real Estate Taxes", "Property Tax", "State Taxes"],
        "Insurance(s)": ["Insurance", "Hazard Insurance", "Crop Insurance"],
        "Interest Expense/Income": ["Interest Expense", "Mortgage Interest"],
    }
    for bucket, labels in families.items():
        for label in labels:
            assert coa.bucket_for(label) == bucket, label
            assert coa.bucket_for(label) != "Operating Expenses"


def test_unmapped_labels_are_reported_not_guessed():
    out = coa.normalize_line_items(
        {"Room Revenue": 1000, "Quantum Flux Capacitor Levy": 42}
    )
    assert out["buckets"]["Revenue"] == 1000
    assert out["unmapped"] == [
        {"label": "Quantum Flux Capacitor Levy", "amount": 42}
    ]


def test_amounts_sum_per_bucket():
    out = coa.normalize_line_items(
        {"Payroll": 100, "Utilities": 50, "Property Tax": 30}
    )
    assert out["buckets"]["Operating Expenses"] == 150
    assert out["buckets"]["Taxes"] == 30
