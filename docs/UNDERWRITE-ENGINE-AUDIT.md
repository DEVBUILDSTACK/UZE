# UZE Underwrite — Engine Audit (HiCRE & ANRD)

**Audience:** James and the investment analyst. **Status: 🟡
analysis, projection, verification and valuation math REAL and
tested · document extraction MOCKED · market comps SYNTHETIC.**
Filed 2026-11-12. Documentation only — this audit describes the
code; it changes none of it. The deep code-level companion is
`docs/UNDERWRITE-ENGINE-ANALYSIS.md`; where the two differ in
framing, the analysis document's executed figures govern.

---

## Executive summary

UZE Underwrite is the autonomous agentic P&L side of
UZEmarkets. An asset's financials enter as raw, inconsistently
labelled historical statements; the engine normalizes them into
one ratified taxonomy, derives an unlevered NOI the business can
stand behind, projects that P&L twelve months forward with every
assumption labelled, later verifies the projection against the
actuals that arrive, and values the asset on the income approach
against micro-region comps. Two engines share the discipline and
split the asset world:

- **SURA — HiCRE (Hospitality & Income CRE).** Hotels,
  multifamily, residential rental and condo, hospitality/resort.
  One bucket-level engine serves every HiCRE class: there are no
  separate hospitality and multifamily formula chains (no
  departmental/undistributed build-up, no GPR→EGI chain) — the
  seven-bucket derivation in Scenario 1 is the whole calculation,
  for a 128-unit hotel fixture and a multifamily T-12 alike.
- **GIRA — ANRD (Agriculture, Development, Resource).** Land is
  not valued on a CRE cap rate. GIRA values productivity: net
  agricultural income on an income multiple, with raw-acreage
  comps alongside (Scenario 3).

The trust loop is the point of the architecture: a projection is
a claim, and claims get verified. Tier 3 scores last year's
projection against this year's actual NOI; an underwriter whose
projections verify earns Precedent Index standing, and one whose
projections miss beyond threshold gets their methodology — not
the property — flagged for the Juror Team.

**Corrections carried in this audit** (the commissioning brief
described four behaviours the code does not have; they are
corrected in place, not transcribed): document extraction is a
mock — there is no OCR and no balance-sheet or sales-data
ingestion; revenue projection growth is sourced from historical
inflation today, with comps-market-trend sourcing a logged
post-recording refinement, not shipped behaviour; Price/Unit
and Price/SqFt are both computed whenever inputs exist, with no
asset-class prioritization rule; valuation by the income
approach runs on verified historical NOI, with a separately
labelled projected value in the projection output.

---

## Scenario 1 — Historical P&L & financial ingestion

**The data.** Two ingestion surfaces exist. The email gateway
(`POST /api/v1/ingest/email`) accepts a forwarded statement
({subject, sender, attachment}) and routes it by subject —
track, use case (standard / valuation / emergency / placement),
and directed focus (distressed, refinancing, cost recovery).
The multi-year endpoint (`POST /api/v1/ingest/multiyear`)
accepts structured years of T-12 line items directly. What does
**not** exist: OCR or document intelligence of any kind — the
gateway's extractor counts the attachment's bytes and returns
deterministic per-track sample figures, and says so on the
generated PDF's face — and no balance-sheet or sales-data
ingestion. The routing, normalization, analysis and reporting
around the mock extraction are real.

**The math — normalization.** The StandardChartOfAccounts
(`chart_of_accounts.py`) maps each raw label into exactly one
of seven ratified buckets — **Revenue · Operating Expenses ·
Taxes · Insurance(s) · Interest Expense/Income · Miscellaneous
Net Expenses/Income · Profit (Net Income)** — by
case/punctuation-insensitive variant matching, so "Repairs &
Maintenance", "R&M" and "Maintenance Expense" converge.
Vacancy Loss, Credit Loss and Bad Debt bucket to Revenue as
contra-revenue deductions. A label with no filed variant is
returned as **unmapped** for human review — never guessed,
because a silently mis-bucketed tax line is the failure this
layer exists to prevent. Tests pin the load-bearing rule:
taxes, insurance and interest can never land in Operating
Expenses.

**The math — unlevered NOI.** Per year:

```
NOI (unlevered)    = Revenue − Operating Expenses − Taxes
                     − Insurance(s) − Miscellaneous Net
levered cash flow  = NOI − Interest Expense/Income   (separate line)
```

