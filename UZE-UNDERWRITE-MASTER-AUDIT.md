# UZE Underwrite — Master Audit & Explainer (HiCRE & ANRD)

**The single definitive document for the investment analyst.**
Part 1 explains the whole engine in business terms. Part 2
proves the math against a real institutional workbook — Graham
Hill, 152 units, Mechanicsburg PA — reproducing its results to
the cent. Part 3 is the technical appendix. Filed 2026-11-12;
suite **319 passed**. This document consolidates and supersedes
the earlier fragments (`docs/UNDERWRITE-ENGINE-ANALYSIS.md`,
`docs/UNDERWRITE-ENGINE-AUDIT.md`, `UZE-MATH-AUDIT-FOR-ANALYST.md`)
as the analyst's reading copy; those remain the code-level
record.

**Status labels, once, up front:** 🟢 the normalization,
historical analysis, projection, verification, valuation and
pro forma math are real and test-pinned · 🟡 email-surface
document extraction is a labelled mock · 🟡 market comps are a
synthetic, CoStar-shaped adapter (license pending) · the
pro forma Excel parser is real (openpyxl).

---

# Part 1 — The Executive Explainer

## The problem

Underwriting a multifamily or hospitality asset starts with
someone re-typing a T-12. The statements arrive as PDFs, emails
and spreadsheets, every operator labelling the same cost
differently — "R&M", "Repairs & Maintenance", "Maintenance
Expense". Three failure modes follow. Figures get bucketed
wrong: taxes or insurance folded into operating expenses, which
quietly corrupts every benchmark comparison downstream, because
taxes are the largest driver of variability between
micro-markets. Interest gets subtracted on the way to NOI,
which produces a levered figure wearing an unlevered label —
the single most common credibility failure in a financing
conversation. And nothing is verified: a projection is made,
the year passes, and nobody scores the projection against the
actuals, so an underwriter's track record is anecdote.

## The solution — autonomous ingestion (SURA, HiCRE)

SURA is the HiCRE engine (Hospitality & Income CRE — hotels,
multifamily, residential rental and condo, hospitality/resort).
Financials enter through three surfaces: an email gateway for
forwarded statements, a structured multi-year endpoint, and —
since 2026-11-12 — a real parser for the institutional pro
forma workbook format (Part 2). Every raw line, however
labelled, is normalized into exactly seven ratified buckets —
**Revenue · Operating Expenses · Taxes · Insurance(s) ·
Interest Expense/Income · Miscellaneous Net Expenses/Income ·
Profit** — by a Standard Chart of Accounts. A label the chart
does not know is returned as *unmapped* for human review, never
guessed: the system's core discipline is that a silently
mis-bucketed line is worse than an unprocessed one. From the
normalized buckets the engine derives the trusted baseline:

> **NOI = Revenue − Operating Expenses − Taxes − Insurance(s)
> − Miscellaneous Net** — unlevered, always. The post-interest
> figure exists too, under its own name: *levered cash flow*.

Year-over-year movements beyond 15% in any bucket are flagged
for line-item review, and the analysis is benchmarked only
against the property's own micro-region.

## The forward projection

Two projection instruments sit on that baseline. The **Tier 2
projection** rolls a property's own historicals forward twelve
months: each bucket grows at its own most recent year-over-year
rate (per-bucket historical inflation — an insurance line that
rose 50% projects at +50%), with explicit overrides and known
shocks (a tax reassessment is a labelled dollar adjustment to
Taxes, never smeared into a growth rate), and every assumption
is printed with its source. When the actual year files,
**Tier 3 verification** scores the projection: variance beyond
a 10% threshold flags the underwriter's *methodology* — not the
property — for the Juror Team; a verified projection earns
Precedent Index standing. The **pro forma engine** (Part 2)
builds the full five-year institutional statement — GPR → EGI
→ NOI — from a workbook's assumptions, including a monthly
lease-up for Year 1.

## The valuation

