# Talent Placement — Ingestion & Parsing Architecture

**Status: MIXED — the JSON path is 🟢 BUILT (2026-11-12);
the document-parsing layer is 🔴 PROPOSAL, deferred to the
January 2nd update by the owner's directive.** Creative
architecture input requested by the owner and provided by
SoSem, 2026-11-12. Scope label (ratified): human-talent/CV
claims sit outside the hackathon build; this document designs
the ingestion layer, it does not enroll it in the submission
narrative.

## One schema, two doors

Every talent — human or agent — lands in a single
**TalentProfile**:

```json
{
  "name": "string, required",
  "role": "string, required",
  "experience_years": "number ≥ 0, required",
  "skills": ["string, …], required, non-empty",
  "expected_rate_usd": "number > 0, required",
  "certifications": ["string, …"], optional"
}
```

**Taxonomy (built 2026-11-12, owner's supplemental tap):**
two optional fields separate who the employer is from what
the worker is — `asset_class_focus` (HOSPITALITY: hired by
organizations · RESIDENTIAL: hired by syndicates/owners) and
`talent_type` (HUMAN_EMPLOYEE · HUMAN_CONTRACTOR ·
AGENTIC_SERVICE). Optional so pre-taxonomy profiles stay
valid; strict when present. The matcher (`match_profiles`)
matches on role family (operations vs knowledge work, read
from the role), the role itself, and focus compatibility —
an unset focus serves any. The underwrite's
`talent_placement` object offers both paths: Operations
(the payroll's roles) and Knowledge Work (outsource the
asset's ongoing financial analysis).

**Door 1 — the agent (built).** An agentic talent submits
the JSON directly. The email gateway's talent track validates
it (`talent_profile.validate_profile`): valid profiles are
normalized and recorded (v1: append-only JSONL, the alpha
intake's pattern; a database table is a later migration);
invalid ones return `INSUFFICIENT_DATA` with the exact
missing/invalid field names. Nothing is inferred to complete
a profile.

**Door 2 — the human (deferred, designed here).** A human
uploads a PDF or Word resume. Today the gateway answers with
the clean deferral: *"PDF/Word resume parsing is deferred to
our January 2nd update. Please provide your resume in JSON
format."* The January design, in three stages:

1. **Text layer.** Extract text with a real PDF parser
   (pypdf/pdfplumber class). Note what does *not* work:
   openpyxl reads spreadsheets — it is the T-12 tool, not a
   document tool — and the gateway today extracts no document
   text at all. Scanned-image resumes would need OCR, a
   further step, separately labelled if ever added.
2. **Structuring.** The extracted text is structured into
   TalentProfile by the inference layer, with every field
   traced to the resume text it came from (the same
   provenance discipline as the underwrite). Fields the
   resume does not support are left empty — and the profile
   then fails validation with those fields named, exactly as
   a hand-written JSON would. The parser proposes; the schema
   disposes.
3. **Confirmation.** Because structuring is interpretive, a
   human-submitted profile is presented back for the talent's
   own confirmation before it is matchable. An agent's JSON
   needs no such step: it asserted the schema itself.

## Rate matching against the underwrite

The bridge (built): every underwrite response carries
`talent_placement` — the roles the asset's payroll lines
already fund, plus the asset's annual payroll budget derived
from those same lines. Matching is then arithmetic, not
vibes: a profile is *rate-compatible* with an asset when its
`expected_rate_usd` fits inside the payroll envelope for its
role, and *role-compatible* when its role is one the
underwrite named. Both checks run on validated data only;
a profile that failed validation matches nothing, and an
asset whose underwrite named no roles requests nothing.

## What this is not

Not an automated hiring system, not a credential verifier —
certifications are recorded as claimed, and any verification
regime (the later-phase credential work) bolts onto the
schema without changing it.

## Development, Design & Wellness taxonomy (built 2026-11-13)

Owner tap, 2026-11-13 (James's own override of recording
standby and the hackathon scope ruling). The D (Development)
side connects to H&I: a developer who secures land and builds
needs the project team that makes it a hospitality asset.

- **Two new OPTIONAL fields** on TalentProfile, validated
  strictly-when-present and stored canonical, exactly like
  `asset_class_focus` / `talent_type`: `role_category` ∈
  ARCHITECT · INTERIOR_DESIGNER ·
  LIGHTING_TECHNOLOGY_INTEGRATOR · WELLNESS_SPA_CONSULTANT ·
  CAD_DRAFTER · PRE_SALES_BROKER, and `domain_focus` ∈
  COMMERCIAL_ARCHITECTURE · LUXURY_RESIDENTIAL ·
  HOSPITALITY_RESORT_DESIGN · WELLNESS_INFRASTRUCTURE.
- **`role` stays free text.** No closed role enum was added —
  one would have invalidated every previously validated
  profile (Property Manager, General Manager, Financial
  Analyst are not project categories).
- **Matcher:** a third role family, `development_design`,
  recognized by declared `role_category` or by role text.
  `match_profiles` additionally accepts `role_category` and
  `domain_focus` on the need, with domain compatibility
  following the focus rule (unset serves any).
  `assemble_project_team(need, profiles)` returns matches
  grouped by category in standing team order, omitting
  categories the marketplace cannot staff.
- **Bridge:** `talent_placement.paths` gains a third entry,
  `development_design` — a standing offer (like knowledge
  work), not a payroll derivation; its roles are the
  platform's project team.
- **Referral edges (v1):** `validate_referral` /
  `record_referral` / `referral_chain` — an edge records who
  referred whom (with the referred profile's role category
  and an optional context ref), stored append-only JSONL
  like the profiles. An edge is a record, not a payout;
  referral economics remain the strategic audit's later
  sequencing.
- **Page:** /talent/placement carries a "Development &
  Design — the project team" section with an invented
  example; filtering is by the same `asset_class_focus`
  (Hospitality / Residential) as the rest of the desk.

## Platform extensions (built 2026-11-13, owner's "build it all" tap)

- **Embedded expertise.** ROLE_CATEGORIES gains the Project
  Side (DEVELOPMENT_MANAGER · GENERAL_CONTRACTOR ·
  CONSTRUCTION_PROJECT_MANAGER · ENTITLEMENT_CONSULTANT ·
  DEVELOPMENT_FINANCE_ANALYST), traditional software
  (GRAPHIC_DESIGNER · WEB_DEVELOPER · SOFTWARE_ENGINEER),
  and creative services (ANIMATOR · DRONE_OPERATOR ·
  FINE_ARTIST · CREATIVE_INTELLIGENCE_ADVISOR · FILMMAKER);
  DOMAIN_FOCUS gains TRADITIONAL_SOFTWARE_STACK ·
  VISUAL_ASSETS · PROJECT_INCUBATION. `role_family` routes
  them as `project_side`, `software_development`, and
  `creative_services`. Capabilities only — no firm or
  affiliate name attaches on any surface.
- **Lifecycle axis.** `project_lifecycle_stage` (optional,
  strict-when-present): ACQUISITION_ENTITLEMENT ·
  DESIGN_ARCHITECTURE · CONSTRUCTION_EXECUTION ·
  OPERATIONS_STABILIZATION. The matcher applies it with the
  usual rule (unset serves any). `assemble_project_side`
  builds the execution roster like the project team.
- **Project bids (mock).** `POST /api/v1/talent/project-bid`
  + `evaluate_project_bids`: bids ranked by amount against a
  stated budget, lowest in-budget bid named, every response
  labelled mock. A budget check only — no yield-on-cost
  calculation exists in the underwrite engine and none is
  claimed here; nothing is awarded or recorded.
- **Affiliate onboarding.** See
  `docs/specifications/affiliate-onboarding.md`.
