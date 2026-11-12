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


def test_blind_hardening_messy_workbook_reports_and_parses():
    """An unseen, messy file: numbers as "$1,615" strings, an
    extra unrecognized numeric label, an optional field absent.
    The parser must parse what it can, default what is optional,
    and REPORT both — not crash."""
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Assumptions"
    rows = [
        ("Property", "Messy Arms"), ("Total Units", "10"), ("Location", "Test, PA"),
        ("Annual Rent Growth Rate", "2%"), ("Initial Occupancy at Purchase", 0.9),
        ("Stabilized Vacancy Rate (Yr 2+)", 0.05), ("Credit Loss / Bad Debt", 0.01),
        ("Other Income ($/unit/yr)", 100), ("Other Income Growth Rate", 0.02),
        ("Management (% of EGI)", 0.03), ("Expense Growth Rate", 0.02),
        ("Payroll / Unit", "$1,000"), ("Utilities / Unit", 500),
        ("Building & Mechanical / Unit", 10), ("Repairs & Maintenance / Unit", 100),
        ("Interior Improvements / Unit", 10), ("Materials & Supplies / Unit", 10),
        ("Marketing / Unit", 10), ("General & Admin / Unit", 10),
        ("Professional Fees / Unit", 10), ("Insurance / Unit", 100),
        ("Taxes / Unit", "$200"), ("Syndication Fee / Unit", 25),
        # Utility Reimbursements deliberately absent -> defaulted
    ]
    for i, (k, v) in enumerate(rows, start=1):
        ws.cell(row=i, column=1, value=k)
        ws.cell(row=i, column=2, value=v)
    ws.cell(row=1, column=4, value="2 BR")
    ws.cell(row=1, column=5, value=10)
    ws.cell(row=1, column=6, value=1000)
    ws.cell(row=2, column=4, value="Total / Blended Avg Rent")
    for n in range(1, 6):
        ws.cell(row=14 + n, column=7, value=f"Reserve — Year {n}")
        ws.cell(row=14 + n, column=8, value=100 * n)
    wb.create_sheet("Pro Forma")
    buf = io.BytesIO()
    wb.save(buf)

    a, report = proforma.parse_with_report(buf.getvalue())
    assert a["total_units"] == 10
    assert a["taxes_per_unit"] == 200          # "$200" coerced
    assert a["payroll_per_unit"] == 1000       # "$1,000" coerced
    assert a["rent_growth"] == 0.02            # "2%" coerced
    assert "Utility Reimbursements ($/unit/yr)" in report["defaulted"]
    assert "syndication fee / unit" in report["unmapped_labels"]
    out = proforma.compute_proforma(a)
    assert out["years"][0]["noi"] > 0


def test_blind_missing_required_lists_everything_missing():
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Assumptions"
    ws.cell(row=1, column=1, value="Total Units")
    ws.cell(row=1, column=2, value=10)
    ws.cell(row=1, column=4, value="2 BR")
    ws.cell(row=1, column=5, value=10)
    ws.cell(row=1, column=6, value=1000)
    wb.create_sheet("Pro Forma")
    buf = io.BytesIO()
    wb.save(buf)
    with pytest.raises(ValueError) as e:
        proforma.parse_with_report(buf.getvalue())
    msg = str(e.value)
    # one error naming several missing labels, not first-failure only
    assert "Credit Loss / Bad Debt" in msg and "Taxes / Unit" in msg


