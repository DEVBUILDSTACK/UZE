"""Three-tier underwriting engine — SURA (HiCRE) + GIRA (ANRD).

Built 2026-11-12 on the owner's UNFREEZE tap, integrating the
investment analyst's feedback. The engine works in three tiers
plus two valuation paths:

  Tier 1 — Historicals. Multi-year T-12s are normalized through
  the StandardChartOfAccounts into the seven ratified buckets
  (email_gateway.analyze_multiyear), NOI is derived UNLEVERED,
  and per-bucket year-over-year trends are stated in words.

  Tier 2 — Projections. generate_projection() rolls the latest
  historical year forward 12 months. Default growth for every
  bucket is that bucket's most recent historical YoY rate;
  explicit overrides (revenue growth, per-bucket growth) and
  known shocks (e.g. a property-tax reassessment, as an absolute
  adjustment) are accepted and EVERY assumption is labelled by
  source in the output. Projected NOI is unlevered; the
  post-interest figure is projected_levered_cash_flow.

  Tier 3 — Verification (the Assuraties layer).
  verify_projection() compares a projection against the actual
  that later arrived for the same period: signed variance % and
  an accuracy score (100 minus |variance %|, floored at 0).
  Inside the threshold the underwriter earns a Precedent Index
  event (+1); outside it, the methodology is FLAGGED for the
  Juror Team. The threshold is a named default (10%) and a
  per-call parameter — it is a policy knob, not a constant of
  nature. The Precedent Index here is a returned event record,
  not a persisted score (mock persistence, stated in output).

  Valuation — income approach: implied value = VERIFIED
  UNLEVERED NOI / cap rate. Levered cash flow is never a
  valuation basis; income_valuation() takes the verified
  unlevered figure by name.

  Comp-set benchmarking (D5 directive, 2026-11-13) —
  POST /comp-benchmark runs comp_benchmark.analyze_comp_set:
  the subject's revenue and operating-expense lines against a
  caller-supplied comp set matched by micro-region, property
  type, vintage band, and class, per unit, with ranked
  findings and a value-creation plan. The comp set is an
  input, never a database lookup; no comps supplied returns
  the labelled NO_COMP_SET_SUPPLIED state.

  ANRD (GIRA) — land is not valued on a CRE cap rate. Net
  agricultural income (projected crop revenue minus input
  costs) is valued on an income multiple (labelled default
  20x) and, when acres and a per-acre comp are supplied, on
  raw acreage comps alongside.

Everything here is deterministic arithmetic over the caller's
figures. Where an input fixture is a mock (the gateway's
per-track constants, the CoStar-shaped comps), the mock is in
the input, not in this math.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

import chart_of_accounts as coa
import comp_benchmark
import underwrite_reports
from db import get_session
from email_gateway import analyze_multiyear

router = APIRouter(prefix="/api/v1/underwrite", tags=["underwrite-engine"])

# Policy defaults (owner-adjustable; labelled in every output).
DEFAULT_VARIANCE_THRESHOLD_PCT = 10.0
DEFAULT_ANRD_INCOME_MULTIPLE = 20.0

# The buckets that flow through a projection. Profit is derived,
# never projected; Interest is projected so the levered figure
# can be reported, but it never enters NOI.
_FLOW_BUCKETS = (
    "Revenue",
    "Operating Expenses",
    "Taxes",
    "Insurance(s)",
    "Interest Expense/Income",
    "Miscellaneous Net Expenses/Income",
)


def _pct_change(before: float, after: float) -> float | None:
    if not before:
        return None
    return (after - before) / abs(before)


def tier1_historicals(years: list[dict]) -> dict[str, Any]:
    """Tier 1: the analyzed historicals plus plain-language
    per-bucket trends for the most recent year-over-year step."""
    analysis = analyze_multiyear(years)
    periods = analysis["periods"]
    trends: list[dict[str, Any]] = []
    if len(periods) >= 2:
        prev, cur = periods[-2], periods[-1]
        for bucket in coa.BUCKETS:
            change = _pct_change(prev["buckets"][bucket], cur["buckets"][bucket])
            if change is None or abs(change) < 0.001:
                continue
            direction = "risen" if change > 0 else "fallen"
            subject = "Revenue" if bucket == "Revenue" else f"{bucket} costs"
            trends.append(
                {
                    "bucket": bucket,
                    "from_period": prev["period"],
                    "to_period": cur["period"],
                    "change_pct": round(change * 100, 2),
                    "statement": (
                        f"{subject} have {direction} {abs(change):.1%} "
                        f"year-over-year ({prev['period']} → {cur['period']})"
                        if bucket != "Revenue"
                        else f"Revenue has {direction} {abs(change):.1%} "
                        f"year-over-year ({prev['period']} → {cur['period']})"
                    ),
                }
            )
    return {**analysis, "trends": trends, "tier": 1}


def generate_projection(
    years: list[dict],
    *,
    cap_rate: float,
    revenue_growth: float | None = None,
    bucket_growth: dict[str, float] | None = None,
    shocks: dict[str, float] | None = None,
    cap_rate_shift_bps: float = 0.0,
) -> dict[str, Any]:
    """Tier 2: a labelled 12-month forward projection from the
    historical baseline. See the module docstring for the rules."""
    if cap_rate <= 0:
        raise ValueError("cap_rate must be positive")
    analysis = analyze_multiyear(years)
    periods = analysis["periods"]
    if not periods:
        raise ValueError("at least one historical year is required")
    basis = periods[-1]
    prior = periods[-2] if len(periods) >= 2 else None

    overrides = dict(bucket_growth or {})
    if revenue_growth is not None:
        overrides["Revenue"] = revenue_growth
    shocks = dict(shocks or {})
    for bucket in list(overrides) + list(shocks):
        if bucket not in _FLOW_BUCKETS:
            raise ValueError(f"unknown bucket for projection: {bucket}")

    projected: dict[str, float] = {}
    assumptions: list[str] = []
    for bucket in _FLOW_BUCKETS:
        base = basis["buckets"][bucket]
        if bucket in overrides:
            rate = overrides[bucket]
            source = "explicit override"
        elif prior is not None:
            rate = _pct_change(prior["buckets"][bucket], base) or 0.0
            source = "historical latest YoY"
        else:
            rate = 0.0
            source = "single-period history — held flat"
        value = base * (1 + rate)
        assumptions.append(f"{bucket}: growth {rate:+.2%} ({source})")
        if bucket in shocks:
            value += shocks[bucket]
            assumptions.append(
                f"{bucket}: known shock {shocks[bucket]:+,.2f} applied after growth"
            )
        projected[bucket] = round(value, 2)

    projected_noi = round(
        projected["Revenue"]
        - projected["Operating Expenses"]
        - projected["Taxes"]
        - projected["Insurance(s)"]
        - projected["Miscellaneous Net Expenses/Income"],
        2,
    )
    projected_levered = round(projected_noi - projected["Interest Expense/Income"], 2)
    projected_cap_rate = round(cap_rate + cap_rate_shift_bps / 10000.0, 6)
    return {
        "tier": 2,
        "basis_period": basis["period"],
        "projected_buckets": projected,
        "projected_noi": projected_noi,
        "projected_noi_basis": "unlevered — interest excluded",
        "projected_levered_cash_flow": projected_levered,
        "cap_rate": cap_rate,
        "projected_cap_rate": projected_cap_rate,
        "projected_implied_value": round(projected_noi / projected_cap_rate, 2)
        if projected_cap_rate > 0
        else None,
        "assumptions": assumptions,
    }


def verify_projection(
    projected_noi: float,
    actual_noi: float,
    *,
    threshold_pct: float = DEFAULT_VARIANCE_THRESHOLD_PCT,
) -> dict[str, Any]:
    """Tier 3: score a projection against the actual that
    arrived for the same period (both figures unlevered NOI)."""
    if not projected_noi:
        raise ValueError("projected_noi must be non-zero to score a variance")
    variance_pct = round((actual_noi - projected_noi) / abs(projected_noi) * 100, 2)
    accuracy = round(max(0.0, 100.0 - abs(variance_pct)), 2)
    within = abs(variance_pct) <= threshold_pct
    out: dict[str, Any] = {
        "tier": 3,
        "projected_noi": projected_noi,
        "actual_noi": actual_noi,
        "variance_pct": variance_pct,
        "accuracy_score": accuracy,
        "threshold_pct": threshold_pct,
        "status": "VERIFIED_WITHIN_THRESHOLD" if within else "FLAGGED_VARIANCE",
    }
    if within:
        out["precedent_index"] = {
            "delta": 1,
            "event": "projection_verified",
            "mock": True,
            "note": "Returned event record — no persistent Precedent Index store exists yet.",
        }
    else:
        out["juror_flag"] = {
            "flag": "UNDERWRITING_METHODOLOGY_FLAGGED",
            "reason": (
                f"Projection variance {variance_pct:+.2f}% exceeds the "
                f"{threshold_pct:.1f}% threshold — the underwriting "
                "methodology, not the property, is the finding."
            ),
        }
    return out


def income_valuation(verified_noi: float, cap_rate: float) -> dict[str, Any]:
    """Tier 4: the income approach on the VERIFIED UNLEVERED
    NOI. Levered cash flow is refused by construction — the
    parameter is the verified figure by name."""
    if cap_rate <= 0:
        raise ValueError("cap_rate must be positive")
    return {
        "tier": 4,
        "noi_basis": "verified_unlevered",
        "verified_noi": verified_noi,
        "cap_rate": cap_rate,
        "implied_value": round(verified_noi / cap_rate, 2),
    }


def gira_yield_valuation(
    projected_revenue: float,
    input_costs: float,
    *,
    income_multiple: float = DEFAULT_ANRD_INCOME_MULTIPLE,
    acres: float | None = None,
    price_per_acre: float | None = None,
) -> dict[str, Any]:
    """Tier 5 (GIRA / ANRD): land valued on productivity, not a
    CRE cap rate — net agricultural income on an income
    multiple, with a raw-acreage comp value alongside when the
    inputs exist."""
    net = round(projected_revenue - input_costs, 2)
    out: dict[str, Any] = {
        "tier": 5,
        "track": "ANRD",
        "projected_revenue": projected_revenue,
        "input_costs": input_costs,
        "net_agricultural_income": net,
        "income_multiple": income_multiple,
        "multiple_is_default": income_multiple == DEFAULT_ANRD_INCOME_MULTIPLE,
        "valuation_income_basis": round(net * income_multiple, 2),
    }
    if acres is not None and price_per_acre is not None:
        out["acres"] = acres
        out["price_per_acre"] = price_per_acre
        out["valuation_acreage_basis"] = round(acres * price_per_acre, 2)
    return out


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------


class ProjectionIn(BaseModel):
    years: list[dict]
    cap_rate: float
    revenue_growth: float | None = None
    bucket_growth: dict[str, float] | None = None
    shocks: dict[str, float] | None = None
    cap_rate_shift_bps: float = 0.0


class VerifyIn(BaseModel):
    projected_noi: float
    actual_noi: float
    threshold_pct: float = DEFAULT_VARIANCE_THRESHOLD_PCT


class ValuationIn(BaseModel):
    verified_noi: float
    cap_rate: float


class AnrdValuationIn(BaseModel):
    projected_revenue: float
    input_costs: float
    income_multiple: float = DEFAULT_ANRD_INCOME_MULTIPLE
    acres: float | None = None
    price_per_acre: float | None = None


class CompBenchmarkIn(BaseModel):
    subject_profile: dict
    # Subject financials: a single period's raw line items, or
    # a years list (the latest period is used — the same
    # convention as analyze_multiyear's comp section).
    line_items: dict | None = None
    years: list[dict] | None = None
    comps: list[dict] | None = None
    threshold_pct: float = comp_benchmark.DEFAULT_FLAG_THRESHOLD_PCT


@router.post("/projection")
def projection(body: ProjectionIn):
    if not body.years:
        raise HTTPException(status_code=422, detail="at least one historical year is required")
    try:
        tier2 = generate_projection(
            body.years,
            cap_rate=body.cap_rate,
            revenue_growth=body.revenue_growth,
            bucket_growth=body.bucket_growth,
            shocks=body.shocks,
            cap_rate_shift_bps=body.cap_rate_shift_bps,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"tier1_historicals": tier1_historicals(body.years), "tier2_projection": tier2}


@router.post("/verify-projection")
def verify(body: VerifyIn):
    try:
        return verify_projection(
            body.projected_noi, body.actual_noi, threshold_pct=body.threshold_pct
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/valuation")
def valuation(body: ValuationIn):
    try:
        return income_valuation(body.verified_noi, body.cap_rate)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/anrd-valuation")
def anrd_valuation(body: AnrdValuationIn):
    return gira_yield_valuation(
        body.projected_revenue,
        body.input_costs,
        income_multiple=body.income_multiple,
        acres=body.acres,
        price_per_acre=body.price_per_acre,
    )


@router.get("/reports/{report_id}")
def get_underwrite_report(report_id: str, session=Depends(get_session)):
    report = underwrite_reports.get_report(session, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="REPORT_NOT_FOUND: no underwrite report with this id",
        )
    return underwrite_reports.report_view(session, report)


@router.get("/reports/{report_id}/pdf")
def get_underwrite_report_pdf(report_id: str, session=Depends(get_session)):
    report = underwrite_reports.get_report(session, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="REPORT_NOT_FOUND: no underwrite report with this id",
        )
    try:
        pdf_bytes = underwrite_reports.render_report_pdf(session, report)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.get("/reports/{report_id}/notifications")
def get_underwrite_report_notifications(
    report_id: str, session=Depends(get_session)
):
    report = underwrite_reports.get_report(session, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="REPORT_NOT_FOUND: no underwrite report with this id",
        )
    return {
        "report_id": report_id,
        "notifications": underwrite_reports.list_notifications(
            session, report_id
        ),
    }


@router.post("/comp-benchmark")
def comp_benchmark_endpoint(body: CompBenchmarkIn):
    line_items = body.line_items
    if line_items is None and body.years:
        ordered = sorted(body.years, key=lambda y: y.get("period", ""))
        line_items = ordered[-1].get("line_items", {})
    if line_items is None:
        raise HTTPException(
            status_code=422,
            detail="line_items or years is required for the subject",
        )
    try:
        return comp_benchmark.analyze_comp_set(
            body.subject_profile,
            line_items,
            body.comps,
            threshold_pct=body.threshold_pct,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
