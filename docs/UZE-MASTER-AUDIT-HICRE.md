# UZE Master Audit — The HiCRE Solution

**The definitive HiCRE document.** Part 1 is the business
explainer for the analyst. Part 2 answers the three scenarios
with the math. Part 3 is the code-stack audit for the lead
engineer. Filed 2026-11-12 · suite **327 passed** ·
documentation only.

**Corrections carried in this audit:** the commissioning brief
named modules that do not exist (`universal_parser.py`,
`sura_engine.py`) — Part 3 maps the real stack. Its Scenario 1
formula chain merges two distinct ingestion paths; they are
kept distinct below, because they are distinct in the code.
And the cross-format identity test covers xlsx/xls/csv
directly; the Google Sheets path joins the identical pipeline
at the xlsx-byte stage and is pinned by mocked-fetch tests —
stated precisely in §3.4, not inflated.

---

# Part 1 — The Business Explainer

## The problem

CRE underwriting still begins with manual re-keying. T-12s and
pro formas arrive as PDFs, legacy spreadsheets, CSV exports
and shared-sheet links, every operator labelling the same cost
a different way. The failure modes are structural: taxes and
insurance folded into operating expenses, corrupting every
micro-region benchmark (taxes are the largest driver of
micro-market variability); interest subtracted on the way to
NOI, producing a levered figure under an unlevered label —
fatal in a financing conversation; formats refused because a
tool only reads one of them; and projections never scored
against the actuals that later arrive, so underwriting quality
is anecdote.

## The solution

**UZE Underwrite** replaces that with autonomous ingestion and
one disciplined math core. The **Universal Parser** accepts
the file the analyst actually has — .xlsx, .xlsm, legacy .xls,
CSV, or a link-shared Google Sheet — and normalizes it into a
single assumptions structure, reporting what it defaulted,
what it didn't recognize, and what looks off, rather than
failing silently or guessing. **SURA**, the HiCRE agent
(hotels, multifamily, residential rental/condo,
hospitality/resort), standardizes historicals into the
ratified taxonomy, derives the baseline, projects forward with
labelled assumptions, verifies projections when actuals land,
and values on the income approach. Weeks of manual assembly
become one verified pass — with the honesty labels intact:
email-surface document extraction is a labelled mock, comps
are a synthetic CoStar-shaped adapter (license pending), and
the engines say so in their own outputs.

## The taxonomy — and the one rule that matters most

Every line maps to exactly one of seven buckets: **Revenue ·
Operating Expenses · Taxes · Insurance(s) · Interest
Expense/Income · Miscellaneous Net Expenses/Income · Profit
(Net Income)**. Operating Expenses never absorb Taxes,
Insurance, or Interest. And:

> **NOI is unlevered.** NOI = Revenue − Operating Expenses −
> Taxes − Insurance(s) − Miscellaneous Net. Interest is
> subtracted only afterwards, into a separately named figure:
> **levered cash flow**.

An unknown label is returned *unmapped* for human review —
never guessed into a bucket.

---

# Part 2 — The Three Scenarios

## Scenario 1 — Historical ingestion & baseline

Two ingestion paths, both ending at the same unlevered NOI
discipline:

**Path A — historicals (T-12s, multi-year statements).**
Structured years of line items are normalized by the Standard
Chart of Accounts (§3.3) and derived bucket-by-bucket:

```
NOI (unlevered)   = Revenue − OpEx − Taxes − Insurance − Misc
levered cash flow = NOI − Interest
```

On the filed SURA fixture: NOI 652,300 → 673,600 across the
two latest years (+3.27% unlevered growth), levered 612,100 →
634,200 — the pair that proves the vocabulary is honest,
because those levered figures are exactly what a pre-correction
version of this engine once mislabelled as NOI. Vacancy and
credit loss net against Revenue as contra-revenue; buckets
moving >15% YoY are flagged for line-item review.

**Path B — the institutional pro forma (the Universal
Parser).** A workbook's assumptions drive the full chain:

```
GPR → − Vacancy → − Credit Loss → Net Rental Income
    → + Other Income → EGI → − Itemized Expenses
    → − Replacement Reserve → NOI
```

