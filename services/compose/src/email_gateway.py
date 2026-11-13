"""Agentic Email Gateway (directed build, 2026-11-10; demo scope).

POST /api/v1/ingest/email accepts a forwarded client email payload
{subject, sender, attachment_base64} and routes it by subject
keywords:

  - Track routing: HiCRE/Hotel -> SURA, ANRD/Farm -> GIRA; no track
    and no use-case default -> 422 {"error": "Could not determine
    asset track"}.
  - Use-case routing (James's three real-world scenarios,
    2026-11-10), in precedence order:
      C. Talent / Management / Hiring -> Human Talent Placement
         protocol: the AI P&L analysis is bypassed and a placement
         alert is recorded.
      B. Acquisition / Due Diligence / Valuation -> the track
         agent's valuation flow: 12/18/36-month NOI historicals, a
         cap rate, and the implied value (NOI / Cap Rate).
      A. Urgent P&L / Replacement / Immediate -> an urgency flag on
         the standard P&L verification; the PDF carries the Talent
         Placement cross-sell footer. An emergency subject with no
         track keyword defaults to SURA (the T-12/P&L artifact is
         HiCRE-shaped; ANRD emergencies carry ANRD/Farm keywords).

DEMO SCOPE, stated plainly: the extraction is a MOCK
(extract_mock_data) — deterministic sample figures per track, with
taxes and insurance kept separate from operating expenses per the
P&L taxonomy (Specification 07 section 2.2). Real OCR / document
intelligence is a later phase and is NOT integrated. The routing,
the API contract, and the PDF generation are real. The endpoint is
unauthenticated by design for the demo; production gating is a
later phase. The placement "alert" is recorded in the response,
not sent — no placement-team channel exists yet. The generated
PDF carries a demonstration footer saying exactly this.
"""

from __future__ import annotations

import base64
import json

import db
import proforma
import research
import talent_profile
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fpdf import FPDF
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/ingest")

CROSS_SELL_CTA = (
    "Need to replace your Property Manager too? UZEmarkets Talent "
    "Placement can source a vetted human manager for your market "
    "in 48 hours."
)

ANRD_REJECTION = (
    "UZE Underwrite currently processes Hospitality & Income CRE "
    "only. Please contact our team directly for A|NR|D spatial "
    "underwriting."
)

_ANRD_KEYWORDS = ("anrd", "farm", "land", "agriculture")

_TALENT_KEYWORDS = ("talent", "management", "hiring")
_VALUATION_KEYWORDS = ("acquisition", "due diligence", "valuation")
_EMERGENCY_KEYWORDS = ("urgent p&l", "replacement", "immediate")


class EmailIngest(BaseModel):
    subject: str
    sender: str
    attachment_base64: str


def route_agent(subject: str) -> str | None:
    """Subject-keyword routing on the UZE Underwrite endpoint:
    HiCRE only (scope narrowed 2026-11-10) — every valid T-12
    routes to SURA. GIRA remains in the codebase (_MOCK_BY_AGENT,
    the agents module) but is DISABLED on this endpoint; ANRD
    subjects are rejected before routing (see ingest_email)."""
    s = subject.lower()
    if "hicre" in s or "hotel" in s:
        return "SURA"
    return None


def is_anrd_subject(subject: str) -> bool:
    s = subject.lower()
    return any(k in s for k in _ANRD_KEYWORDS)


# User-directed analysis (diagram 17): the subject directs not
# just the flow but the FOCUS. Intent is P&L verification vs
# valuation (from the use case); the modifier names why the user
# needs it. Precedence: distressed > refinancing > cost recovery
# > the acquisition default.
_MODIFIERS = (
    (("distressed", "distress"), "distressed_sale", "rapid liquidity"),
    (("refinanc",), "refinancing", "debt service coverage"),
    (("cost recovery", "overspend"), "cost_recovery", "OpEx overspend"),
)


def detect_direction(subject: str, use_case: str) -> tuple[str, str | None, str | None]:
    """Returns (intent, modifier, focus)."""
    intent = (
        "valuation"
        if use_case == "acquisition_due_diligence"
        else "pnl_verification"
    )
    s = subject.lower()
    for keywords, modifier, focus in _MODIFIERS:
        if any(k in s for k in keywords):
            return intent, modifier, focus
    if use_case == "acquisition_due_diligence":
        return intent, "standard_acquisition", "market comps"
    return intent, None, None


