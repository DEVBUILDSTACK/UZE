# UZE Math Audit — For the Analyst

**Scope: the financial math and business logic only** — formulas,
the code that computes them, and the tests that pin them. No API
routing, no database schemas. Filed 2026-11-12. Every figure below
was produced by executing the code; every snippet is verbatim from
the source named beside it.

**One framing correction:** Scenario 3 of the commissioning brief
values the property "based on the projected NOI." The engine keeps
two values strictly separate: the income-approach valuation runs on
**verified historical NOI** (§3.1), and the projection emits its own
**projected implied value**, labelled as such (§2.3). They are never
the same field.

---

## Scenario 1 — Historical P&L & NOI derivation

### 1.1 From a T-12 to buckets

Raw line items `{label: amount}` are normalized by
`chart_of_accounts.normalize_line_items()` into the seven ratified
buckets. Matching is label-based (`bucket_for`): the label is
lowercased, punctuation-stripped and whitespace-collapsed, then
looked up in a filed variant table (spaced form, then squashed —
"R&M" → "rm"). Amounts sum per bucket; a label with no variant is
returned in `unmapped`, never guessed into a bucket.

### 1.2 The NOI formula — `email_gateway.analyze_multiyear()`

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

That is the entire derivation, and its shape is the audit answer:

- **NOI = Revenue − OpEx − Taxes − Insurance − Misc.** Taxes and
  Insurance are their own subtractions, never inside OpEx.
- **Interest is excluded from NOI by construction** — it appears
  exactly once, in the line below, producing the separately named
  `levered_cash_flow`. (Before 2026-11-12 the Interest subtraction
  sat inside the NOI expression; the analyst correction moved it
  out. The pre-fix behaviour is preserved in git history and in
  the test comment quoted below.)
- Filed Profit-bucket lines (a stated "NOI" or "Net Income" line
  in the T-12) are excluded from the derivation — no double-count.

**Test evidence** — `tests/test_email_gateway.py`:

```python
def test_multiyear_noi_is_unlevered_and_levered_figure_is_separate():
    # Rental 1,000,000; R&M 120,000; Taxes 90,000; Insurance 40,000;
    # Interest Expense 150,000
    assert period["noi"] == 750000               # interest NOT subtracted
    assert period["levered_cash_flow"] == 600000  # NOI − interest
```

And at API level — `tests/test_underwrite_metrics.py`, on the filed
SURA multi-year fixture (which carries interest lines every year):

```
2024: NOI 652,300 · levered 612,100 · interest bucket 40,200
2026: NOI 673,600 · levered 634,200 · interest bucket 39,400
NOI growth (unlevered basis): +3.27%
```

Note what the pair proves: the values 612,100 / 634,200 are exactly
what the pre-fix code reported **as NOI**. They are the
post-interest figures; the corrected vocabulary puts them where
they belong.

Historical growth in the email valuation flow is computed as
trailing-12 NOI against the annualized 36-month base:
`(504,100 − 1,398,500/3) / (1,398,500/3) = +8.14%`.

### 1.3 Contra-revenue — vacancy & credit loss

They are Revenue deductions, filed as variants of the Revenue
bucket (`chart_of_accounts.py`):

```python
"vacancy loss": "Revenue",
"vacancy credit loss": "Revenue",
"credit loss": "Revenue",
"credit loss bad debt": "Revenue",
"bad debt": "Revenue",
"bad debt expense": "Revenue",
```