def test_gateway_routes_xlsx_attachments_to_the_parser(client):
    payload = {
        "subject": "HiCRE proforma for review",
        "sender": "analyst@example.com",
        "attachment_base64": base64.b64encode(_mini_workbook_bytes()).decode(),
    }
    r = client.post("/api/v1/ingest/email", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["routedTo"] == "UZE Underwrite pro forma parser"
    assert body["units"] == 10
    assert len(body["years"]) == 5
    assert "parse_report" in body

    # a non-workbook attachment keeps the established mock flow
    payload["attachment_base64"] = base64.b64encode(b"%PDF-1.4 fake").decode()
    payload["subject"] = "HiCRE T-12 for the Brickell hotel"
    r = client.post("/api/v1/ingest/email", json=payload)
    assert r.status_code == 200
    assert r.json()["agent"] == "SURA"


# ------------------------------------------------ universal formats
# The same mini assumptions laid out four ways must produce the
# IDENTICAL computed output — that is the universal-parser proof.

_MINI_LABELS = [
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


def _mini_grid() -> list[list]:
    grid = [[""] * 9 for _ in range(24)]
    for i, (k, v) in enumerate(_MINI_LABELS):
        grid[i][0], grid[i][1] = k, v
    grid[0][3], grid[0][4], grid[0][5] = "2 BR", 10, 1000
    grid[1][3] = "Total / Blended Avg Rent"
    for n in range(1, 6):
        grid[13 + n][6] = f"Reserve — Year {n}"
        grid[13 + n][7] = 100 * n
    return grid


def _mini_xls_bytes() -> bytes:
    import xlwt

    wb = xlwt.Workbook()
    ws = wb.add_sheet("Assumptions")
    for r, row in enumerate(_mini_grid()):
        for c, v in enumerate(row):
            if v != "":
                ws.write(r, c, v)
    wb.add_sheet("Pro Forma")
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _mini_csv_bytes() -> bytes:
    import csv as _csv

    buf = io.StringIO()
    w = _csv.writer(buf)
    for row in _mini_grid():
        w.writerow(row)
    return buf.getvalue().encode()


def test_all_formats_produce_identical_math():
    outs = {}
    for name, blob in (
        ("xlsx", _mini_workbook_bytes()),
        ("xls", _mini_xls_bytes()),
        ("csv", _mini_csv_bytes()),
    ):
        a, _report, fmt = proforma.parse_any_with_report(blob)
        assert fmt == name
        outs[name] = proforma.compute_proforma(a)
    assert outs["xlsx"] == outs["xls"] == outs["csv"]


def test_detect_format():
    assert proforma.detect_format(_mini_workbook_bytes()) == "xlsx"
    assert proforma.detect_format(_mini_xls_bytes()) == "xls"
    assert proforma.detect_format(_mini_csv_bytes()) == "csv"
    assert proforma.detect_format(b"%PDF-1.4 fake") is None
    assert proforma.detect_format(b"plain text with no labels") is None


def test_google_sheets_url_rules():
    url = proforma.google_sheet_export_url(
        "https://docs.google.com/spreadsheets/d/AbC-123_xYz/edit#gid=0"
    )
    assert url == "https://docs.google.com/spreadsheets/d/AbC-123_xYz/export?format=xlsx"
    for bad in (
        "http://docs.google.com/spreadsheets/d/AbC-123_xYz",       # not https
        "https://evil.example.com/spreadsheets/d/AbC-123_xYz",     # not Google
        "https://docs.google.com/document/d/AbC-123_xYz",          # not a sheet
        "https://docs.google.com/spreadsheets/d/",                 # no id
    ):
        with pytest.raises(ValueError):
            proforma.google_sheet_export_url(bad)


def test_google_sheets_fetch_paths(client, monkeypatch):
    # link-shared sheet: the export returns real xlsx bytes
    monkeypatch.setattr(
        proforma, "_fetch_url_bytes",
        lambda url: (_mini_workbook_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    )
    r = client.post(
        "/api/v1/ingest/proforma",
        json={"source_url": "https://docs.google.com/spreadsheets/d/AbC-123_xYz/edit"},
    )
    assert r.status_code == 200
    assert r.json()["input_format"] == "xlsx"
    assert r.json()["units"] == 10

    # private sheet: Google answers with an HTML login page
    monkeypatch.setattr(
        proforma, "_fetch_url_bytes",
        lambda url: (b"<!doctype html><title>Sign in</title>", "text/html"),
    )
    r = client.post(
        "/api/v1/ingest/proforma",
        json={"source_url": "https://docs.google.com/spreadsheets/d/AbC-123_xYz/edit"},
    )
    assert r.status_code == 422
    assert "anyone with the link" in r.json()["detail"]

    # a non-Google URL never reaches the fetcher
    r = client.post(
        "/api/v1/ingest/proforma",
        json={"source_url": "https://evil.example.com/spreadsheets/d/AbC"},
    )
    assert r.status_code == 422


def test_gateway_routes_xls_and_csv_too(client):
    for blob in (_mini_xls_bytes(), _mini_csv_bytes()):
        r = client.post(
            "/api/v1/ingest/email",
            json={
                "subject": "HiCRE proforma attached",
                "sender": "analyst@example.com",
                "attachment_base64": base64.b64encode(blob).decode(),
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["routedTo"] == "UZE Underwrite pro forma parser"
        assert body["units"] == 10
        assert body["input_format"] in ("xls", "csv")
