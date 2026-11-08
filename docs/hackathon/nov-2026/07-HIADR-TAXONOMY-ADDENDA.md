<!--
  Filed 2026-11-08. Source: DeepSeek scope package relayed by James
  ("Please implement from DeepSeek"), adopted by James as finalized
  ("James has finalized the HIADR taxonomy and the Content Desk
  strategy"). Addenda A and B are DeepSeek's text, condensed only in
  formatting. The Conformance notes at the end are SoSem's: where
  the package's generic scaffold sketches differed from the filed
  repo record, the filed record governed (05-HOW-TO-USE-DIAGRAMS
  rule, applied to specs).
-->

# HIADR Taxonomy & Content Desk — Scope Package (2026-11-08)

**Scope directive.** UZEMARKETS expands from a single-vertical CRE
marketplace to a multi-asset spatial finance engine. The taxonomy
is HIADR (Hospitality, Income, Agriculture, Development,
Resource). Three executions: (1) extend the schema per Addendum A;
(2) update the narrative per Addendum B; (3) return to the critical
path (Day 3 settle, Day 4 inference). Do NOT build the Content Desk
bot yet; do NOT build the spatial APIs yet.

## Addendum A — Schema Extension Specification

Rule: additive only; from-empty replay required.

1. **Taxonomy enum.** `AssetSubclass`: H (Hospitality — resorts,
   hotels) · I (Income — multifamily, residential, condos) · A
   (Agriculture — farms, agricultural raw land) · D (Development —
   industrial, data centers, raw land) · R (Resource —
   subterranean exploration/extraction). (Replaces the earlier
   asset_taxonomy_class notion.)
2. **Spatial constraints (target_area).** H and I (operating CRE):
   a 37.5-mile radius (epicenter_lat, epicenter_lng) OR a GeoJSON
   polygon. A, D, R (raw land): a GeoJSON polygon is required;
   radius is invalid for these tracks.
3. **Subterranean & resource context.** New JSON column on Intent,
   `subterranean_context`: soil_analysis_depth_meters,
   resource_types [soil, mineral, oil_gas, carbon, water],
   water_source (ground_level | subterranean_aquifer |
   surface_riparian | none), water_rights_owner (landowner |
   government | split | unknown), jurisdiction (e.g. BR, US-TX,
   US-CA). "If asset_subclass is R or A, this field is mandatory
   for the data science pipeline. The system uses jurisdiction to
   apply the correct legal split (e.g., Brazil's 50/50 mineral
   split)."
4. **Content Desk data layer.** New JSON column on MicroRegion,
   `pulse_data`: prior_period_30d, prior_period_90d, lookback_18m,
   lookback_36m.

Also specified: `GET /api/v1/micro-regions/{id}/pulse` returning a
schema.org Dataset ("{Region} HiCRE Pulse", temporalCoverage,
variableMeasured, `agent_action: "POST /api/v1/specs to initiate
underwriting"`).

## Addendum B — Executive Summary & the HIADR Content Desk

UZEmarkets is a multi-asset capital markets engine in the HIADR
taxonomy. H & I: operating assets, micro-region expense analysis.
A & D: raw land, polygon spatial underwriting (soil, zoning,
financing). R: subterranean assets, subsurface rights and
geological analysis (water, minerals, oil/gas). **Financing link:**
HI routes to operating lenders; AD routes to land/development
funds; R routes to resource extraction financiers.

**The HIADR Content Desk** is the organic growth engine: a
dual-surface data science engine generating continuous market
intelligence for X.com and UZEmarkets.com. Format: a
human-readable financial analysis followed immediately by a
machine-readable JSON payload at the bottom of the post. GEO play:
an AI crawler ingesting the post receives the JSON block with the
exact x402/API endpoints to transact. Cadence: daily (7×/week)
micro-region financial metrics; weekly Sunday blog deep-dive
spatial analysis; weekly Tuesday post distilling the blog into a
data-rich X thread with the JSON hook.

## Conformance notes (SoSem, 2026-11-08)

- **Paths/structure:** the package's stack sketch (services/compose/
  api/, apps/web, migrations/) is a generic scaffold. The filed repo
  governs: services/compose/src/, apps/uze-web, alembic/versions/.
  No restructuring was done.
- **Schema form:** the sketch's fresh `intents`/`micro_regions`
  tables, Numeric budgets, and string statuses conflict with the
  filed compose schema (existing `intent`/`micro_region` tables,
  BigInteger USDC, typed enums). Addendum A was implemented
  additively onto the filed schema, per its own rule: migration
  `851420c2adc4` adds the `asset_subclass` enum, intent
  `assetSubclass` / `targetArea` / `subterraneanContext`, and
  micro_region `pulseData` — all nullable; no existing column or
  table changed. (There was no pre-existing `asset_taxonomy_class`
  in the filed schema to replace.)
- **Subterranean scope:** Addendum A §3 mandates the context for
  **R and A**; the stack sketch's schema comment said A/D/R.
  Addendum A governed the first implementation (A and R; D polygon
  only). **RESOLVED by DeepSeek 2026-11-08: mandatory for A, D and
  R** — a data center (D) requires water rights for cooling and
  soil/bedrock analysis for foundations, so D cannot be
  underwritten without the subterranean layer. Implemented the
  same day (one-line change in the ingestion validator + tests).
