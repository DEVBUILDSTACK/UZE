# Affiliate Onboarding — as built (2026-11-13)

Owner tap, 2026-11-13 (James's own words): build the
integration of affiliates **as their onboarding** at Hack
launch. This document records what was built, in the
platform's honest-status style.

## The schema 🟢 BUILT

`services/compose/src/affiliate_profile.py` —
`validate_affiliate_profile` / `record_affiliate_profile` /
`order_affiliates`. An affiliate onboards by declaring:

- `name` + `slug` (slug derived from the name when not
  supplied; must be URL-safe).
- `creative_services.visualization` ⊆ DRONE ·
  MOTION_GRAPHICS · 3D_RENDER.
- `software_development.app_types` ⊆ BOOKING_ENGINE ·
  TENANT_PORTAL · CRM_FRONTEND · PROPERTY_DASHBOARD, plus a
  free-text `stack_preference`.
- `portfolio`: `media_assets` (URLs — drone video, 3D
  renders, interior photos), `historical_projects`
  ({project_name, location, year, asset_type}), `awards`
  ({award_name, year, organization}), `specialties`.
- `sponsorship_status` (boolean, default false). Its ONLY
  effect is directory ordering: sponsored first
  (`order_affiliates`).

Validation refuses and names every bad field by path
(e.g. `portfolio.historical_projects[0]`); nothing is
completed by guessing. Storage is the v1 pattern —
append-only JSONL (env `AFFILIATE_PROFILES_PATH`); a
database table is a later migration.

**There is no Entity or Affiliate database table.** Five
relayed directives presupposed one; each was corrected on
the record. If multi-tenant affiliate data ever needs a
real table, it is designed then, with an Alembic migration
proven by the from-empty replay standard.

## White-label pages 🟡 BUILT AS DEMONSTRATION

- `/affiliates` — the directory, sponsored first, clearly
  labelled a demonstration directory.
- `/affiliates/[slug]` — the firm's agency page inside
  UZEmarkets: portfolio, services, hire CTA ("Hire this Firm
  for your next Development" / "Request a Consultation"),
  and JSON-LD (`ProfessionalService` + `Person`) so agent
  crawlers can cite the portfolio.

Two deliberate deviations from the relayed design, with
reasons:

1. **Not a root `/[affiliate_slug]` route.** A root catch-all
   collides with every platform surface (talent, underwrite,
   alpha…) and contradicts the owner's tenant topology —
   tenant instances are cloned containers under a separate
   account pairing, not slugs on the core domain.
2. **Fixtures are invented firms, labelled as such.** Real
   pages render from onboarding records once the compose API
   is publicly deployed (the Render step on the owner's
   log) — the same dependency the alpha intake carries. The
   client never fakes a live record.

Positioning rule (owner correction, 2026-11-13): no
affiliate badging or prominent naming on public surfaces.
Capabilities are embedded in the taxonomy; generic titles
("Creative Intelligence Agency", "Institutional Software
Partner") are the public language. Written names in
internal documents are exact: Learn2Launch, Decensat
Design, Decensat.org — "Decent" is a spoken pronunciation
of Decensat for TTS, never a written name.

## The Development Stack page 🟢 BUILT

`/development-stack` — the turnkey offer in four parts:
(1) Architecture & execution (project team + project side
roster, lifecycle stages), (2) Visualization under the
generic Creative Intelligence Agency title, (3) Software
under the generic Institutional Software Partner title,
(4) Compute rental tiers. CTA: "Launch Your Full Project
Stack" → affiliate onboarding (/alpha).

## Compute rental 🟡 SHAPE ONLY

Tiers are Day · Week · Month · Quarter, presented on
/development-stack with **no checkout and no prices**
(participation is market-bid; public pages carry no dollar
amounts). Container provisioning is NOT built: the
time-based NEAR AI Cloud container model remains the
session-lifecycle proposal's territory, the NEAR AI org
balance is $0, and x402's authorization verifier in this
codebase is a labelled mock. When the program opens,
billing runs on the metered rails; until then the page
routes to onboarding. Nothing on the surface claims
otherwise.

## Future tech (documented, not built)

The document parser will eventually ingest CAD files to
generate visualizations automatically — feeding the same
visualization categories (DRONE · MOTION_GRAPHICS ·
3D_RENDER) the creative taxonomy already carries. Today
the gateway parses spreadsheets and TalentProfile JSON;
it ingests no CAD and no document text, and PDF/Word resume
parsing remains deferred to the January 2nd update.