The income approach, on the figure a lender can rely on:
**Implied Value = verified unlevered NOI ÷ cap rate**. The
historical engine values on *verified historical* NOI; the pro
forma engine values on its Year 1 NOI (the workbook format
carries no cap rate, so the rate is an explicit parameter —
Part 2 uses 5.5%). Price per Unit and Price per Square Foot
are computed alongside, to be read against micro-region comps.
The comps layer is a CoStar-shaped adapter returning synthetic,
labelled data behind the real interface — the benchmarking
logic is production-shaped; the benchmark data awaits the
license.

## The ANRD distinction (GIRA)

Agriculture, Development and Resource assets are not valued
on a CRE cap rate, and GIRA — the ANRD engine — does not try.
Land is valued on productivity: net agricultural income
(projected revenue less input costs) carried on an income
multiple, with a raw-acreage value (acres × price per acre)
alongside. ANRD intake is evidence-gated and separate: no
financing, treatment or auction executes from it. Same
taxonomy discipline, completely different valuation physics —
by design.

---

# Part 2 — The Math Audit (Graham Hill as the test case)

The workbook: 152 units (mix: 18×1BR @ $1,495 · 4 @ $1,695 ·
33 @ $1,795 · 81×2BR @ $1,895 · 16×3BR @ $1,995; blended
$1,831.18/mo), 90.13% in-place occupancy, 5% stabilized
vacancy, 0.75% credit loss, 3% rent growth, 3% expense growth,
management fee 3% of EGI, replacement reserve $200→$400/unit
escalating. The engine's output below is checked against the
workbook's **own cached values** — the acceptance standard is
the file itself.

## 2.1 The GPR → EGI chain

Year 1 runs through the monthly lease-up (months at the
workbook's occupancy path, 137 in-place + 7 leases); Years 2+
are stabilized:

```
GPR (Yr 1)      = Σ monthly mix rent            =  3,340,080.00
Vacancy (Yr 1)  = Σ −GPR_m × (1 − occupancy_m)  =   −197,767.89
Credit Loss     = −0.75% × (GPR − Vacancy)      =    −23,567.34
Net Rental Inc. = GPR + Vacancy + Credit Loss   =  3,118,744.76
Other Income    = fee/other 132,275 + utility
                  reimbursements 37,180         =    +169,455.00
EGI (Yr 1)      = NRI + Other Income            =  3,288,199.76  ✓ workbook
```

Years 2+: `GPR = mix × 12 × (1 + 3%)` in Year 2, then ×1.03
per year; vacancy = −5% × GPR; credit loss on (GPR − vacancy)
as above; fee/other and utility income scale with occupied
units and grow at 3%.

## 2.2 The NOI derivation — Year 1, to the cent

Expenses are per-unit × 152 in Year 1. Note where Taxes and
Insurance sit: their own lines, their own buckets — the
workbook's combined total is shown because that is its
presentation, and the UZE view reports OpEx excluding both
($948,325.99):

```
Payroll 334,400.00 · Utilities 157,320.00 · Mechanical 5,320.00
R&M 206,720.00 · Interior 38,000.00 · Materials 15,200.00
Marketing 36,480.00 · Management Fee 98,645.99 (= 3% × EGI)
G&A 51,680.00 · Professional 4,560.00
Insurance 116,280.00 · Real Estate Taxes 245,480.00
Total Operating Expenses                = 1,310,085.99
Replacement Reserve (200 × 152)         =     30,400.00

NOI = EGI − Total OpEx − Reserve
    = 3,288,199.76 − 1,310,085.99 − 30,400.00
    = $1,947,713.77   ✓ the workbook's Year 1 NOI, exactly
```

## 2.3 The five-year projections

Rent +3%/yr, expenses +3%/yr (Year 2 = Year 1 × 1.03, and so
on), management fee re-struck at 3% of each year's EGI,
reserve per the Assumptions schedule ($200/250/300/350/400):

| Year | GPR | EGI | Total OpEx | Reserve | **NOI** |
|---|---|---|---|---|---|
| 1 | 3,340,080.00 | 3,288,199.76 | 1,310,085.99 | 30,400 | **1,947,713.77** |
| 2 | 3,440,282.40 | 3,418,877.37 | 1,350,349.52 | 38,000 | **2,030,527.85** |
| 3 | 3,543,490.87 | 3,521,443.69 | 1,390,860.01 | 45,600 | **2,084,983.68** |
| 4 | 3,649,795.60 | 3,627,087.00 | 1,432,585.81 | 53,200 | **2,141,301.19** |
| 5 | 3,759,289.47 | 3,735,899.61 | 1,475,563.38 | 60,800 | **2,199,536.23** |

Every cell matches the workbook's cached value (test tolerance:
5 cents; observed difference: zero after rounding).