Amounts are filed as negatives and net against Revenue (the module
preserves the caller's sign convention). Test evidence —
`tests/test_chart_of_accounts.py`:

```python
def test_vacancy_and_credit_loss_are_contra_revenue():
    out = coa.normalize_line_items(
        {"Gross Potential Rent": 1000, "Vacancy Loss": -60, "Credit Loss": -15}
    )
    assert out["buckets"]["Revenue"] == 925   # netted, not expensed
    assert out["unmapped"] == []
```

The taxonomy guard behind all of the above —
`test_taxes_insurance_interest_never_land_in_opex` — iterates every
filed tax/insurance/interest label and asserts its bucket; the
suite fails if any variant ever maps into Operating Expenses.

---

## Scenario 2 — Forward projections (pro forma)

### 2.1 The growth logic — `underwrite_engine.generate_projection()`

The projection rolls the **latest historical year's buckets**
forward 12 months. Each bucket's growth rate is resolved in this
exact precedence:

```python
if bucket in overrides:
    rate = overrides[bucket];            source = "explicit override"
elif prior is not None:
    rate = _pct_change(prior[bucket], base) or 0.0
    source = "historical latest YoY"     # the bucket's own last YoY step
else:
    rate = 0.0;                          source = "single-period history — held flat"

value = base * (1 + rate)
if bucket in shocks:                     # known adjustments, after growth
    value += shocks[bucket]              # e.g. Taxes +20,000 reassessment
```

**The defaults, answering the brief's question directly:** not a
flat percentage, and not micro-market comps. The shipped default is
**per-bucket historical inflation** — each bucket grows at its own
most recent year-over-year rate (an insurance line that rose 50%
projects at +50%; a flat interest line projects flat). Market-trend
sourcing (the comps layer's rent-growth figure) is a logged
post-recording refinement; today a market view enters only as an
explicit override, and every rate's source is printed in the
output's `assumptions` list.

### 2.2 Projected NOI

```python
projected_noi = (projected["Revenue"]
    - projected["Operating Expenses"]
    - projected["Taxes"]
    - projected["Insurance(s)"]
    - projected["Miscellaneous Net Expenses/Income"])
projected_levered = projected_noi - projected["Interest Expense/Income"]
projected_cap_rate = cap_rate + cap_rate_shift_bps / 10000   # default shift: 0
```

Same unlevered discipline as §1.2 — interest exists only in the
levered line.

### 2.3 Worked example (from `tests/test_underwrite_engine.py`)

Basis year (2025): Revenue 1,100,000 · OpEx 110,000 · Taxes 88,000 ·
Insurance 60,000 · Interest 100,000 — each grown at its 2024→2025
rate (+10% / +10% / +10% / +50% / 0%):

```
projected Revenue 1,210,000 · OpEx 121,000 · Taxes 96,800
projected Insurance 90,000 · Interest 100,000
projected NOI (unlevered)      = 902,200
projected levered cash flow    = 802,200
projected implied value @5.5%  = 902,200 / 0.055 = 16,403,636.36
```

With a +20,000 Taxes shock and a +5% revenue override instead:
Revenue 1,155,000, Taxes 116,800, projected NOI **827,200** — the
shock flows through NOI in full, labelled.

### 2.4 Verification (the math that closes the loop)

```python
variance_pct   = (actual_noi − projected_noi) / |projected_noi| × 100
accuracy_score = max(0, 100 − |variance_pct|)
within         = |variance_pct| ≤ threshold_pct      # default 10%
```

Example: projected 902,200 vs actual 880,000 → variance −2.46%,
accuracy 97.54, within threshold. Vs actual 700,000 → −22.41%,
flagged. (Both pinned in tests.)

---

## Scenario 3 — Valuation & comps

### 3.1 The income approach — `underwrite_engine.income_valuation()`

```python
def income_valuation(verified_noi: float, cap_rate: float) -> dict:
    if cap_rate <= 0:
        raise ValueError("cap_rate must be positive")
    return {
        "noi_basis": "verified_unlevered",
        "verified_noi": verified_noi,
        "cap_rate": cap_rate,
        "implied_value": round(verified_noi / cap_rate, 2),
    }
```

The basis is the verified **historical** unlevered NOI, taken by
parameter name. Fixture: 504,100 / 0.055 = **$9,165,454.55**.

### 3.2 Price per Unit / Price per Sq Ft — `email_gateway.extract_mock_data()`

```python
asking = data.get("askingPrice")
if asking and data.get("units"):
    data["pricePerUnit"] = round(asking / data["units"], 2)
if asking and data.get("grossLeasableAreaSqFt"):
    data["pricePerSqFt"] = round(asking / data["grossLeasableAreaSqFt"], 2)
```

Both are computed whenever their inputs exist — there is no
asset-class prioritization between them. Fixture (asking
$9,400,000; 128 units; 96,400 sq ft GLA): **$73,437.50 per unit**,
**$97.51 per sq ft**.

### 3.3 The comps payload — `costar.py`, parsed by the flow

The underwriting flow consumes comps through the
`ICoStarProvider` protocol (`sales_comps` /
`hospitality_metrics` / `market_trends` per micro-region). The
served implementation is the mock; one verbatim comp from its
Baltimore-Washington set:

```json
{
  "asset": "Select-service hotel, Baltimore Inner Harbor",
  "units": 142,
  "sale_price_usd": 13200000,
  "price_per_unit_usd": 92958,
  "price_per_sqft_usd": 141.20,
  "cap_rate": 0.0575,
  "sold": "2026-06"
}
```

Every response is wrapped in an envelope the flow reads before
the data:

```json
{"provider": "costar-shaped-mock", "synthetic": true,
 "license_note": "CoStar-shaped adapter, built to the interface,
 license pending. Figures are SYNTHETIC demo data — not CoStar data.",
 "micro_region": "baltimore-washington", "fallback_region": false}
```

Benchmarking, as the math consumes it: the subject's cap rate,
price/unit and price/sq ft (§3.1–3.2) are read against the comp
set's stored `cap_rate`, `price_per_unit_usd` and
`price_per_sqft_usd` fields and the region's `cap_rate_band`
([5.25%, 6.00%] in the synthetic set), plus STR-shaped metrics
(occupancy 0.684, ADR $158.40, RevPAR $108.35) for hospitality.
The comp figures are fixture values, labelled synthetic in every
payload — benchmarking logic is real, benchmark data is not, and
the envelope is how the code keeps those two facts inseparable.
