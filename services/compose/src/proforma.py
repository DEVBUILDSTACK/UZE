"""Institutional multifamily pro forma ingestion (the Graham Hill
format) — owner's unfreeze tap, 2026-11-12.

Parses the 4-sheet institutional pro forma structure (Comps /
Assumptions / Lease-Up Schedule / Pro Forma) and replicates its
math exactly:

    GPR -> vacancy -> credit loss -> Net Rental Income
        -> + other income -> EGI -> operating expenses
        -> replacement reserve -> NOI, Years 1-5.

CONVENTIONS — read before touching:
- The workbook's own presentation sums Insurance and Real Estate
  Taxes inside its "Total Operating Expenses" row. This module
  preserves every labelled line separately (the UZE taxonomy:
  Taxes and Insurance(s) are their own buckets, never inside
  OpEx) and reports BOTH views: `expenses.total` (the workbook's
  presentation, so its NOI reconciles to the cent) and
  `uze_view.opex_excl_taxes_insurance`.
- Replacement Reserve follows the WORKBOOK's convention: its own
  line, subtracted above NOI. That is the file's institutional
  convention, kept visible as a separate field rather than
  folded into any bucket.
- The workbook grows Real Estate Taxes at its Expense Growth
  Rate (its Pro Forma formulas reference that rate; the separate
  Tax Growth Rate cell is present but unreferenced there).
  Replicated as filed.
- Year 1 runs through the monthly lease-up (initial occupancy,
  monthly new leases, occupancy-capped); Years 2+ are stabilized
  (vacancy % on GPR, growth rates per the Assumptions tab).
- The workbook carries no cap rate. Valuation applies a cap-rate
  PARAMETER (default 5.5%, the SURA fixture rate, labelled mock)
  to Year 1 NOI.

REAL: the parser (openpyxl) and every formula. The filed sample
below is the Graham Hill workbook's extracted assumptions,
verbatim values, so the engine's output can be checked against
the workbook's own cached results (done in test_proforma.py).
"""

from __future__ import annotations

import base64
import io
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["proforma"])

DEFAULT_CAP_RATE = 0.055  # mock default — the SURA fixture rate

# Per-unit expense lines: (assumptions key, workbook label, output key)
_EXPENSE_LINES = [
    ("payroll_per_unit", "Payroll / Unit", "payroll"),
    ("utilities_per_unit", "Utilities / Unit", "utilities"),
    ("mechanical_per_unit", "Building & Mechanical / Unit", "building_mechanical"),
    ("repairs_per_unit", "Repairs & Maintenance / Unit", "repairs_maintenance"),
    ("interior_per_unit", "Interior Improvements / Unit", "interior_improvements"),
    ("materials_per_unit", "Materials & Supplies / Unit", "materials_supplies"),
    ("marketing_per_unit", "Marketing / Unit", "marketing"),
    ("general_admin_per_unit", "General & Admin / Unit", "general_admin"),
    ("professional_per_unit", "Professional Fees / Unit", "professional_fees"),
    ("insurance_per_unit", "Insurance / Unit", "insurance"),
    ("taxes_per_unit", "Taxes / Unit", "real_estate_taxes"),
]

