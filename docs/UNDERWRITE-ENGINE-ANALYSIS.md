# UZE Underwrite — Ingestion Engine Analysis (Analyst Review)

**Status: 🟡 analysis logic REAL and tested · extraction MOCKED ·
comps SYNTHETIC.** Filed 2026-11-12 for analyst review. Every formula
below is quoted from the code as built and, where a number appears, it
was produced by executing the code — not transcribed from a spec.

Source modules: `services/compose/src/chart_of_accounts.py` (138
lines), `email_gateway.py` (445), `agents.py` (the SURA/GIRA
endpoints and the SURA analysis directive), `costar.py` (160),
`juror.py` (the Assuraties claim juror — a different instrument,
included because the taxonomy discipline lives there too).

**Read this first — three places where the request that commissioned
this document described the engine incorrectly.** They are corrected
in place below, because the corrections are the substance of the
review:

1. Operating Expenses do **not** include Taxes and Insurance — in the
   ratified taxonomy or in the code. They are separate buckets and
   separate subtractions (§2).
2. There is **no** Gross-Potential-Rent → EGI formula chain and **no**
   departmental/undistributed hospitality chain in the code. The
   engine works at the seven-bucket level for every asset class (§2).
3. There is **no** Price/Unit-vs-Price/SqFt prioritization switch.
   Both metrics are computed whenever their inputs exist (§5).

---

## 1. Ingestion & normalization

### The two ingestion surfaces

- **Email gateway** — `POST /api/v1/ingest/email` accepts
  `{subject, sender, attachment_base64}`. Routing is by subject
  keywords, in precedence order: ANRD keywords (`anrd, farm, land,
  agriculture`) are declined first with a 422 (§6); then the use
  cases — **C** Talent/Management/Hiring → placement flow, analysis
  bypassed; **B** Acquisition/Due Diligence/Valuation → valuation
  flow; **A** Urgent P&L/Replacement/Immediate → standard flow with
  an urgency flag; otherwise standard. Track routing is HiCRE-only:
  `hicre`/`hotel` → SURA; an emergency subject with no track keyword
  defaults to SURA. A direction layer reads the subject for a
  modifier — distressed > refinancing > cost recovery — and attaches
  the matching focus (rapid liquidity / debt service coverage / OpEx
  overspend).
- **Multi-year endpoint** — `POST /api/v1/ingest/multiyear` accepts
  `{years: [{period, line_items: {label: amount}}]}` and runs
  `analyze_multiyear()` (§2). This is the surface that exercises the
  chart of accounts.

### Extraction — there is no OCR

`extract_mock_data()` is explicit in its own docstring: the
attachment is base64-decoded **only to count its bytes**
(`attachmentBytes`); it is never read. The figures are deterministic
per-track constants. Real document intelligence is a later phase, and
the generated PDF's footer says so on its face ("document extraction
is simulated pending production OCR"). The routing, the API contract,
the normalization, the analysis, and the PDF generation are real; the
extraction is the mock.

### Normalization — `StandardChartOfAccounts`

`chart_of_accounts.py` maps raw T-12 labels into the ratified
seven-bucket taxonomy (Spec 07 §2.2): **Revenue · Operating Expenses ·
Taxes · Insurance(s) · Interest Expense/Income · Miscellaneous Net
Expenses/Income · Profit (Net Income)**. Mechanics:

- A label is normalized by `_key()`: lowercase, `&` removed,
  punctuation stripped, whitespace collapsed. Lookup tries the spaced
  form, then the squashed form — so `Repairs & Maintenance`, `R&M`,
  and `Maintenance Expense` all land in Operating Expenses.
- ~50 filed variants. Every known tax label (`real estate taxes`,
  `property tax`, `state/local/federal taxes`, …) routes to Taxes;
  every insurance label to Insurance(s); every interest label to
  Interest Expense/Income.
- **Unmapped labels are never guessed.** They are returned in an
  `unmapped` list with their amounts, for human review — the module
  exists precisely so a tax line can never be silently mis-bucketed
  as an expense.
- The guarantee is pinned by tests
  (`tests/test_chart_of_accounts.py`):
  `test_taxes_insurance_interest_never_land_in_opex`,
  `test_unmapped_labels_are_reported_not_guessed`, and three more.