## 2.4 The valuation

```
Implied Value  = Year 1 NOI / Cap Rate
               = 1,947,713.77 / 0.055  = $35,412,977.66
Price per Unit = 35,412,977.66 / 152   = $232,980.12
```

The 5.5% is a parameter, labelled in the output — the workbook
carries no cap rate; 5.5% is the rate the SURA fixture set
uses, adopted here as the mock default.

---

# Part 3 — Technical Appendix

## 3.1 The parser (real, openpyxl)

`services/compose/src/proforma.py` — the workbook is read by
label, not by fixed cell addresses, so the format survives
re-layouts:

```python
wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
for sheet in ("Assumptions", "Pro Forma"):
    if sheet not in wb.sheetnames:
        raise ValueError(f"missing required sheet: {sheet}")
ws = wb["Assumptions"]
labels = _label_map(ws)   # col-A label -> col-B value, normalized
a = {
    "total_units": int(num("Total Units")),
    "rent_growth": num("Annual Rent Growth Rate"),
    "stabilized_vacancy": num("Stabilized Vacancy Rate (Yr 2+)"),
    "credit_loss_rate": num("Credit Loss / Bad Debt"),
    "management_fee_pct": num("Management (% of EGI)"),
    # ... per-unit expense lines, unit mix, lease-up months,
    # and the Reserve — Year N schedule, extracted the same way
}
```

## 3.2 The tests that pin this math

`services/compose/tests/test_proforma.py` (7 tests), against
the workbook's transcribed cached values:

- `test_graham_hill_all_five_years_match_the_workbook` — GPR,
  EGI, total OpEx and NOI for all five years, plus the identity
  NOI = EGI − OpEx − Reserve per year
- `test_year1_flows_through_lease_up_not_stabilized_vacancy` —
  Year 1 vacancy is occupancy-driven (−197,767.89), not the
  stabilized 5%; credit-loss base; management fee = 3% of EGI
- `test_taxes_and_insurance_stay_out_of_opex_in_the_uze_view`
- `test_valuation_applies_cap_rate_to_year1_noi`
- `test_parser_reads_the_four_sheet_structure` ·
  `test_parser_rejects_a_non_workbook` ·
  `test_api_sample_and_file_ingest`

The historical engine's pins, for completeness:
`test_multiyear_noi_is_unlevered_and_levered_figure_is_separate`
(NOI 750,000 vs levered 600,000 on a 150,000 interest line),
`test_taxes_insurance_interest_never_land_in_opex`,
`test_vacancy_and_credit_loss_are_contra_revenue`.

## 3.3 The endpoint contract

```
POST /api/v1/ingest/proforma
  { "file_base64": "<.xlsx, base64>", "cap_rate": 0.055? }
  -> 200 { status, property, units, years[5]{ gpr, vacancy_loss,
       credit_loss, net_rental_income, total_other_income, egi,
       expenses{...lines, management_fee, total},
       replacement_reserve, noi, uze_view{...} },
       valuation{ implied_value, price_per_unit, cap_rate } }
  -> 422 on unreadable workbook / missing sheet / missing assumption

POST /api/v1/ingest/proforma/from-assumptions  { assumptions, cap_rate? }
GET  /api/v1/ingest/proforma/sample            the Graham Hill file, computed live
```

---

*Consolidation note: written 2026-11-12 on the owner's tap as
the single analyst-facing document. The code-level record
remains `docs/UNDERWRITE-ENGINE-ANALYSIS.md` (updated through
§8, the pro forma build) and the executed-numbers record in
`docs/TICKETING-DELPHI-EXECUTION.md` for the ticketing layer.*