# The Graham Hill workbook's assumptions, extracted 2026-11-12 by
# parse_proforma_xlsx from the file James filed. Values verbatim.
SAMPLE_ASSUMPTIONS: dict[str, Any] = {
    "property": "Graham Hill",
    "location": "Mechanicsburg, PA",
    "total_units": 152,
    "unit_mix": [
        {"type": "1BR / 1 BA", "existing": 18, "market_rent": 1495, "value_add": 0, "value_add_rent": 0, "delivery_month": 0},
        {"type": "1 BR / 1.5 BA", "existing": 4, "market_rent": 1695, "value_add": 0, "value_add_rent": 0, "delivery_month": 0},
        {"type": "1 BR / 2 BA", "existing": 33, "market_rent": 1795, "value_add": 0, "value_add_rent": 0, "delivery_month": 0},
        {"type": "2 BR / 2 BA", "existing": 81, "market_rent": 1895, "value_add": 0, "value_add_rent": 0, "delivery_month": 0},
        {"type": "3 BR / 2 BA", "existing": 16, "market_rent": 1995, "value_add": 0, "value_add_rent": 0, "delivery_month": 0},
    ],
    "rent_growth": 0.03,
    "initial_occupancy": 0.9013,
    "stabilized_vacancy": 0.05,
    "commercial_income": 0,
    "commercial_vacancy": 0,
    "utility_reimbursement_per_unit": 260,
    "credit_loss_rate": 0.0075,
    "fee_income_per_unit": 0,
    "other_income_per_unit": 925,
    "other_income_growth": 0.03,
    "management_fee_pct": 0.03,
    "expense_growth": 0.03,
    "payroll_per_unit": 2200,
    "utilities_per_unit": 1035,
    "mechanical_per_unit": 35,
    "repairs_per_unit": 1360,
    "interior_per_unit": 250,
    "materials_per_unit": 100,
    "marketing_per_unit": 240,
    "general_admin_per_unit": 340,
    "professional_per_unit": 30,
    "insurance_per_unit": 765,
    "taxes_per_unit": 1615,
    "lease_up_new_leases": [1, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0],
    "replacement_reserve_per_unit": [200, 250, 300, 350, 400],
}


def _r2(x: float) -> float:
    return round(x + 0.0, 2)