def detect_use_case(subject: str) -> str:
    """The three real-world scenarios, in precedence order:
    placement (C) bypasses analysis entirely; valuation (B) adds
    the valuation flow; emergency (A) flags the standard flow."""
    s = subject.lower()
    if any(k in s for k in _TALENT_KEYWORDS):
        return "talent_placement"
    if any(k in s for k in _VALUATION_KEYWORDS):
        return "acquisition_due_diligence"
    if any(k in s for k in _EMERGENCY_KEYWORDS):
        return "emergency_replacement"
    return "standard"


_MOCK_BY_AGENT: dict[str, dict] = {
    "SURA": {
        "documentType": "T-12 Operating Statement (hotel)",
        "period": "Trailing 12 months",
        "currency": "USD",
        "revenue": 1842500,
        "operatingExpenses": 1093800,
        "taxes": 148200,
        "insurance": 96400,
        "netOperatingIncome": 504100,
        "historicalsNOI": {"months12": 504100, "months18": 731200, "months36": 1398500},
        "capRate": 0.055,
        "askingPrice": 9400000,
        "units": 128,
        "grossLeasableAreaSqFt": 96400,
        "assessment": (
            "SURA assessment: net operating income of $504,100 on "
            "revenue of $1,842,500 (NOI margin 27.4%). Taxes and "
            "insurance are stated separately from operating expenses "
            "and are flagged for benchmarking against the property's "
            "own micro-region before any claim is issued."
        ),
    },
    "GIRA": {
        "documentType": "Farm Operating Statement",
        "period": "Last completed crop year",
        "currency": "USD",
        "revenue": 862400,
        "operatingExpenses": 517900,
        "taxes": 38400,
        "insurance": 51200,
        "netOperatingIncome": 254900,
        "historicalsNOI": {"months12": 254900, "months18": 372300, "months36": 701600},
        "capRate": 0.0625,
        "assessment": (
            "GIRA assessment: net operating income of $254,900 on "
            "revenue of $862,400 (margin 29.6%). Taxes follow the "
            "parcel's local jurisdiction and crop insurance follows "
            "the local crop and climate; both are flagged for "
            "micro-region benchmarking before any claim is issued."
        ),
    },
}


def extract_mock_data(
    attachment_base64: str, agent: str, use_case: str, focus: str | None = None
) -> dict:
    """MOCK extraction (demo scope): deterministic sample figures
    per track. The attachment bytes are accepted and measured but
    NOT OCR-read — real document intelligence is a later phase.
    The valuation flow adds the historicals, the cap rate, and the
    implied value (NOI / Cap Rate) computed from them."""
    data = dict(_MOCK_BY_AGENT[agent])
    data["attachmentBytes"] = len(base64.b64decode(attachment_base64))
    if focus:
        data["assessment"] = (
            data["assessment"] + f" Directed focus: {focus}."
        )
    if use_case == "acquisition_due_diligence":
        noi = data["historicalsNOI"]["months12"]
        data["impliedValue"] = round(noi / data["capRate"], 2)
        # Institutional metrics (2026-11-11): beyond the cap
        # rate — price per unit and price per square foot
        # against the asking price, plus historical NOI growth
        # from the annualized 36-month base to trailing 12.
        asking = data.get("askingPrice")
        if asking and data.get("units"):
            data["pricePerUnit"] = round(asking / data["units"], 2)
        if asking and data.get("grossLeasableAreaSqFt"):
            data["pricePerSqFt"] = round(
                asking / data["grossLeasableAreaSqFt"], 2
            )
        base_annualized = data["historicalsNOI"]["months36"] / 3
        if base_annualized:
            data["noiGrowthRate"] = round(
                (noi - base_annualized) / base_annualized, 4
            )
        metrics_note = ""
        if "pricePerUnit" in data:
            metrics_note = (
                f" At the ${asking:,} asking price: "
                f"${data['pricePerUnit']:,.2f} per unit and "
                f"${data['pricePerSqFt']:,.2f} per square foot, to be"
                " read against the micro-region sales comps."
            )
        if "noiGrowthRate" in data:
            metrics_note += (
                f" Historical NOI growth of {data['noiGrowthRate']:.1%}"
                " from the 36-month annualized base to trailing 12."
            )
        data["assessment"] = (
            data["assessment"]
            + f" Valuation: at a {data['capRate']:.2%} capitalization"
            f" rate on trailing-12 NOI of ${noi:,}, the implied value"
            f" is ${data['impliedValue']:,.2f}, subject to benchmark"
            " verification of the 12/18/36-month historicals."
            + metrics_note
        )
    else:
        data.pop("historicalsNOI", None)
        data.pop("capRate", None)
        data.pop("askingPrice", None)
        data.pop("units", None)
        data.pop("grossLeasableAreaSqFt", None)
    return data


