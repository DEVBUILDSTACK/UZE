# UZE Analyze — Custom Analysis (Specification)

**Status: SPECIFICATION (owner tap, 2026-11-12).** The custom
tier covers what the SKU menu does not. It is specified here;
the endpoint is not yet built.

```
POST /api/v1/analyze/custom
{
  "documents": [ ...per-call, stateless... ],
  "session_id": null,               // optional future extension
  "question": "What is the property's exposure to a 200bp
               rate rise over the next 24 months?",
  "metrics_required": ["levered_cash_flow", "dscr",
                       "interest_coverage"],
  "comparison_basis": "micro_region_comps"
}
```

**The citation rule (non-negotiable):** every figure in a
custom response cites the source line items it derives from,
in the same provenance block the SKUs carry. A custom answer
without citations is a defect, not a style choice.

**The insufficiency rule:** when a requested metric cannot
be computed from the ingested data, the response is
`INSUFFICIENT_DATA` with the machine-readable array of
missing field names — so the requesting agent can fetch
exactly those inputs and retry. Worked example: `dscr`
requires debt service (interest **and** principal); the
engine ingests interest but not amortization, so a DSCR
request against a standard T-12 returns
`{"error": "INSUFFICIENT_DATA", "missing_fields":
["principal_payments"]}` — the guardrail working as designed.

**Pricing:** metered, market-bid via UZEguidance (no static
rates in public copy); the live rate is published in
`llms.txt` at read time.

**Comps:** any micro-region comparison is served by the
CoStar-shaped synthetic adapter, license pending, and is
labelled synthetic in the payload.
