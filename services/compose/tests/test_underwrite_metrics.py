"""Institutional underwrite metrics (2026-11-11 build):
price/unit + price/sqft in the valuation flow, multi-year
normalization with NOI growth and fluctuation flags."""
import json
import pathlib

import email_gateway


def test_valuation_flow_carries_price_per_unit_and_sqft():
    data = email_gateway.extract_mock_data(
        "aGVsbG8=", "SURA", "acquisition_due_diligence"
    )
    # Fixture: asking 9,400,000 / 128 units / 96,400 sqft.
    assert data["pricePerUnit"] == 73437.50
    assert data["pricePerSqFt"] == 97.51
    assert data["impliedValue"] == round(504100 / 0.055, 2)
    assert data["noiGrowthRate"] == 0.0814 or abs(data["noiGrowthRate"] - 0.0814) < 0.001
    assert "per unit" in data["assessment"]


def test_non_valuation_flow_carries_no_price_metrics():
    data = email_gateway.extract_mock_data("aGVsbG8=", "SURA", "standard")
    assert "pricePerUnit" not in data
    assert "askingPrice" not in data


def test_multiyear_normalization_growth_and_flags(client):
    fixture = json.loads(
        (
            pathlib.Path(__file__).parent.parent
            / "scripts"
            / "fixtures"
            / "multiyear-t12-sura.json"
        ).read_text()
    )
    resp = client.post("/api/v1/ingest/multiyear", json={"years": fixture["years"]})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    periods = body["periods"]
    assert [p["period"] for p in periods] == ["2024", "2025", "2026"]
    # Every label in the fixture maps — inconsistent spellings
    # across years are the whole point of the layer.
    assert all(p["unmapped"] == [] for p in periods)
    assert periods[0]["noi"] == 612100
    assert periods[-1]["noi"] == 634200
    assert body["noi_growth_rate"] == round((634200 - 612100) / 612100, 4)
    # The 2026 insurance spike (+44%) must be flagged; taxes
    # (+6%/yr) must not be.
    flagged = {(f["bucket"], f["to_period"]) for f in body["fluctuation_flags"]}
    assert ("Insurance(s)", "2026") in flagged
    assert not any(b == "Taxes" for b, _ in flagged)
    # And the taxonomy guard inside the analysis: the 2026 tax
    # line sits in Taxes, never inside Operating Expenses.
    buckets_2026 = periods[-1]["buckets"]
    assert buckets_2026["Taxes"] == 148200
    assert buckets_2026["Operating Expenses"] == 899400


def test_sura_assessment_carries_the_analysis_directive():
    import agents

    assert "Price per Unit" in agents.SURA_ANALYSIS_DIRECTIVE
    assert "never absorb taxes, insurance, or" in agents.SURA_ANALYSIS_DIRECTIVE
    assert "15%" in agents.SURA_ANALYSIS_DIRECTIVE