def _money(value) -> str:
    return f"${value:,.2f}" if isinstance(value, float) else f"${value:,}"


def render_pdf(payload: EmailIngest, agent: str, data: dict, cross_sell: str | None) -> bytes:
    """One-page PDF assessment report (fpdf2, no OS dependencies)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "UZEmarkets - Agent Assessment Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 7, f"Underwriting agent: {agent}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Subject: {payload.subject}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"From: {payload.sender}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Document: {data['documentType']} - {data['period']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Extracted financials", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    rows = [
        ("Revenue", data["revenue"]),
        ("Operating Expenses", data["operatingExpenses"]),
        ("Taxes", data["taxes"]),
        ("Insurance", data["insurance"]),
        ("Net Operating Income", data["netOperatingIncome"]),
    ]
    for label, value in rows:
        pdf.cell(70, 7, label)
        pdf.cell(0, 7, _money(value), new_x="LMARGIN", new_y="NEXT")
    if "impliedValue" in data:
        pdf.ln(2)
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "Valuation (NOI / Cap Rate)", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 11)
        hist = data["historicalsNOI"]
        for label, value in [
            ("NOI - trailing 12 months", hist["months12"]),
            ("NOI - trailing 18 months", hist["months18"]),
            ("NOI - trailing 36 months", hist["months36"]),
        ]:
            pdf.cell(70, 7, label)
            pdf.cell(0, 7, _money(value), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(70, 7, "Cap Rate")
        pdf.cell(0, 7, f"{data['capRate']:.2%}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(70, 7, "Implied Value")
        pdf.cell(0, 7, _money(data["impliedValue"]), new_x="LMARGIN", new_y="NEXT")
        if "pricePerUnit" in data:
            pdf.cell(70, 7, "Price per Unit (asking)")
            pdf.cell(0, 7, _money(data["pricePerUnit"]), new_x="LMARGIN", new_y="NEXT")
        if "pricePerSqFt" in data:
            pdf.cell(70, 7, "Price per Sq Ft (asking)")
            pdf.cell(0, 7, _money(data["pricePerSqFt"]), new_x="LMARGIN", new_y="NEXT")
        if "noiGrowthRate" in data:
            pdf.cell(70, 7, "NOI Growth (36m base to T12)")
            pdf.cell(0, 7, f"{data['noiGrowthRate']:.1%}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Agent assessment", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(0, 6, data["assessment"])
    if cross_sell:
        pdf.ln(4)
        pdf.set_font("helvetica", "B", 10)
        pdf.multi_cell(0, 6, cross_sell)
    pdf.ln(6)
    pdf.set_font("helvetica", "I", 8)
    pdf.multi_cell(
        0,
        5,
        "Demonstration build - document extraction is simulated "
        "pending production OCR. Routing, metering, and report "
        "generation are live.",
    )
    return bytes(pdf.output())


def analyze_multiyear(
    years: list[dict],
    context: dict | None = None,
    subject_profile: dict | None = None,
    comps: list[dict] | None = None,
    comp_threshold_pct: float | None = None,
) -> dict:
    """Multi-year T-12 analysis (2026-11-11): each year's raw
    line items are normalized through the StandardChartOfAccounts
    into the seven ratified buckets, NOI is derived per year
    (Revenue minus OpEx, Taxes, Insurance, Misc — Profit bucket
    lines are NOT double-counted), historical NOI growth is
    computed first-to-last year, and any bucket moving more than
    15% year-over-year is flagged as an expense/revenue
    fluctuation for analyst review. Unmapped labels are surfaced,
    never guessed.

    NOI is UNLEVERED (analyst correction, owner tap 2026-11-12):
    Interest is never subtracted into NOI. The post-interest
    figure is reported separately per year as levered_cash_flow
    (= NOI minus the Interest Expense/Income bucket).

    Comp-set benchmarking (D5 directive, 2026-11-13): when the
    caller declares a subject_profile and/or supplies comps,
    the result gains a "comp_benchmark" section from
    comp_benchmark.analyze_comp_set over the latest period's
    line items — per-unit revenue/expense benchmarking by
    property type, vintage, and class, findings, and a
    value-creation plan. Absent both inputs the section is
    omitted entirely (existing consumers unchanged)."""
    import chart_of_accounts as coa

    ordered = sorted(years, key=lambda y: y.get("period", ""))
    periods = []
    for entry in ordered:
        normalized = coa.normalize_line_items(entry.get("line_items", {}))
        b = normalized["buckets"]
        noi = (
            b["Revenue"]
            - b["Operating Expenses"]
            - b["Taxes"]
            - b["Insurance(s)"]
            - b["Miscellaneous Net Expenses/Income"]
        )
        levered_cash_flow = noi - b["Interest Expense/Income"]
        periods.append(
            {
                "period": entry.get("period"),
                "buckets": b,
                "noi": round(noi, 2),
                "levered_cash_flow": round(levered_cash_flow, 2),
                "unmapped": normalized["unmapped"],
            }
        )
    flags = []
    for prev, cur in zip(periods, periods[1:]):
        for bucket in coa.BUCKETS:
            before, after = prev["buckets"][bucket], cur["buckets"][bucket]
            if before and abs(after - before) / abs(before) > 0.15:
                flags.append(
                    {
                        "bucket": bucket,
                        "from_period": prev["period"],
                        "to_period": cur["period"],
                        "change_pct": round((after - before) / abs(before), 4),
                        "note": "fluctuation >15% YoY — requires line-item review",
                    }
                )
    growth = None
    if len(periods) >= 2 and periods[0]["noi"]:
        growth = round(
            (periods[-1]["noi"] - periods[0]["noi"]) / abs(periods[0]["noi"]), 4
        )
    result = {
        "periods": periods,
        "noi_growth_rate": growth,
        "fluctuation_flags": flags,
        "taxonomy": "seven-bucket P&L (Spec 07 §2.2); OpEx excludes Taxes/Insurance/Interest; NOI is unlevered — interest appears only in levered_cash_flow",
        "mock": True,
        # B2B -> B2C bridge (owner tap, 2026-11-12): the roles
        # this asset's payroll already pays for, linked to
        # Talent Placement.
        "talent_placement": talent_profile.derive_talent_placement(
            years, context
        ),
    }
    if subject_profile is not None or comps is not None:
        # Comp-set benchmarking (D5 directive, 2026-11-13):
        # additive section over the LATEST period's line items.
        # Runs only when the caller declares a subject profile
        # or supplies comps; with no comp set the section
        # carries the labelled NO_COMP_SET_SUPPLIED state
        # rather than implying a benchmark exists.
        import comp_benchmark

        latest_items = ordered[-1].get("line_items", {}) if ordered else {}
        kwargs = {}
        if comp_threshold_pct is not None:
            kwargs["threshold_pct"] = comp_threshold_pct
        result["comp_benchmark"] = comp_benchmark.analyze_comp_set(
            subject_profile, latest_items, comps, **kwargs
        )
    return result


class MultiYearIngest(BaseModel):
    years: list[dict]
    # Optional DECLARED project context for development
    # routing (owner tap, 2026-11-13): lifecycle stage,
    # domain focus, asset-class focus. Never inferred.
    context: dict | None = None
    # Optional comp-set benchmarking inputs (D5 directive,
    # 2026-11-13): the subject property's profile and the
    # caller-supplied comps. Declared, never inferred; absent
    # both, the result carries no comp_benchmark section.
    subject_profile: dict | None = None
    comps: list[dict] | None = None
    comp_threshold_pct: float | None = None


@router.post("/multiyear")
def ingest_multiyear(payload: MultiYearIngest):
    if not payload.years:
        raise HTTPException(status_code=422, detail="at least one year is required")
    try:
        result = analyze_multiyear(
            payload.years,
            payload.context,
            subject_profile=payload.subject_profile,
            comps=payload.comps,
            comp_threshold_pct=payload.comp_threshold_pct,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return JSONResponse(content=result)


@router.post("/email")
def ingest_email(payload: EmailIngest):
    # Pro forma spreadsheets route to the REAL parser
    # (2026-11-12): an attachment detected as .xlsx/.xlsm/.xls/
    # pro forma CSV is parsed before any subject routing. A
    # readable spreadsheet missing required sheets/assumptions
    # gets the parser's exact error, not the mock extraction.
    # Non-spreadsheet attachments fall through untouched.
    try:
        _raw = base64.b64decode(payload.attachment_base64, validate=True)
    except Exception:
        _raw = b""
    if proforma.detect_format(_raw) is not None:
        try:
            _assumptions, _report, _fmt = proforma.parse_any_with_report(_raw)
        except ValueError as e:
            return JSONResponse(
                status_code=422,
                content={"error": str(e), "routedTo": "UZE Underwrite pro forma parser"},
            )
        _result = proforma.compute_proforma(_assumptions)
        _result["routedTo"] = "UZE Underwrite pro forma parser"
        _result["input_format"] = _fmt
        _result["parse_report"] = _report
        return _result

    if "research" in payload.subject.lower():
        # Research door (owner directive, 2026-11-13): the
        # subject carries the question after the keyword —
        # "Research: <question>". Runs the same provider
        # functions and writes the same event log as the API
        # door (research.py); the gateway demo profile is
        # unmetered and the log row records that profile.
        _idx = payload.subject.lower().find("research")
        _query = payload.subject[_idx + len("research"):].strip(" :-").strip()
        if not _query:
            return JSONResponse(
                status_code=422,
                content={
                    "error": "research request needs a question: "
                    "put it in the subject after 'Research:'",
                    "routedTo": "UZE Research",
                },
            )
        _session = db.session()
        try:
            _result = research.run_via_gateway(
                _session, query=_query, sender=payload.sender
            )
        except research.ResearchNotConfigured:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "RESEARCH_NOT_CONFIGURED",
                    "routedTo": "UZE Research",
                },
            )
        except research.ResearchUpstreamError:
            return JSONResponse(
                status_code=502,
                content={
                    "error": "RESEARCH_UPSTREAM_ERROR",
                    "routedTo": "UZE Research",
                },
            )
        finally:
            _session.close()
        _result["routedTo"] = "UZE Research"
        return _result

    if is_anrd_subject(payload.subject):
        # Scope narrowing (2026-11-10): UZE Underwrite is HiCRE
        # only. ANRD subjects are declined politely, before any
        # use-case or track routing.
        return JSONResponse(
            status_code=422,
            content={"error": ANRD_REJECTION},
        )

    use_case = detect_use_case(payload.subject)

    if use_case == "talent_placement":
        # Talent ingestion (owner tap, 2026-11-12): a JSON
        # attachment is validated against the TalentProfile
        # schema and recorded; a PDF/Word resume gets the clean
        # deferral (parsing layer lands January 2nd); anything
        # else keeps the established placement-alert behavior.
        if talent_profile.is_pdf(_raw) or talent_profile.is_docx(_raw):
            return JSONResponse(
                status_code=422,
                content={"error": talent_profile.PDF_DEFERRAL_MESSAGE},
            )
        _profile_data = None
        try:
            _parsed = json.loads(_raw) if _raw else None
            if isinstance(_parsed, dict):
                _profile_data = _parsed
        except Exception:
            _profile_data = None
        if _profile_data is not None:
            _profile, _problems = talent_profile.validate_profile(_profile_data)
            if _profile is None:
                return JSONResponse(
                    status_code=422,
                    content={
                        "error": "INSUFFICIENT_DATA",
                        "missing_fields": _problems,
                    },
                )
            talent_profile.record_profile(_profile, payload.sender)
            return {
                "status": "success",
                "useCase": use_case,
                "routedTo": "Talent Placement — profile validated",
                "agent": None,
                "profile": _profile,
                "message": (
                    "TalentProfile validated and recorded. The "
                    "placement team matches validated profiles "
                    "against underwritten assets."
                ),
            }
        # Use Case C: bypass the AI P&L analysis entirely; record
        # the placement alert (demo scope: recorded, not sent).
        return {
            "status": "success",
            "useCase": use_case,
            "routedTo": "Human Talent Placement",
            "agent": None,
            "alert": "placement-team alert recorded (demo: not sent)",
            "message": (
                "Routed to UZEmarkets Talent Placement. The "
                "placement team sources a vetted human manager for "
                "your market (own sourced talent in Active/Pilot "
                "markets; outstaffed via human partners outside)."
            ),
        }

    agent = route_agent(payload.subject)
    if agent is None:
        if use_case == "emergency_replacement":
            agent = "SURA"  # T-12/P&L artifact default (see docstring)
        else:
            return JSONResponse(
                status_code=422,
                content={"error": "Could not determine asset track"},
            )

    intent, modifier, focus = detect_direction(payload.subject, use_case)
    data = extract_mock_data(payload.attachment_base64, agent, use_case, focus)
    cross_sell = CROSS_SELL_CTA if use_case == "emergency_replacement" else None
    pdf_b64 = base64.b64encode(
        render_pdf(payload, agent, data, cross_sell)
    ).decode()
    response = {
        "status": "success",
        "useCase": use_case,
        "intent": intent,
        "modifier": modifier,
        "focus": focus,
        "agent": agent,
        "extracted": data,
        "pdf_base64": pdf_b64,
    }
    if cross_sell:
        response["crossSell"] = cross_sell
    return response