def compute_proforma(a: dict[str, Any], cap_rate: float = DEFAULT_CAP_RATE) -> dict[str, Any]:
    """Replicate the workbook's Pro Forma sheet, Years 1-5."""
    if cap_rate <= 0:
        raise ValueError("cap_rate must be positive")
    units = int(a["total_units"])
    mix = a["unit_mix"]
    monthly_base = sum(
        (m["existing"] - m["value_add"]) * m["market_rent"]
        + m["value_add"] * m["value_add_rent"]
        for m in mix
    )
    total_existing = sum(m["existing"] for m in mix)

    def monthly_gpr(month: int) -> float:
        base = sum((m["existing"] - m["value_add"]) * m["market_rent"] for m in mix)
        delivered = sum(
            m["value_add"] * m["value_add_rent"]
            for m in mix if m["delivery_month"] <= month
        )
        return base + delivered

    def available(month: int) -> int:
        offline = sum(m["value_add"] for m in mix if m["delivery_month"] > month)
        return total_existing - offline

    fee_other_unit = float(a.get("fee_income_per_unit") or 0) + float(a.get("other_income_per_unit") or 0)
    stab_vac = float(a["stabilized_vacancy"])
    credit_rate = float(a["credit_loss_rate"])

    # ---- Year 1: monthly lease-up (workbook's Lease-Up Schedule:
    # month 1 occupied = ROUND(units x initial occupancy) + month-1
    # leases; later months add their leases; capped at available) ----
    leases = list(a.get("lease_up_new_leases") or [0] * 12)
    leases = (leases + [0] * 12)[:12]
    occupied = round(units * float(a["initial_occupancy"]))
    gpr1 = vac1 = fee1 = 0.0
    occ_months: list[int] = []
    for month in range(1, 13):
        avail = available(month)
        if month == 1:
            occupied = min(occupied + leases[0], avail)
        else:
            occupied = min(occ_months[-1] + leases[month - 1], avail)
        occ_months.append(occupied)
        g = monthly_gpr(month)
        gpr1 += g
        vac1 += -g * (1 - occupied / avail) if avail else 0.0
        fee1 += occupied * fee_other_unit / 12
    credit1 = -(gpr1 + vac1) * credit_rate
    nri1 = gpr1 + vac1 + credit1
    util1 = (sum(occ_months) / 12) * float(a["utility_reimbursement_per_unit"])
    comm1 = float(a.get("commercial_income") or 0)
    comm_vac1 = -comm1 * float(a.get("commercial_vacancy") or 0)
    other1 = comm1 + comm_vac1 + fee1 + util1
    egi1 = nri1 + other1

    years: list[dict[str, Any]] = [{
        "year": 1, "gpr": gpr1, "vacancy_loss": vac1, "credit_loss": credit1,
        "net_rental_income": nri1, "commercial_income": comm1,
        "commercial_vacancy": comm_vac1, "fee_other_income": fee1,
        "utility_reimbursements": util1, "total_other_income": other1, "egi": egi1,
    }]

    # ---- Years 2-5: stabilized ----
    gpr = monthly_base * 12 * (1 + float(a["rent_growth"]))
    fee = fee_other_unit * units * (1 - stab_vac) * (1 + float(a["other_income_growth"]))
    util = float(a["utility_reimbursement_per_unit"]) * units * (1 - stab_vac)
    comm = comm1
    for y in range(2, 6):
        if y > 2:
            gpr = gpr * (1 + float(a["rent_growth"]))
            fee = fee * (1 + float(a["other_income_growth"]))
            util = util * (1 + float(a["other_income_growth"]))
        vac = -gpr * stab_vac
        credit = -(gpr + vac) * credit_rate
        nri = gpr + vac + credit
        comm_vac = -comm * float(a.get("commercial_vacancy") or 0)
        other = comm + comm_vac + fee + util
        years.append({
            "year": y, "gpr": gpr, "vacancy_loss": vac, "credit_loss": credit,
            "net_rental_income": nri, "commercial_income": comm,
            "commercial_vacancy": comm_vac, "fee_other_income": fee,
            "utility_reimbursements": util, "total_other_income": other,
            "egi": nri + other,
        })

    # ---- Expenses, reserve, NOI (all years) ----
    growth = 1 + float(a["expense_growth"])
    reserves = list(a.get("replacement_reserve_per_unit") or [])
    for idx, yr in enumerate(years):
        exp: dict[str, float] = {}
        for key, _label, out_key in _EXPENSE_LINES:
            base = float(a.get(key) or 0) * units
            exp[out_key] = base * (growth ** idx)
        exp["management_fee"] = float(a["management_fee_pct"]) * yr["egi"]
        total = sum(exp.values())
        reserve = (float(reserves[idx]) * units) if idx < len(reserves) else 0.0
        yr["expenses"] = {**exp, "total": total}
        yr["replacement_reserve"] = reserve
        yr["noi"] = yr["egi"] - total - reserve
        yr["uze_view"] = {
            "egi": yr["egi"],
            "opex_excl_taxes_insurance": total - exp["real_estate_taxes"] - exp["insurance"],
            "taxes": exp["real_estate_taxes"],
            "insurance": exp["insurance"],
            "replacement_reserve": reserve,
            "noi": yr["noi"],
        }

    def clean(yr: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in yr.items():
            if isinstance(v, dict):
                out[k] = {kk: _r2(vv) for kk, vv in v.items()}
            elif isinstance(v, float):
                out[k] = _r2(v)
            else:
                out[k] = v
        return out

    noi_y1 = years[0]["noi"]
    implied = noi_y1 / cap_rate
    return {
        "status": "computed",
        "source_format": "institutional multifamily pro forma (4-sheet)",
        "property": a.get("property"),
        "location": a.get("location"),
        "units": units,
        "years": [clean(y) for y in years],
        "valuation": {
            "basis": "year_1_noi_after_replacement_reserve",
            "cap_rate": cap_rate,
            "cap_rate_source": "parameter — the workbook carries no cap rate; "
                               "default is the SURA fixture rate (mock)",
            "implied_value": _r2(implied),
            "price_per_unit": _r2(implied / units),
        },
        "conventions": [
            "Taxes and Insurance(s) are separate lines/buckets, never inside OpEx; "
            "expenses.total follows the workbook's presentation so its NOI reconciles.",
            "Replacement Reserve is its own line, subtracted above NOI (the workbook's convention).",
            "NOI is unlevered; no debt service exists anywhere in this model.",
        ],
    }


# ---------------------------------------------------------------- parser

MAX_XLSX_BYTES = 10_000_000

_RECOGNIZED_LABELS = {
    "property", "location", "total units", "annual rent growth rate",
    "initial occupancy at purchase", "stabilized vacancy rate (yr 2+)",
    "commercial income ($/yr)", "commercial vacancy",
    "utility reimbursements ($/unit/yr)", "credit loss / bad debt",
    "fee income ($/unit/yr)", "other income ($/unit/yr)",
    "other income growth rate", "management (% of egi)",
    "expense growth rate", "tax growth rate",
} | {label.lower() for _k, label, _o in _EXPENSE_LINES}


def _coerce_number(v: Any) -> float | None:
    """Numbers as real-world files carry them: 1615, 1615.0,
    "1,615", "$1,615", "3%" (-> 0.03). Anything else: None."""
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        t = v.strip().replace("$", "").replace(",", "").replace(" ", "")
        if not t:
            return None
        try:
            if t.endswith("%"):
                return float(t[:-1]) / 100
            return float(t)
        except ValueError:
            return None
    return None


def _label_map(ws) -> dict[str, Any]:
    """First-column label -> value in column B, normalized keys."""
    out: dict[str, Any] = {}
    for row in ws.iter_rows(min_col=1, max_col=2):
        label, value = row[0].value, row[1].value
        if isinstance(label, str) and label.strip():
            out[" ".join(label.strip().lower().split())] = value
    return out


def _parse(data: bytes) -> tuple[dict[str, Any], dict[str, Any]]:
    """Parse + a blind-test report: what defaulted, what was
    present but unmapped, and what looks off. Required fields
    that are missing fail ONCE, listing all of them."""
    if len(data) > MAX_XLSX_BYTES:
        raise ValueError(f"workbook too large: {len(data)} bytes (limit {MAX_XLSX_BYTES})")
    try:
        import openpyxl
    except ImportError as e:  # pragma: no cover
        raise ValueError("openpyxl is not installed") from e
    try:
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    except Exception as e:
        raise ValueError(f"not a readable .xlsx workbook: {e}") from e
    for sheet in ("Assumptions", "Pro Forma"):
        if sheet not in wb.sheetnames:
            raise ValueError(f"missing required sheet: {sheet}")
    ws = wb["Assumptions"]
    labels = _label_map(ws)
    report: dict[str, Any] = {"defaulted": [], "unmapped_labels": [], "warnings": []}
    missing: list[str] = []

    def num(label: str, default: float | None = None) -> float:
        v = _coerce_number(labels.get(label.lower()))
        if v is None:
            if default is not None:
                report["defaulted"].append(label)
                return default
            missing.append(label)
            return 0.0
        return v

    a: dict[str, Any] = {
        "property": labels.get("property"),
        "location": labels.get("location"),
        "total_units": int(num("Total Units")),
        "rent_growth": num("Annual Rent Growth Rate"),
        "initial_occupancy": num("Initial Occupancy at Purchase"),
        "stabilized_vacancy": num("Stabilized Vacancy Rate (Yr 2+)"),
        "commercial_income": num("Commercial Income ($/yr)", 0.0),
        "commercial_vacancy": num("Commercial Vacancy", 0.0),
        "utility_reimbursement_per_unit": num("Utility Reimbursements ($/unit/yr)", 0.0),
        "credit_loss_rate": num("Credit Loss / Bad Debt"),
        "fee_income_per_unit": num("Fee Income ($/unit/yr)", 0.0),
        "other_income_per_unit": num("Other Income ($/unit/yr)", 0.0),
        "other_income_growth": num("Other Income Growth Rate", 0.0),
        "management_fee_pct": num("Management (% of EGI)"),
        "expense_growth": num("Expense Growth Rate"),
    }
    for key, label, _out in _EXPENSE_LINES:
        a[key] = num(label)
    if missing:
        raise ValueError(
            "missing required assumptions on sheet 'Assumptions': "
            + ", ".join(missing)
        )

    # Unit mix: rows under 'UNIT MIX' — col D type, E existing,
    # F market rent, G value-add, H va rent, I delivery month.
    mix: list[dict[str, Any]] = []
    for row in ws.iter_rows(min_col=4, max_col=9):
        t = row[0].value
        if isinstance(t, str) and t.strip().lower().startswith("total"):
            break  # the mix table ends at its Total / Blended row
        existing = _coerce_number(row[1].value)
        if isinstance(t, str) and t.strip() and existing:
            def _num(v: Any) -> float:
                return _coerce_number(v) or 0.0

            mix.append({
                "type": t.strip(),
                "existing": int(existing),
                "market_rent": _num(row[2].value),
                "value_add": int(_num(row[3].value)),
                "value_add_rent": _num(row[4].value),
                "delivery_month": int(_num(row[5].value)),
            })
    if not mix:
        raise ValueError("no unit-mix rows found on the Assumptions tab")
    a["unit_mix"] = mix
    mix_units = sum(m["existing"] + m["value_add"] for m in mix)
    if mix_units != a["total_units"]:
        report["warnings"].append(
            f"unit mix sums to {mix_units} units but Total Units says {a['total_units']}"
        )

    # Lease-up: the vertical month table (col D month, col E new leases).
    leases: dict[int, int] = {}
    for row in ws.iter_rows(min_col=4, max_col=5):
        m = _coerce_number(row[0].value)
        n = _coerce_number(row[1].value)
        if m is not None and 1 <= int(m) <= 12 and n is not None:
            leases[int(m)] = int(n)
    a["lease_up_new_leases"] = [leases.get(m, 0) for m in range(1, 13)]
    if not any(a["lease_up_new_leases"]):
        report["warnings"].append(
            "no lease-up leases filed — Year 1 runs at initial occupancy all year"
        )

    # Replacement reserves: 'Reserve — Year N' labels in col G, values col H.
    reserves: dict[int, float] = {}
    for row in ws.iter_rows(min_col=7, max_col=8):
        label, v = row[0].value, _coerce_number(row[1].value)
        if isinstance(label, str) and "reserve" in label.lower() and v is not None:
            for n in range(1, 10):
                if f"year {n}" in label.lower():
                    reserves[n] = v
    a["replacement_reserve_per_unit"] = [reserves.get(n, 0.0) for n in range(1, 6)]
    if len(reserves) < 5:
        report["warnings"].append(
            f"replacement reserve filed for {len(reserves)} of 5 years — missing years are computed at 0"
        )

    report["unmapped_labels"] = sorted(
        k for k, v in labels.items()
        if k not in _RECOGNIZED_LABELS and _coerce_number(v) is not None
    )
    return a, report


def parse_proforma_xlsx(data: bytes) -> dict[str, Any]:
    """Extract the assumptions dict from a 4-sheet pro forma file."""
    a, _report = _parse(data)
    return a


def parse_with_report(data: bytes) -> tuple[dict[str, Any], dict[str, Any]]:
    """parse_proforma_xlsx + the blind-test report (defaulted /
    unmapped / warnings). Raises ValueError on unreadable files
    and on missing REQUIRED assumptions, listing all of them."""
    return _parse(data)


# ---------------------------------------------------------------- routes

class ProformaFileIn(BaseModel):
    file_base64: str
    cap_rate: float | None = None


class ProformaAssumptionsIn(BaseModel):
    assumptions: dict[str, Any]
    cap_rate: float | None = None


@router.post("/api/v1/ingest/proforma")
def ingest_proforma(body: ProformaFileIn) -> dict[str, Any]:
    """Parse a base64-encoded 4-sheet pro forma .xlsx and compute
    its Years 1-5 EGI/NOI exactly as the workbook does."""
    try:
        raw = base64.b64decode(body.file_base64, validate=True)
    except Exception:
        raise HTTPException(422, "file_base64 is not valid base64")
    try:
        assumptions, report = parse_with_report(raw)
        out = compute_proforma(assumptions, body.cap_rate or DEFAULT_CAP_RATE)
        out["parse_report"] = report
        return out
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.post("/api/v1/ingest/proforma/from-assumptions")
def proforma_from_assumptions(body: ProformaAssumptionsIn) -> dict[str, Any]:
    try:
        return compute_proforma(body.assumptions, body.cap_rate or DEFAULT_CAP_RATE)
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(422, f"invalid assumptions: {e}")


@router.get("/api/v1/ingest/proforma/sample")
def proforma_sample() -> dict[str, Any]:
    """The filed Graham Hill sample, computed live."""
    return compute_proforma(SAMPLE_ASSUMPTIONS)
