# INTENT SCHEMA — Draft (Sprint 1.5, Day 1)

**Status:** Draft, per `01-PICKUP-TONIGHT.md`. CRE-specific by design — not a generic talent marketplace schema.
**Consumed by:** Day 2 additive compose migration (`MicroRegion`, `Intent`, `Bid`, `Match`) and the Rust contract's typed structs (Day 2+; the Day 1 scaffold uses `String` JSON payloads).

```rust
Intent {
  kind: "availability" | "demand",
  poster_kind: "human" | "agent" | "internal_agent" | "partner",
  poster_account: AccountId,
  domain: "cre_expense_analysis" | "cre_property_management" |
          "cre_market_survey" | "cre_income_analysis",
  work_product: "operating_budget" | "pm_spec" | "cost_model" |
                "benchmark_analysis" | "placement",
  deliverable: JSON,
  micro_region_id: String,
  asset_context: {
    property_type: "branded_hotel" | "residential_rental" |
                   "residential_condo" | "hospitality" | "medical_recovery",
    door_count: Int,
    brand_affiliation: String?,
    acquisition_stage: "underwriting" | "post_close" | "operating"
  },
  on_site_days: Int?,
  remote_days: Int?,
  budget_min_usdc: U64,
  budget_max_usdc: U64,
  available_from: U64,
  available_until: U64,
  tier: "A" | "B" | "C" | "D" | "E" | "ANY",
  referring_partner: String?
}
```

## Notes

- `work_product` distinguishes the two service lines: `operating_budget` / `pm_spec` (Service Line 1 — Assessment and Advisory) from `placement` (Service Line 2 — Talent Placement). See `04-DECISIONS-LOG.md` D2.
- `micro_region_id` references the `MicroRegion` reference table (Day 2 migration). Micro-region is the analytical unit — see D3.
- Money fields are USDC amounts (`budget_min_usdc` / `budget_max_usdc` as U64). The USDC-only settlement invariant (af20ad9) is unchanged.
- Contract serialization rule (from `01-PICKUP-TONIGHT.md`): state uses Borsh; function inputs/outputs use JSON; u64/u128 cross the boundary as U64/U128 from `near_sdk::json_types`. The String-payload scaffold avoids this on Day 1 only.
- Lifecycle states this schema moves through are defined in `docs/diagrams/04-intent-lifecycle.md` (POSTED → BIDDING → SELECTED → SETTLING → SETTLED → DELIVERED; EXPIRED terminal; SETTLE_FAILED returns to SELECTED).