- **targetArea shape:** GeoJSON Polygon at the top level
  ({"type": "Polygon", "coordinates": [...]}) per the stack spec's
  own API payload example; radius form is {"type": "Radius",
  epicenterLat, epicenterLng, radiusMiles}. The addendum's phrase
  "target_area.polygon_params" was read as referring to this
  polygon requirement, not a nested key.
- **JSON vs JSONB:** the filed schema's free-form columns use
  SQLAlchemy JSON; the new columns match that precedent.
- **Not built (per the directive's own exclusions):** the Content
  Desk bot/publisher, services/content_desk, the data-science
  router and spatial agent, financing-linkage routing. The pulse
  endpoint serves measured variables computed from real records
  (spec count, comparable count, settled volume) — the sketch's
  example figures were illustrative and are never served as data.


---

## Paraguay extension + data-science routing (2026-11-08, DeepSeek directive)

Strategic extension relayed by James: the AgTech/land pilot
extends to **Paraguay** (macro distress following the Ueno bank
collapse — the corroborated event in our record, 2026-11-05), and
the schema must support **dynamic country extension on demand**.

**Conformance note:** the directive names
`operational_optimization_context` and `rwa_monetization_context`
as the carriers for these fields. Neither object exists in the
filed schema and no AgTech referral pilot structure is on record,
so the fields land in the filed shapes instead of inventing two
new context objects: `countryCode` and `macroDistressExit` are
**Intent-level** (migration `85fe8850a6f9`), and the subterranean
context's `jurisdiction` carries "PY" like any jurisdiction value.

**Shipped (schema):**
- `countryCode` — enum {BR, PY, UY, US}. New markets arrive as
  enum members, not schema changes (the dynamic-extension rule).
- `macroDistressExit` — boolean. The dual-track flag: the owner
  is optimizing the asset (the Hold) while preparing its
  liquidation route (the Exit).

**Filed as spec, NOT built (routing):** the data-science router
remains excluded per the HIADR directive's own sequencing; these
rules are its specification when it is built (Sprint 2):
- An agriculture intent with `countryCode == "PY"` routes its
  polygon to AgTech partner yield optimization (partner API
  integration — Effatha named in the directive as the example
  partner; no integration exists yet, partner onboarding is a
  business step, not a schema step).
- An intent flagged `macroDistressExit` in a distressed market
  (PY today) is simultaneously tagged for the exit route:
  `executionEnvironment = ARCIUM_AUCTION` (the tag shipped in the
  trust-layer pass) — the Arcium sealed-bid auction pipeline that
  liquidates the land RWA into USDC on Solana, the capital
  migration route out of the distressed fiat.
- The two routes are not exclusive: the flag means both run —
  optimize to save the farm; keep the exit priced and ready.


---

## Diagram 05 mapping review (2026-11-08)

`docs/diagrams/05-agtech-cattle-stack.md` was saved verbatim as
directed. Per the diagram governance (05-HOW-TO-USE-DIAGRAMS),
diagrams are shared vocabulary, not the specification — the
review below maps each element to the filed system and names
every divergence rather than shipping one silently:

- **Distribution wedge / webhook** (`POST
  /api/v1/webhooks/agriculture/intent`, crop_type CORN/SORGHUM):
  not built. Ingestion today is `POST /api/v1/specs`. The webhook
  belongs to the partner/data-science layer the HIADR directive
  sequenced to Sprint 2; crop_type rides the intent's asset
  context conventions when that layer is built.
- **Agro Digital spatial engine:** our `targetArea` IS standard
  GeoJSON Polygon at the top level (filed in the HIADR pass) —
  CAR-mappable as the mapping requires. Their "6m soil" return
  aligns with `subterraneanContext.soil_analysis_depth_meters`
  (the filed example value is 6).
- **Effatha yield loop:** routing rules filed in the Paraguay
  section above; the partner integration itself is not built
  (no partner API exists to integrate against yet).
- **AI & tracking:** the NEAR AI inference module, the x402
  metering, and x401 all exist; x401 verification is now real in
  the Assurative trust layer (compose's local stub still serves
  the tier gate until the Sprint 2 swap to the trust call).
- **Capital split:** Path 1 (finance) is the filed financing
  linkage — design only. Path 2 (exit) is expressed by shipped
  fields: `macroDistressExit` + `executionEnvironment =
  ARCIUM_AUCTION`, settling in USDC on Solana over the shipped
  rail.
- **The named context objects**
  (`operational_optimization_context`, `rwa_monetization_context`):
  not separate objects in the filed schema, by design — every
  field they would carry already lives on the Intent
  (countryCode, macroDistressExit, subterraneanContext,
  executionEnvironment, targetArea). Splitting them out as
  parallel JSONB contexts would duplicate state the Intent
  already owns. If James/DeepSeek want the named objects as a
  partner-facing payload shape, that is a serialization view to
  add at the routing layer, not new storage — flagged for their
  call, not silently built.