- **Gap closed the same day (owner's tap, 2026-11-12):** vacancy-loss
  and credit-loss / bad-debt labels were added to the variant table as
  **contra-revenue** — they bucket to Revenue, so amounts filed as
  negatives net against it instead of surfacing as `unmapped`. Pinned
  by `test_vacancy_and_credit_loss_are_contra_revenue`.

---

## 2. The P&L computation — what the code actually derives

There is one derivation, in `analyze_multiyear()`, applied per year
after normalization:

```
NOI (unlevered)    =  Revenue
                    − Operating Expenses
                    − Taxes
                    − Insurance(s)
                    − Miscellaneous Net Expenses/Income

levered cash flow  =  NOI − Interest Expense/Income
                      (reported separately per year, never as NOI)
```

- Taxes and Insurance are **their own subtractions**, never inside
  Operating Expenses — in the bucket totals, in this formula, and in
  the email fixture alike.
- Lines filed into the **Profit bucket are excluded** from the
  derivation — a filed "NOI" or "Net Income" line is never
  double-counted against the derived figure.
- The same formula serves multifamily and hospitality. The SURA
  fixture is a hotel T-12 (128 units); no asset-class-specific chain
  (no GPR − vacancy − credit loss + other income = EGI build-up, no
  departmental/undistributed split) exists anywhere in the codebase.
  If the analyst wants those chains, they are a build, not a setting.
- Per year the endpoint also computes: **bucket fluctuation flags** —
  any bucket moving more than 15% year-over-year is flagged
  "requires line-item review" — and **historical NOI growth**,
  first year to last.

**Worked example** (executed against the code for this document;
two filing years, labels deliberately inconsistent across years):

| | 2024 filed | 2025 filed |
|---|---|---|
| Rental Income | 1,000,000 | 1,100,000 |
| Repairs & Maintenance / R&M | 120,000 | 150,000 |
| Property Taxes | 90,000 | 95,000 |
| Insurance | 40,000 | 60,000 |
| Interest Expense | 150,000 | 150,000 |
| Mystery Line | 5,000 → **unmapped** | — |

Derived: NOI 750,000 (2024) → 795,000 (2025); growth **+6.0%** on
the unlevered figure; levered cash flow 600,000 → 645,000; flags
raised on Operating Expenses (+25%) and Insurance (+50%). (This
example was re-executed after the §3 fix; before the fix the same
filings reported the levered figures under the NOI label.)

The email-gateway SURA fixture, for reference (hotel, trailing 12):
Revenue 1,842,500 − OpEx 1,093,800 − Taxes 148,200 − Insurance 96,400
= **NOI 504,100** (margin 27.4%). It carries no interest or
miscellaneous lines.

---

## 3. The NOI & Interest rule — stated exactly, and the flaw it exposed (fixed)

What the code guarantees:

- Interest can never land **inside** Operating Expenses — the variant
  table routes it to its own bucket, and the test named in §1 pins
  all three families (taxes, insurance, interest) out of OpEx.
- The juror layer enforces the same discipline on claims:
  `juror.py`'s system prompt instructs the judge to categorize every
  disputed figure into exactly one bucket and to "never judge taxes,
  insurance, or interest as if they were operating expenses," judging
  taxes and insurance only against the claim's own micro-region.

**The flaw this section originally flagged — FIXED the same day
(owner's tap, 2026-11-12):** as first built, the Interest bucket was
one of the subtractions *on the way to* the figure the code labelled
`noi`, so a filing carrying an interest line produced a post-interest
(levered) figure under an NOI label — in the worked example, 600,000
reported where the unlevered NOI is 750,000. The derivation now
excludes Interest from NOI entirely and reports the post-interest
figure separately as `levered_cash_flow` per year; historical growth
is computed on the unlevered figure. Pinned by
`test_multiyear_noi_is_unlevered_and_levered_figure_is_separate`.
(The email fixture was never affected — it files no interest line,
so its 504,100 was always unlevered as presented.)

---

## 4. The SURA analysis directive

The underwriting judgment itself is codified in `agents.py` as
`SURA_ANALYSIS_DIRECTIVE`, the instruction set every SURA surface
reads (the headless endpoint, the email gateway, and any future
model-backed path):

> Analyze the provided multi-year T-12s, normalized through the
> Standard Chart of Accounts into the seven-bucket P&L … operating
> expenses never absorb taxes, insurance, or interest. Calculate
> historical NOI growth across the years provided. Evaluate the
> asking price using Cap Rate, Price per Unit, and Price per Square
> Foot against the provided micro-region sales comps. Highlight any
> anomalous line items or unexplained expense fluctuations (any
> bucket moving more than 15% year-over-year is flagged). Judge only
> against same-micro-region benchmarks.

The >15% flag in the directive and the >15% flag in
`analyze_multiyear()` are the same rule, once in prose for the
analyst-model and once in code for the deterministic path.

---

## 5. Valuation & comps

### The valuation flow (email gateway, use case B only)

Computed from the fixture's inputs — cap rate is an **input**
(5.5% in the SURA fixture), never derived:

```
impliedValue   = trailing-12 NOI / capRate        = 504,100 / 0.055  = $9,165,454.55
pricePerUnit   = askingPrice / units              = 9,400,000 / 128  = $73,437.50
pricePerSqFt   = askingPrice / GLA sq ft          = 9,400,000 / 96,400 = $97.51
noiGrowthRate  = T12 vs (36-month NOI / 3)        = 504,100 vs 466,166.67 = +8.1%
```

Both per-unit metrics are computed whenever their inputs exist and
both are printed on the PDF. There is no rule anywhere that
prioritizes Price/Unit for multifamily or Price/SqFt for
commercial/hospitality — adding one is a product decision, not a
latent behaviour to discover.

### The comps provider — CoStar-shaped, synthetic, labelled

`costar.py` defines the interface the underwriting flow consumes,
`ICoStarProvider` — `sales_comps`, `hospitality_metrics` (occupancy /
ADR / RevPAR, STR-shaped), `market_trends` — and one implementation,
`MockCoStarProvider`. The standing line, verbatim in every payload:
**"CoStar-shaped adapter, built to the interface, license pending.
Figures are SYNTHETIC demo data — not CoStar data."**

- One synthetic region exists (Baltimore-Washington; three hotel
  comps with stored price-per-unit, price-per-sqft, and cap-rate
  fields — fixture values, not computed at query time). An unknown
  region returns that set **with `fallback_region: true`** — never a
  silent substitution.
- Every response envelope carries `provider: "costar-shaped-mock"`
  and `synthetic: true`. Served at `GET /api/v1/underwrite/comps`.
- When a license exists, a live provider implements the same
  protocol at `get_provider()` and the mock retires; nothing in the
  underwriting flow changes.

---

## 6. The ANRD track — present, separate, and gated off this surface

GIRA (the A | D | R agent — Agriculture, Development, Resource)
remains fully in the codebase and shares no P&L logic with SURA:

- `agents.py` carries GIRA's underwrite endpoint: GeoJSON-polygon
  based, reading staged provider snapshots (soil profile, crop
  suitability, feedlot and agrotechnical contexts from the Agro
  Digital / BDCS / Effatha partner schemas), with subterranean
  context mandatory for A, D and R.
- `agtech.py` is the evidence-gated referral webhook: authenticated,
  idempotent, and it **stops** at INPUT_VALIDATED — provider status
  is forced to UNVERIFIED server-side, no assessment runs, no
  financing or auction step executes. A macro signal proposes; it
  never triggers.
- On the email underwrite surface, ANRD is **disabled** (the
  2026-11-10 scope narrowing: UZE Underwrite is HiCRE only). An
  ANRD-subject email receives a 422 with a polite referral message
  before any routing. GIRA's mock fixture still exists in the
  gateway's data table but is unreachable through the endpoint.

---

## Real vs. mock — the ledger

**Real:** subject/use-case/direction routing with its precedence
rules; the chart-of-accounts normalization and its unmapped
discipline; the bucket-level NOI derivation, fluctuation flags, and
growth math; the valuation arithmetic; the PDF report generation;
the comps interface and its labelled-fallback behaviour; the test
suite pinning the taxonomy (the modules above ship inside the
300-test suite).

**Mock / synthetic / not built:** document extraction (no OCR —
attachment bytes counted, never read); both per-track financial
fixtures; every comp, STR metric, and trend figure (synthetic,
labelled in-payload); the cap rate as an input rather than a
market-derived figure; the placement alert (recorded, not sent);
the endpoint's authentication (demo scope, unauthenticated by
design).

**Open items for the analyst:** (1) the GPR→EGI and
departmental/undistributed chains do not exist — bucket-level only
(§2); (2) no Price/Unit vs Price/SqFt prioritization rule (§5).
Resolved the day this document was filed, on the owner's tap: the
post-interest "NOI" label (§3) and the missing vacancy-loss /
credit-loss variants (§1).

---

## 7. The three-tier engine (built later the same day)

After this analysis was filed, the owner unfroze the build on his
own tap and the three-tier engine was built in
`services/compose/src/underwrite_engine.py`, with the SURA analysis
directive in `agents.py` extended to match. Endpoints:
`POST /api/v1/underwrite/projection`, `/verify-projection`,
`/valuation`, `/anrd-valuation`. Ten new tests; the suite stands
at 312.

- **Tier 1 — Historicals.** §1–§3 of this document, plus
  plain-language per-bucket trends for the most recent
  year-over-year step ("Insurance(s) costs have risen 50.0%
  year-over-year").
- **Tier 2 — Projections.** `generate_projection()` rolls the
  latest historical year forward 12 months. Default growth per
  bucket is that bucket's most recent historical YoY rate;
  revenue growth and per-bucket growth accept explicit overrides;
  known shocks (e.g. a tax reassessment) apply as labelled
  absolute adjustments after growth. **Every assumption is
  labelled by source in the output.** Projected NOI is unlevered;
  the post-interest figure is `projected_levered_cash_flow`. The
  projected cap rate is the underwriting cap rate plus an
  optional basis-point shift (default 0 — held, and labelled).
- **Tier 3 — Verification.** `verify_projection()` scores a
  projection against the actual that arrived for the same period:
  signed variance % and an accuracy score (100 − |variance %|,
  floored at 0). Within threshold: a Precedent Index event (+1)
  is returned. Beyond it: `UNDERWRITING_METHODOLOGY_FLAGGED` for
  the Juror Team. **The threshold is a policy default of 10%,
  set as a named constant and a per-call parameter** — the
  commissioning directive left it as "X%"; 10% is the shipped
  default, adjustable without code changes. Honest limits: the
  Precedent Index is a returned event record, not a persisted
  score, and the flag is a computed status — no live juror run is
  triggered by this module.
- **Tier 4 — Valuation.** `income_valuation()` takes the
  verified unlevered NOI by name; levered cash flow cannot be
  passed as the basis without misusing the API.
- **Tier 5 — ANRD (GIRA).** `gira_yield_valuation()`: net
  agricultural income (projected crop revenue − input costs)
  valued on an income multiple — **20× shipped as the labelled
  default** (`multiple_is_default` is stated in the output) —
  with a raw-acreage comp value alongside when acres and a
  per-acre price are supplied.

Still true after the unfreeze: extraction is mocked (§1), comps
are synthetic (§5), the GPR→EGI and departmental/undistributed
chains do not exist on the historical surfaces (§2 — but see
§8: the pro forma ingestion module implements the GPR→EGI
chain for its own format), and there is no
Price/Unit-vs-SqFt prioritization rule (§5).

## 8. The GPR→EGI chain now exists — for the pro forma format (2026-11-12)

`services/compose/src/proforma.py` (owner's unfreeze tap,
2026-11-12) ingests the institutional multifamily pro forma
format — the Graham Hill workbook (152 units, Mechanicsburg
PA) is the filed reference — and computes the full chain:
GPR → vacancy → credit loss → Net Rental Income → + other
income → EGI → itemized expenses → Replacement Reserve → NOI,
Years 1–5, with Year 1 run through a monthly lease-up. The
engine reproduces the workbook's own cached GPR/EGI/OpEx/NOI
for all five years to the cent (acceptance figures pinned in
`tests/test_proforma.py`; suite 319). Conventions: taxes and
insurance remain separate lines/buckets (the module also
reports the workbook's combined expense total so its NOI
reconciles); the Replacement Reserve follows the workbook —
its own line above NOI; valuation applies a cap-rate parameter
to Year 1 NOI (the workbook carries none). Endpoints:
`POST /api/v1/ingest/proforma` (base64 .xlsx),
`POST /api/v1/ingest/proforma/from-assumptions`,
`GET /api/v1/ingest/proforma/sample`. The email/historical
surfaces are unchanged — this chain serves pro forma
ingestion, not T-12 analysis.
