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
  Addendum A governs: mandatory for A and R; D requires the polygon
  (§2) but not the context. Flagged for DeepSeek correction if the
  intent was A/D/R.
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