Interest and debt service are never inside NOI; the
post-interest figure is reported under its own name. Filed
Profit-bucket lines are excluded from the derivation so nothing
double-counts. On the demo hotel fixture: revenue 1,842,500 −
OpEx 1,093,800 − taxes 148,200 − insurance 96,400 = **NOI
504,100** (27.4% margin).

**Trend flags.** Any bucket moving more than 15%
year-over-year is flagged "requires line-item review", and the
Tier 1 output states the most recent step in words ("Insurance(s)
costs have risen 50.0% year-over-year"). Taxes — the largest
driver of micro-market variability — are benchmarked only
against the property's own micro-region.

## Scenario 2 — The projected P&L (pro forma)

**The logic.** A human analyst or an autonomous agent working
from the same historicals gets the same instrument:
`generate_projection()` in `underwrite_engine.py` rolls the
latest historical year forward twelve months. The SURA analysis
directive (carried in `agents.py`, read by every SURA surface)
requires the three tiers to stay distinct: historicals as
filed, projections with labelled assumptions, verification
when actuals land.

**The math — growth assumptions.** Each bucket grows at its
own rate, and every rate carries its source in the output's
`assumptions` list:

- **Default — Historical Inflation:** the bucket's most recent
  historical YoY rate, per bucket. An insurance line that rose
  50% last year projects at +50%; a flat interest line projects
  flat.
- **Overrides:** an explicit revenue-growth rate (the slot where
  a market view — rent growth, an ADR/occupancy path — is
  entered by the analyst or agent) and per-bucket growth
  overrides, each labelled "explicit override".
- **Known shocks:** absolute adjustments applied after growth —
  a property-tax reassessment is +$X to Taxes, labelled "known
  shock", never smeared into a growth rate.

**Not yet shipped — stated plainly:** sourcing the revenue
rate automatically from the comps layer's market trends (the
synthetic Baltimore-Washington set carries rent growth of
3.1%), labelled "Market Trend" beside "Historical Inflation",
is the logged post-recording refinement. Today that figure
enters only as an explicit override.

**Outputs.** Projected buckets, **projected NOI (unlevered)**,
projected levered cash flow, the projected cap rate (the
underwriting cap rate, optionally shifted by basis points and
labelled as held), and a projected implied value. Then the
loop closes: when the actual year files, `verify_projection()`
computes signed variance % and an accuracy score against the
projection. Within the 10% default threshold the underwriter
earns a Precedent Index event; beyond it, the methodology is
flagged for the Juror Team. (Both the threshold and the
accuracy mechanics are policy parameters; the Precedent Index
is currently a returned event record, not a persisted score.)

## Scenario 3 — Income-based valuation (comps & cap rates)

**The logic.** The income approach, on the figure the market
can rely on:

```
Implied Value = Verified Unlevered NOI / Cap Rate
```

`income_valuation()` takes the verified NOI **by parameter
name** — levered cash flow cannot be passed as the basis
without misusing the API. On the fixture: 504,100 / 5.5% =
**$9,165,454.55**. The Tier 2 projection separately reports a
projected implied value from projected NOI, labelled as
projection-based; the two values are never conflated.

**The comps.** The CoStar-shaped adapter (`costar.py`) serves
sales comps, STR-shaped hospitality metrics (occupancy / ADR /
RevPAR) and market trends per micro-region behind one
interface, so a licensed provider can replace it without the
underwriting flow changing. Every payload is labelled
synthetic, with the standing line verbatim: *"CoStar-shaped
adapter, built to the interface, license pending."* One
synthetic region exists (Baltimore-Washington); an unknown
region returns it with a fallback flag — never silently.

**Validation metrics.** Against the asking price the engine
computes **both** Price per Unit and Price per Square Foot
whenever the inputs exist (fixture: $9,400,000 asking →
$73,437.50/unit over 128 units; $97.51/sq ft over 96,400 sq ft),
to be read against the micro-region comps. There is no rule
prioritizing one metric for multifamily and the other for
commercial — both are reported, and the analyst weighs them.

**The ANRD path (GIRA).** `gira_yield_valuation()` values land
on productivity: net agricultural income (projected crop
revenue − input costs) × an income multiple — 20× shipped as
the labelled default — plus a raw-acreage value (acres ×
price/acre) when those inputs exist. The logged refinement
splits the two properly: acreage comps as the primary basis
for raw land, a yield multiple nearer 5× for active farms.
GIRA's intake is evidence-gated and separate from the HiCRE
surface: agricultural referrals stop at INPUT_VALIDATED with
provider status forced UNVERIFIED, and ANRD subjects are
declined on the email underwrite endpoint — the tracks share
the taxonomy discipline and nothing else.
