# UZE Evaluate — The Valuation Product (Specification)

**Status: SPECIFICATION (owner tap, 2026-11-12).** The
valuation math is 🟢 built (Tier 4 `income_valuation`: implied
value = verified unlevered NOI / cap rate, with the NOI basis
labelled so a levered figure cannot be passed as the basis);
the single-purpose endpoint below is the specified product
surface.

```
POST /api/v1/evaluate
{
  "documents": [ ...per-call, stateless... ],   // or:
  "noi_source": "verified",     // engine-computed NOI from an
                                // ingested T-12 in this call
  "cap_rate": 0.055,
  "comps_source": "costar_mock" // the CoStar-shaped synthetic
                                // adapter, license pending
}
→ { implied_value, price_per_unit, price_per_sqft,
    noi_basis: "verified_unlevered", cap_rate,
    comps: { ..., synthetic: true },
    provenance: { ... } }
```

Rules: the NOI basis is always the **verified unlevered**
figure; price per unit and price per square foot are computed
whenever unit count / GLA are known and omitted (named in
`missing_fields`) when they are not — never estimated.
Pricing is flat per valuation, market-bid via UZEguidance,
published in `llms.txt` at read time; no static price appears
in public copy.
