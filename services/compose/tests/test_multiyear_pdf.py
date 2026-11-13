"""Multi-year underwrite PDF report (PDF follow-on, 2026-11-13).

The /multiyear endpoint and the paid SKU surface return
analyze_multiyear results as JSON only; render_pdf serves the
single-document email flow. render_multiyear_pdf is the
multiyear counterpart. Pins: with a comp_benchmark section
carrying findings, the PDF gains the Comparable Benchmarking
findings section and the Value-Creation Plan after the period
analysis, rendered only from the result dict; without the
section the report is the period analysis alone; in the
labelled NO_COMP_SET_SUPPLIED state the report states that no
comparable set was supplied and prints no findings; unicode
punctuation in plan text (the irregularity action carries an
em dash) is transliterated for fpdf2's latin-1 core fonts
instead of raising.

PDF text is read by zlib-decompressing the content streams
(stdlib only — no PDF library is a dependency of this
service).
"""

from __future__ import annotations

import re
import zlib

from email_gateway import analyze_multiyear, render_multiyear_pdf

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


def _comp(name, units, items):
    return {
        "name": name,
        "profile": {
            "property_type": "GARDEN_STYLE",
            "year_built": 2004,
            "property_class": "B",
            "unit_count": units,
            "micro_region": "baltimore-washington",
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

YEARS = [
    {"period": "2024", "line_items": {
        "Rental Income": 900_000, "Repairs & Maintenance": 120_000,
    }},
    {"period": "2025", "line_items": SUBJECT_ITEMS},
]


def _pdf_text(pdf_bytes: bytes) -> bytes:
    out = []
    for stream in re.findall(rb"stream\r?\n(.*?)endstream", pdf_bytes, re.S):
        try:
            stream = zlib.decompress(stream)
        except zlib.error:
            pass
        # PDF literal strings escape ( ) and backslash.
        out.append(re.sub(rb"\\([()\\])", rb"\1", stream))
    return b"\n".join(out)


def test_pdf_with_findings_carries_both_comp_sections():
    result = analyze_multiyear(YEARS, subject_profile=SUBJECT, comps=COMPS)
    assert result["comp_benchmark"]["findings"]  # fixture sanity
    pdf = render_multiyear_pdf(result, subject="Test Asset")
    assert pdf.startswith(b"%PDF") and pdf.rstrip().endswith(b"%%EOF")
    text = _pdf_text(pdf)
    # The existing analysis content comes first.
    assert b"UZEmarkets - Multi-Year Underwrite Report" in text
    assert b"Period analysis" in text
    assert b"Net Operating Income (unlevered)" in text
    # (a) Findings: heading, the top finding's line and
    # classification, its per-unit figures, comp basis, note.
    assert b"Comparable Benchmarking - Findings" in text
    assert b"Repairs & Maintenance" in text
    assert b"Expense opportunity" in text
    assert b"$1,500.00/unit" in text  # subject R&M per unit
    assert b"$1,200.00/unit" in text  # comp-set median per unit
    assert b"comp(s), same micro-region" in text  # count + match basis
    assert b"for further analysis" in text
    # (b) The plan: heading, value at stake for the top finding
    # ($300/unit x 100 units), an action.
    assert b"Value-Creation Plan" in text
    assert b"$30,000.00 per year at stake" in text
    assert b"Action: " in text
    # Findings render after the period analysis.
    assert text.index(b"Period analysis") < text.index(
        b"Comparable Benchmarking - Findings"
    )


def test_pdf_without_comp_section_is_the_period_analysis_alone():
    result = analyze_multiyear(YEARS)
    assert "comp_benchmark" not in result
    text = _pdf_text(render_multiyear_pdf(result))
    assert b"Period analysis" in text
    assert b"Net Operating Income (unlevered)" in text
    assert b"Levered Cash Flow" in text
    assert b"Fluctuation flags" in text
    assert b"Comparable Benchmarking" not in text
    assert b"Value-Creation Plan" not in text


def test_pdf_labelled_no_comp_set_state_is_stated_not_filled():
    result = analyze_multiyear(YEARS, subject_profile=SUBJECT, comps=[])
    assert result["comp_benchmark"]["status"] == "NO_COMP_SET_SUPPLIED"
    text = _pdf_text(render_multiyear_pdf(result))
    assert b"Comparable Benchmarking" in text
    assert b"No comparable set was supplied" in text
    assert b"Findings" not in text
    assert b"Value-Creation Plan" not in text


def test_pdf_survives_unicode_punctuation_in_plan_actions():
    # Parking far ABOVE the comp median classifies as an
    # irregularity, whose generic plan action in comp_benchmark
    # carries an em dash — outside fpdf2's latin-1 core fonts.
    items = dict(SUBJECT_ITEMS, Parking=60_000)
    result = analyze_multiyear(
        [{"period": "2025", "line_items": items}],
        subject_profile=SUBJECT, comps=COMPS,
    )
    actions = [
        p["action"] for p in result["comp_benchmark"]["value_creation_plan"]
    ]
    assert any("—" in a for a in actions)  # fixture sanity
    text = _pdf_text(render_multiyear_pdf(result))
    assert b"Verify the divergence is real and sustainable -" in text
