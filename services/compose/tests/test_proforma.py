"""Pro forma ingestion (owner tap 2026-11-12): the engine must
reproduce the Graham Hill institutional workbook EXACTLY — its
cached GPR / EGI / total OpEx / NOI for all five years are the
acceptance figures, transcribed from the filed .xlsx."""

import base64
import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import proforma  # noqa: E402

WB = {
    "gpr": [3340080, 3440282.40, 3543490.87, 3649795.60, 3759289.47],
    "egi": [3288199.76, 3418877.37, 3521443.69, 3627087.00, 3735899.61],
    "noi": [1947713.77, 2030527.85, 2084983.68, 2141301.19, 2199536.23],
    "total_opex": [1310085.99, 1350349.52, 1390860.01, 1432585.81, 1475563.38],
}


def test_graham_hill_all_five_years_match_the_workbook():
    out = proforma.compute_proforma(proforma.SAMPLE_ASSUMPTIONS)
    assert out["units"] == 152
    for i, yr in enumerate(out["years"]):
        assert yr["gpr"] == pytest.approx(WB["gpr"][i], abs=0.05), f"GPR Y{i+1}"
        assert yr["egi"] == pytest.approx(WB["egi"][i], abs=0.05), f"EGI Y{i+1}"
        assert yr["expenses"]["total"] == pytest.approx(WB["total_opex"][i], abs=0.05), f"OpEx Y{i+1}"
        assert yr["noi"] == pytest.approx(WB["noi"][i], abs=0.05), f"NOI Y{i+1}"
        # the identity, every year: NOI == EGI - OpEx - Reserve
        assert yr["noi"] == pytest.approx(
            yr["egi"] - yr["expenses"]["total"] - yr["replacement_reserve"], abs=0.02
        )


def test_year1_flows_through_lease_up_not_stabilized_vacancy():
    y1 = proforma.compute_proforma(proforma.SAMPLE_ASSUMPTIONS)["years"][0]
    # lease-up vacancy (occupancy-driven), NOT 5% of GPR (167,004)
    assert y1["vacancy_loss"] == pytest.approx(-197767.89, abs=0.05)
    # credit loss is 0.75% of (GPR - vacancy), the workbook's base
    assert y1["credit_loss"] == pytest.approx(-23567.34, abs=0.05)
    assert y1["net_rental_income"] == pytest.approx(3118744.76, abs=0.05)
    # management fee is 3% of EGI, not a per-unit line
    assert y1["expenses"]["management_fee"] == pytest.approx(98645.99, abs=0.05)
    # reserve escalates per the Assumptions tab: 200/unit in Y1
    assert y1["replacement_reserve"] == 30400


def test_taxes_and_insurance_stay_out_of_opex_in_the_uze_view():
    y1 = proforma.compute_proforma(proforma.SAMPLE_ASSUMPTIONS)["years"][0]
    v = y1["uze_view"]
    assert v["taxes"] == 245480          # 1,615/unit x 152
    assert v["insurance"] == 116280      # 765/unit x 152
    assert v["opex_excl_taxes_insurance"] == pytest.approx(
        y1["expenses"]["total"] - 245480 - 116280, abs=0.02
    )
    # and the NOI is identical under both presentations
    assert v["noi"] == y1["noi"]


def test_valuation_applies_cap_rate_to_year1_noi():
    out = proforma.compute_proforma(proforma.SAMPLE_ASSUMPTIONS, cap_rate=0.055)
    v = out["valuation"]
    assert v["implied_value"] == pytest.approx(1947713.77 / 0.055, abs=1.0)
    assert v["price_per_unit"] == pytest.approx(v["implied_value"] / 152, abs=0.05)


def _mini_workbook_bytes() -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Assumptions"
    rows = [
        ("Property", "Mini Court"), ("Total Units", 10), ("Location", "Test, PA"),
        ("Annual Rent Growth Rate", 0.02), ("Initial Occupancy at Purchase", 0.9),
        ("Stabilized Vacancy Rate (Yr 2+)", 0.05), ("Credit Loss / Bad Debt", 0.01),
        ("Other Income ($/unit/yr)", 100), ("Other Income Growth Rate", 0.02),
        ("Management (% of EGI)", 0.03), ("Expense Growth Rate", 0.02),
        ("Payroll / Unit", 1000), ("Utilities / Unit", 500),
        ("Building & Mechanical / Unit", 10), ("Repairs & Maintenance / Unit", 100),
        ("Interior Improvements / Unit", 10), ("Materials & Supplies / Unit", 10),
        ("Marketing / Unit", 10), ("General & Admin / Unit", 10),
        ("Professional Fees / Unit", 10), ("Insurance / Unit", 100),
        ("Taxes / Unit", 200), ("Utility Reimbursements ($/unit/yr)", 50),
    ]
    for i, (k, v) in enumerate(rows, start=1):
        ws.cell(row=i, column=1, value=k)
        ws.cell(row=i, column=2, value=v)
    ws.cell(row=1, column=4, value="2 BR")
    ws.cell(row=1, column=5, value=10)
    ws.cell(row=1, column=6, value=1000)
    ws.cell(row=2, column=4, value="Total / Blended Avg Rent")
    for n in range(1, 6):  # reserves sit below the mix table, as filed
        ws.cell(row=14 + n, column=7, value=f"Reserve — Year {n}")
        ws.cell(row=14 + n, column=8, value=100 * n)
    wb.create_sheet("Pro Forma")
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_parser_reads_the_four_sheet_structure():
    a = proforma.parse_proforma_xlsx(_mini_workbook_bytes())
    assert a["total_units"] == 10
    assert a["unit_mix"] == [{
        "type": "2 BR", "existing": 10, "market_rent": 1000.0,
        "value_add": 0, "value_add_rent": 0.0, "delivery_month": 0,
    }]
    assert a["replacement_reserve_per_unit"] == [100, 200, 300, 400, 500]
    out = proforma.compute_proforma(a)
    y1 = out["years"][0]
    assert y1["noi"] == pytest.approx(
        y1["egi"] - y1["expenses"]["total"] - y1["replacement_reserve"], abs=0.02
    )


def test_parser_rejects_a_non_workbook():
    with pytest.raises(ValueError):
        proforma.parse_proforma_xlsx(b"this is not an xlsx")


def test_api_sample_and_file_ingest(client):
    r = client.get("/api/v1/ingest/proforma/sample")
    assert r.status_code == 200
    assert r.json()["years"][0]["noi"] == pytest.approx(1947713.77, abs=0.05)

    payload = {"file_base64": base64.b64encode(_mini_workbook_bytes()).decode()}
    r = client.post("/api/v1/ingest/proforma", json=payload)
    assert r.status_code == 200
    assert r.json()["units"] == 10

    r = client.post("/api/v1/ingest/proforma", json={"file_base64": "!!!not-base64!!!"})
    assert r.status_code == 422
    r = client.post(
        "/api/v1/ingest/proforma",
        json={"file_base64": base64.b64encode(b"junk").decode()},
    )
    assert r.status_code == 422
