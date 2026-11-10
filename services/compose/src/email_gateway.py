"""Agentic Email Gateway (directed build, 2026-11-10; demo scope).

POST /api/v1/ingest/email accepts a forwarded client email payload
{subject, sender, attachment_base64}, routes it to the underwriting
agent for its asset track by subject keywords (HiCRE/Hotel -> SURA,
ANRD/Farm -> GIRA, anything else -> 422), extracts the attachment's
financials, and returns a one-page PDF assessment report (base64)
alongside the structured extraction.

DEMO SCOPE, stated plainly: the extraction is a MOCK
(extract_mock_data) — a deterministic stand-in returning sample
figures per track, with taxes and insurance kept separate from
operating expenses per the P&L taxonomy (Specification 07 section
2.2). Real OCR / document intelligence is a later phase and is NOT
integrated. The routing, the API contract, and the PDF generation
are real. The endpoint is unauthenticated by design for the demo;
production gating is a later phase. The generated PDF carries a
demonstration footer saying exactly this.
"""

from __future__ import annotations

import base64

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fpdf import FPDF
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/ingest")


class EmailIngest(BaseModel):
    subject: str
    sender: str
    attachment_base64: str


def route_agent(subject: str) -> str | None:
    """Subject-keyword routing to the track's underwriting agent."""
    s = subject.lower()
    if "hicre" in s or "hotel" in s:
        return "SURA"
    if "anrd" in s or "farm" in s:
        return "GIRA"
    return None


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
        "assessment": (
            "GIRA assessment: net operating income of $254,900 on "
            "revenue of $862,400 (margin 29.6%). Taxes follow the "
            "parcel's local jurisdiction and crop insurance follows "
            "the local crop and climate; both are flagged for "
            "micro-region benchmarking before any claim is issued."
        ),
    },
}


def extract_mock_data(attachment_base64: str, agent: str) -> dict:
    """MOCK extraction (demo scope): deterministic sample figures
    per track. The attachment bytes are accepted and measured but
    NOT OCR-read — real document intelligence is a later phase."""
    data = dict(_MOCK_BY_AGENT[agent])
    data["attachmentBytes"] = len(base64.b64decode(attachment_base64))
    return data


def _money(value: int) -> str:
    return f"${value:,}"


def render_pdf(payload: EmailIngest, agent: str, data: dict) -> bytes:
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
    pdf.ln(4)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Agent assessment", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(0, 6, data["assessment"])
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


@router.post("/email")
def ingest_email(payload: EmailIngest):
    agent = route_agent(payload.subject)
    if agent is None:
        return JSONResponse(
            status_code=422,
            content={"error": "Could not determine asset track"},
        )
    data = extract_mock_data(payload.attachment_base64, agent)
    pdf_b64 = base64.b64encode(render_pdf(payload, agent, data)).decode()
    return {
        "status": "success",
        "agent": agent,
        "extracted": data,
        "pdf_base64": pdf_b64,
    }
