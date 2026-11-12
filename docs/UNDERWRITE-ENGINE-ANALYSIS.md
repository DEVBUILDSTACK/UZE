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
- **Known gap for the analyst:** the variant table has no
  vacancy-loss or credit-loss labels today. A T-12 filing those lines
  would return them as `unmapped` — surfaced, not lost, but not yet
  bucketed.

---

## 2. The P&L computation — what the code actually derives

There is one derivation, in `analyze_multiyear()`, applied per year
after normalization:

```
derived NOI  =  Revenue
              − Operating Expenses
              − Taxes
              − Insurance(s)
              − Interest Expense/Income
              − Miscellaneous Net Expenses/Income
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

Derived: NOI 600,000 (2024) → 645,000 (2025); growth **+7.5%**;
flags raised on Operating Expenses (+25%) and Insurance (+50%).

The email-gateway SURA fixture, for reference (hotel, trailing 12):
Revenue 1,842,500 − OpEx 1,093,800 − Taxes 148,200 − Insurance 96,400
= **NOI 504,100** (margin 27.4%). It carries no interest or
miscellaneous lines.

---

## 3. The NOI & Interest rule — stated exactly, with one open item

What the code guarantees:

- Interest can never land **inside** Operating Expenses — the variant
  table routes it to its own bucket, and the test named in §1 pins
  all three families (taxes, insurance, interest) out of OpEx.
- The juror layer enforces the same discipline on claims:
  `juror.py`'s system prompt instructs the judge to categorize every
  disputed figure into exactly one bucket and to "never judge taxes,
  insurance, or interest as if they were operating expenses," judging
  taxes and insurance only against the claim's own micro-region.

**Open item — flagged for the analyst's ruling, not papered over:**
in the §2 derivation, the Interest bucket is one of the subtractions
*on the way to* the figure the code labels `noi`. So when a filing
carries an interest line, the derived figure is **post-interest**
(levered), despite the NOI label. In the worked example: pre-interest
the property derives 750,000; the endpoint reports 600,000. The
email fixture is unaffected (it files no interest line, so its
504,100 is unlevered as presented). The fix is small — report both a
pre-interest NOI and a post-interest levered figure, or rename the
output — but it changes the API's vocabulary, so it waits for the
analyst's word.

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

**Open items for the analyst:** (1) the post-interest "NOI" label in
the multi-year derivation (§3); (2) vacancy-loss / credit-loss
variants absent from the chart of accounts (§1); (3) the GPR→EGI and
departmental/undistributed chains do not exist — bucket-level only
(§2); (4) no Price/Unit vs Price/SqFt prioritization rule (§5).