**The Graham Hill proof** (152 units, Mechanicsburg PA;
workbook's own cached values as the standard): Year 1 GPR
3,340,080 (monthly lease-up) − vacancy 197,767.89 − credit
loss 23,567.34 + other income 169,455 = **EGI 3,288,199.76**;
expenses 1,310,085.99 (Taxes 245,480 and Insurance 116,280 as
their own lines — OpEx excluding both: 948,325.99) − reserve
30,400 → **NOI $1,947,713.77, to the cent.**

Formats: the same file as .xlsx, .xls, or .csv produces
identical output (§3.4); a Google Sheets link enters as its
xlsx export. A raw T-12 CSV (line items × months) is Path A
input via the multiyear endpoint, not a pro forma — the shapes
are different and the engine does not pretend otherwise.

## Scenario 2 — Forward projections (pro forma)

Two instruments. The **pro forma engine** builds the 5-year
statement from the workbook's own growth assumptions —
Graham Hill: rents +3%/yr, expenses +3%/yr, management fee
re-struck at 3% of each year's EGI, reserve escalating
$200→$400/unit:

| Year | EGI | Total OpEx | Reserve | **NOI** |
|---|---|---|---|---|
| 1 | 3,288,199.76 | 1,310,085.99 | 30,400 | **1,947,713.77** |
| 2 | 3,418,877.37 | 1,350,349.52 | 38,000 | **2,030,527.85** |
| 3 | 3,521,443.69 | 1,390,860.01 | 45,600 | **2,084,983.68** |
| 4 | 3,627,087.00 | 1,432,585.81 | 53,200 | **2,141,301.19** |
| 5 | 3,735,899.61 | 1,475,563.38 | 60,800 | **2,199,536.23** |

The **Tier 2 projection** works from a property's own
historicals instead: each bucket grows at its own latest YoY
rate (per-bucket historical inflation), with explicit
overrides and known shocks labelled by source. **Tier 3**
then verifies: when actuals file, variance against the
projection is scored — within the 10% default threshold the
underwriter earns Precedent Index standing; beyond it, the
methodology is flagged for the Juror Team.

## Scenario 3 — Valuation

```
Implied Value = Verified Unlevered NOI / Cap Rate
```

The historical engine takes the verified NOI by parameter
name (levered cash flow cannot be passed as the basis); the
pro forma engine values on Year 1 NOI with the cap rate as an
explicit parameter — Graham Hill at the labelled 5.5% mock
default: **1,947,713.77 / 0.055 = $35,412,977.66**, and
**Price per Unit = $232,980.12** (÷ 152). Price per Square
Foot is computed alongside whenever GLA is known; both are
read against micro-region comps from the CoStar-shaped
adapter, every payload labelled synthetic until the license
lands.

---

# Part 3 — The Code Stack (for the lead engineer's audit)

## 3.1 The real module map

All under `services/compose/src/`, one FastAPI app (`app.py`):

| Module | Role |
|---|---|
| `proforma.py` | The Universal Parser + pro forma engine (GPR→EGI chain, lease-up, 5-yr NOI, valuation) |
| `chart_of_accounts.py` | The Standard Chart of Accounts — the 7-bucket taxonomy and label variants |
| `email_gateway.py` | Ingestion surfaces: email routing (incl. spreadsheet detection), mock extraction, `analyze_multiyear` (Path A math), PDF reports |
| `underwrite_engine.py` | Tier 2 projection · Tier 3 verification · Tier 4 income valuation · Tier 5 GIRA yield valuation |
| `agents.py` | Track routing (SURA→HiCRE, GIRA→ANRD) + the SURA analysis directive |
| `juror.py` | The Juror Team prompt surface — enforces bucket discipline in review |
| `costar.py` | CoStar-shaped comps adapter (synthetic, labelled) |
| `agtech.py` | ANRD evidence-gated intake (stops at INPUT_VALIDATED) |

There is no `universal_parser.py` or `sura_engine.py`; SURA is
a routing + directive role across these modules, not a file.

## 3.2 The Universal Parser — without pandas

Format normalization is a grid layer in `proforma.py`. pandas
was evaluated and deliberately not adopted: its `read_excel`
sits on openpyxl/xlrd anyway; direct grids are lighter and
sufficient.

```python
def detect_format(data: bytes) -> str | None:
    """'xlsx' (also .xlsm — same container), 'xls', 'csv', or None."""
    if data[:4] == b"PK\x03\x04":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                if "xl/workbook.xml" in zf.namelist():
                    return "xlsx"
        except Exception:
            return None
        return None
    if data[:8] == _OLE2_MAGIC:            # legacy .xls container
        return "xls"
    # ... text that carries the assumptions labels -> "csv"
```

Each format becomes grids — `_grids_from_openpyxl`,
`_grids_from_xlrd`, `_grid_from_csv` (delimiter sniffing,
utf-8-sig/latin-1 fallback) — and **one** extractor
(`_extract`) consumes them, so the parse report (defaulted /
unmapped / warnings) and the math cannot diverge by format.
Google Sheets is a guarded fetch, never arbitrary-URL:

```python
_SHEETS_URL_RE = re.compile(
    r"^https://docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]+)(?:[/?#].*)?$"
)

def google_sheet_export_url(url: str) -> str:
    m = _SHEETS_URL_RE.match((url or "").strip())
    if not m:
        raise ValueError("not a Google Sheets URL — expected https://docs.google.com/spreadsheets/d/...")
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=xlsx"
```

The fetch enforces a 15 s timeout and the 10 MB cap, and an
HTML response (Google's login page for a private sheet) is
detected and reported as *"not shared as 'anyone with the
link'"* — never parsed.

## 3.3 The SURA math — taxonomy and unlevered NOI

Taxonomy enforcement lives in `chart_of_accounts.py`
(label-variant table; unmapped labels returned, never guessed)
and is pinned by a test that iterates **every** filed
tax/insurance/interest label and asserts its bucket. The NOI
derivation, verbatim from `email_gateway.analyze_multiyear`:

```python
noi = (
    b["Revenue"]
    - b["Operating Expenses"]
    - b["Taxes"]
    - b["Insurance(s)"]
    - b["Miscellaneous Net Expenses/Income"]
)
levered_cash_flow = noi - b["Interest Expense/Income"]
```

## 3.4 The test suite — 327 passed

Full suite at filing: **327 passed** (services/compose). The
pins that carry this document's claims:

*Graham Hill / pro forma* (`tests/test_proforma.py`, 15 tests):
`test_graham_hill_all_five_years_match_the_workbook` ·
`test_year1_flows_through_lease_up_not_stabilized_vacancy` ·
`test_taxes_and_insurance_stay_out_of_opex_in_the_uze_view` ·
`test_valuation_applies_cap_rate_to_year1_noi` ·
`test_all_formats_produce_identical_math` (the same
assumptions as .xlsx, .xls and .csv → byte-identical computed
output) · `test_detect_format` · `test_google_sheets_url_rules`
· `test_google_sheets_fetch_paths` (Sheets enters as xlsx bytes
via a mocked fetch — link-shared success, HTML-login refusal,
non-Google rejection) · `test_blind_hardening_messy_workbook_reports_and_parses`
· `test_blind_missing_required_lists_everything_missing` ·
`test_gateway_routes_xlsx_attachments_to_the_parser` ·
`test_gateway_routes_xls_and_csv_too` ·
`test_parser_reads_the_four_sheet_structure` ·
`test_parser_rejects_a_non_workbook` ·
`test_api_sample_and_file_ingest`.

*Historical engine*: `test_multiyear_noi_is_unlevered_and_levered_figure_is_separate`
· `test_taxes_insurance_interest_never_land_in_opex` ·
`test_vacancy_and_credit_loss_are_contra_revenue` ·
`test_multiyear_normalization_growth_and_flags`.

*Endpoints*: `POST /api/v1/ingest/proforma` (base64 file or
`source_url`) · `POST /api/v1/ingest/proforma/from-assumptions`
· `GET /api/v1/ingest/proforma/sample` ·
`POST /api/v1/ingest/email` (spreadsheet attachments route to
the parser before subject routing) ·
`POST /api/v1/ingest/multiyear` ·
`POST /api/v1/underwrite/{projection,verify-projection,valuation,anrd-valuation}`.
