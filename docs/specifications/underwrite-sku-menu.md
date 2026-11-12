# UZE Underwrite — The SKU Menu (Commercial Specification)

**Status: SPECIFICATION (owner tap, 2026-11-12).** The engine
beneath every SKU is the built UZE Underwrite engine (suite
green at filing). Each SKU carries its own build status —
a SKU marked 🔴 is a contract being specified, not a claim
that the computation exists.

**Pricing rule (ratified):** no static prices appear in any
public copy or in this menu. SKU prices are **market-bid via
UZEguidance priced markets** and are fetched from `llms.txt`
at read time, so an agent always sees the currently honored
price. **Comps rule:** every benchmark below is served by the
**CoStar-shaped synthetic adapter, license pending** — every
payload that carries comps labels them synthetic. **Payload
rule:** execution is **stateless by default** (documents are
supplied per call); `session_id` is an optional future
extension (see the session-lifecycle proposal). **Provenance
rule:** every SKU response includes a `provenance` block
citing the exact source lines each figure derives from.
**Error rule:** when a SKU cannot be computed from the
supplied documents, the response is `INSUFFICIENT_DATA` with
a JSON array of the missing field names — never a
hallucinated figure.

## The menu

| SKU | Report | Status | Engine surface |
|---|---|---|---|
| UZ-W-001 | Full T-12 Underwriting — seven-bucket P&L, unlevered NOI, per-unit metrics | 🟢 Built | `analyze_multiyear` |
| UZ-W-002 | Multi-Year Historical Baseline — YoY trends, >15% fluctuation flags, NOI growth | 🟢 Built | `analyze_multiyear` |
| UZ-W-003 | 12-Month Pro Forma — forward NOI on labelled growth assumptions | 🟡 Partial | pro forma engine (full GPR→EGI chain); Tier-2 bucket projection |
| UZ-W-004 | 5-Year Projection — five-year NOI table, custom or workbook growth | 🟢 Built | pro forma engine |
| UZ-W-005 | Rent Roll Audit — units, occupancy, loss-to-lease, charge-code rollup | 🔴 Proposed | no rent-roll parser exists yet; dialect proven by hand in the Westley blind test |
| UZ-W-006 | OpEx Benchmark — OpEx per unit vs micro-region comps (synthetic adapter) | 🟢 Built | buckets + `costar.py` |
| UZ-W-007 | Tax & Insurance Isolation — tax/ins as their own lines and % of revenue, benchmarked | 🟢 Built | buckets + `costar.py` |
| UZ-W-008 | Variance Analysis — actual vs budget, line-by-line with anomaly flags | 🔴 Proposed | Tier-3 scores projection-vs-actual; budget ingestion is not built |
| UZ-W-009 | Projection Verification — a filed projection scored against arrived actuals (variance %, accuracy score, precedent standing) | 🟢 Built | Tier 3 `verify_projection` |
| UZ-W-010 | Full Underwriting Package — every built SKU above in one bonded payload, one provenance block | 🟢 Built (of the built SKUs) | composition |

## Contract shape

```
POST /api/v1/underwrite/{sku}
{ "documents": [ ...per-call, stateless... ],
  "session_id": null  // optional future extension
}
→ 200 { sku, status, results, provenance: {figures → source lines},
        talent_placement: {...} }
→ 422 { "error": "INSUFFICIENT_DATA", "missing_fields": [ ... ] }
```

Every underwrite response also carries the `talent_placement`
bridge object — the operational roles the asset's payroll
already funds, with the placement CTA (Master Directive
Part 2; built 2026-11-12).
