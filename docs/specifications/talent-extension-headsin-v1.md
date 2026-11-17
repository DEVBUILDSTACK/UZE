# Talent Extension v1 — HeadsIn-Modeled Components, Category Routing, Intents Solver

**Status: 🟢 SPEC AGREED & BUILT (2026-11-17).** Owner
directive (James, 2026-11-17): finalize and extend the
existing talent specification and build, based on the
HeadsIn human UI and on how opportunities move across
categories — our dual-plane focus in Hospitality and Income
CRE, our expertise in software stack and blockchain
technical development, and the other fields we do not build
natively.

This document **extends, and does not replace**, the existing
talent record:

- `talent-placement-parsing.md` — the TalentProfile schema
  and ingestion architecture (JSON path built 2026-11-12).
- `strategic-talent-ui-audit.md` — the 2026-11-12 audit and
  proposal (Engagement object, referral engine, agentic
  interface, executive-search feel). Sections of that
  proposal that this extension builds are named where they
  land; the rest of that proposal stands as filed.
- `services/compose/src/talent_profile.py` — the built
  schema, taxonomy, matcher, underwrite bridge, referral
  edges, project-bid mock.
- The integration mapping in the HeadsIn reverse-build memo
  (filed 2026-11-17, research notes) — the component list in
  §2 is that memo's table, specified against our objects.

**Clean-room rule (owner ruling, 2026-11-17):** the HeadsIn
solution is reverse-engineered from publicly observable
product behaviour only. Nothing in this extension obtains,
licenses in, or reuses HeadsIn source code, and no step
depends on it. HeadsIn remains the back-end partner under
the signed agreement (candidate supply and placement
operations in India); the implementation here is our own.

---

## 1. Settled structure this extension is built on

Three top levels (owner rulings, 2026-11-17):

- **Treasury** — its own top level.
- **Talent** — the broad **people layer**: who is engaged
  and how. Not a workflow system.
- **Enterprise Services** — the systemic **workflow layer**:
  the **ATS sits under Enterprise Services**, alongside
  **payroll** (its main functionality). Placement workflows
  and payroll setup live here; Talent classifies the person
  being placed.

Dual-plane discipline (unchanged, non-negotiable): every
component below exists twice over the *same live objects* —
(a) a human UI surface, and (b) a headless autonomous
counterpart serving the same objects as JSON for agents.
Nothing is UI-only.

The demand side is the **employer**. All people engaged
through this system — employees, affiliates, agentic
services — are **Creative Intelligence** (Learn2Launch):
hired for their contribution.

**Governance constraint (standing, owner ruling
2026-11-17):** UZEmarkets will **always** control all of
Talent and the Talent build internally. **Talent will
never be an external affiliate** — the direct inverse of
the DealFi/Fundio affiliate pattern (§10). The Talent
system, its build, and its data remain internal to
UZEmarkets permanently: affiliates integrate **into**
Talent; Talent itself is never spun out, sub-licensed, or
externalized.

---

## 2. HeadsIn-modeled components (dual-plane)

Each component is modelled on a behaviour HeadsIn's public
product demonstrates, and implemented as our own object.

### 2.1 Trusted profiles

- **Object:** the TalentProfile (existing). "Trusted" is
  earned standing on the record — claimed certifications are
  labelled *claimed* until the credential layer exists (the
  audit's §3 guardrail stands).
- **Human plane:** profile pages under `/talent/<account>`;
  the profile builder (§2.2).
- **Headless plane:** the profile as JSON
  (`/api/v1/talent/<account>` pattern); agents read and
  match on the same record.

### 2.2 Profile / resume builder — the profile is the source of record

- A resume is a **rendering** of the TalentProfile, never
  the input. The builder flow assembles the profile fields;
  the JSON profile is what the system stores and matches.
- PDF/Word intake stays deferred per the January 2nd ruling
  (`talent-placement-parsing.md`); the gateway keeps saying
  so cleanly.

### 2.3 The pre-assessment — an assessment object on the profile

Modelled on HeadsIn's ~250-second role-specific
pre-assessment ("skills prove the fit"). Ours is an
**assessment object** carried on the TalentProfile:

```json
"assessment": {
  "role": "string — the role assessed against",
  "score": "number 0–100",
  "duration_seconds": "number > 0 (≈250 nominal)",
  "skills_proven": ["string, …"],
  "completed_at": "string — ISO-8601 timestamp"
}
```

Optional, strict-when-present, like every taxonomy field:
a malformed assessment names `assessment` in the
INSUFFICIENT_DATA problem list; a profile without one stays
valid. Assessments are also recordable on their own through
the headless surface (§7), because a candidate may be
assessed after the profile lands.

- **Human plane:** an in-browser timed assessment; the
  candidate sees the outcome on their profile.
- **Headless plane:** the assessment object in profile JSON;
  the matcher and agents consume the score without the UI.

### 2.4 Scorecards — assessment score into the deterministic matcher

HeadsIn's AI scorecards are, on our side, **ranked
shortlists produced by our deterministic matcher** with the
assessment score as one input — never an "AI match" claim
(the audit's honesty rule stands: the copy stays as honest
as the math).

- A need may declare `min_assessment_score`; profiles below
  it are filtered out.
- Scorecard results carry, per profile: the matcher's
  verdict, the assessment score (or null), the segment route
  (§6), and a rank. When assessment scores are present the
  scorecard ranks by score; otherwise matcher order stands.
- **Human plane:** employer scorecard/shortlist pages.
- **Headless plane:** the solver response (§5) is the
  scorecard in JSON.

### 2.5 Role postings — seeded by UZE Underwrite

Modelled on HeadsIn's AI JD maker, with our difference:
roles originate in the underwrite. An asset's payroll lines
name the roles (`derive_talent_placement`); platform roles
(developers, AI, data science, agentic-marketplace skills)
originate from our own staffing needs.

- **Human plane:** employer posting flow; the generated
  draft is human-editable.
- **Headless plane:** role objects (needs) in the ATS API —
  the same need shape the matcher and the solver consume.

### 2.6 The two-way application lifecycle — the ATS state machine

HeadsIn's signature transparency: one application state,
seen identically by candidate and recruiter. Ours is the
**ATS application** (Enterprise Services workflow layer)
with a single state machine:

```
RECOMMENDED → APPLIED → IN_PROGRESS → ACCEPTED
                                  ↘ REJECTED
                        APPLIED → REJECTED
```

- Every transition is recorded as an **event** (from-state,
  to-state, actor, timestamp) on an append-only record —
  the lifecycle is auditable, and both planes read the same
  event stream.
- ACCEPTED is the settlement point of a match: it produces
  the **placement record** that feeds Enterprise Services
  payroll setup (§4).
- **Human plane:** candidate tracker and recruiter pipeline
  board — two views of one state.
- **Headless plane:** application JSON + transition events;
  agents act on transitions; the autonomous placement engine
  advances states under the same rules.

### 2.7 In-app communication

Message threads **bound to the application** (not to a
person): candidate and employer converse inside the
application record; contact details are never exposed
(HeadsIn's privacy-preserving pattern). Messages are part of
the application's append-only record, readable on both
planes; agent-mediated comms serve AGENTIC_SERVICE talent.

---

## 3. The category model — how opportunities move

A need (and, optionally, a profile) declares an
**opportunity category**. Categories decide *who builds the
supply*:

| Category | Class | How it moves |
|---|---|---|
| `HOSPITALITY` | **FOCUS** — built natively | Roles named by UZE Underwrite from asset payroll lines; the Operations path. Matched natively. |
| `INCOME_CRE` | **FOCUS** — built natively | Income commercial real estate roles (operations + knowledge work on income assets). Matched natively. |
| `SOFTWARE_STACK` | **EXPERTISE** — built natively | Traditional software stack development, from the standing bench (§3.1). Matched natively. |
| `BLOCKCHAIN_TECH` | **EXPERTISE** — built natively | Blockchain technical development, from the standing bench (§3.1). Matched natively. |
| `OTHER` | **Not built natively** | Healthcare, pharma/scientific, and every other field: routed through **placement agreements** to **expert contractor-affiliates**, case by case (§3.2). |

**Financial-services demand** has its own answer in this
model: the DealFi desk (§10) — an external affiliate
solution integrated into the platform, not a UZEmarkets
build. A company whose need is *financing sales* — selling
debt financing, equity, or private equity — does not hire
for it through placement at all; the desk is the
productized form of that placement, supplied by the
affiliate.

### 3.1 The standing technical bench + the selection rule

For technical software and blockchain development the
expert relationships are already established — go-to
benches in **India, Brazil, the United States, and Europe,
particularly Spain and Costa Rica**.

**Selection rule:** which bench expert is used is
determined by **(1) the employer's industry vertical/niche**
first, and **(2) the pertinent language requirements of the
target employee or contractor** second. That is what
decides India vs Brazil vs any other location.

### 3.2 OTHER — routed, labelled, never a silent no-match

A need in category `OTHER` does **not** run the native
matcher. The routing result is explicit:

```json
{
  "status": "routed_to_affiliate_expert",
  "routing": "affiliate_expert",
  "category": "OTHER",
  "matches": [],
  "route_reason": "…placement agreement to an expert
                   contractor-affiliate, case by case…"
}
```

Corporate placement mechanics (owner rulings, 2026-11-17):
UZEmarkets Americas or UZEmarkets Europe signs the
placement agreement (different contracts per region); the
fee is usually paid **on placement of the employee**,
occasionally with an upfront distribution. The engagement
may be passed to sector and language/region experts **as
our contractor — which makes them an affiliate** for that
engagement.

---

## 4. The people-layer taxonomy as data

Talent is the people layer. Two new optional profile
fields carry it (strict-when-present, backward compatible):

### 4.1 `engagement_class`

| Value | Who | Money flow |
|---|---|---|
| `EMPLOYEE` | The employer's own person — **not an affiliate** | Employer payroll. The employer may use **our payroll + ATS for a fee**, or do it directly — case by case. |
| `AFFILIATE_SOLOPRENEUR` | Solopreneur creator outsourced/outstaffed through UZEmarkets | Through us: client pays UZEmarkets, **we pass the spread**. Or placed as contractor: employer remits payroll **through us or around us**. |
| `AFFILIATE_EXPERT` | Expert firm/specialist engaged per placement as our contractor | Placement-agreement fee, usually on placement (§3.2). |
| `AGENTIC_SERVICE` | An agentic service | **x402** payment identity; no payroll. |

`engagement_class` is a different axis from the existing
`talent_type` (HUMAN_EMPLOYEE / HUMAN_CONTRACTOR /
AGENTIC_SERVICE): talent_type says what the worker *is*;
engagement_class says *through whom they are engaged and
how the money moves*. Both stand.

### 4.2 `work_mode` — employees only

`REMOTE | HYBRID | ON_SITE` (hybrid = partially on-site,
max ~2 days off-site per week). **Work mode is an employee
attribute.** Validation rejects `work_mode` on any profile
whose engagement class is not `EMPLOYEE` — including a
profile that declares a work mode without declaring the
employee class — naming `work_mode` in the problem list.

### 4.3 The placement record → payroll handoff

On ACCEPTED (§2.6), the placement record fires the
Enterprise Services setup for the profile's engagement
class: EMPLOYEE → payroll enrolment (ours for a fee, or the
employer's own, per the engagement); AFFILIATE_SOLOPRENEUR
→ the spread or pass-through track; AFFILIATE_EXPERT → the
placement-agreement fee track; AGENTIC_SERVICE → x402.
Settlement currencies per the standing matrix: USDC on
Solana / USDC on Base / USDG on Robinhood Chain.

---

## 5. The matching mechanism — NEAR AI Intents solver interface

Matching is specified as an **autonomous marketplace for
demand for skills**, on the NEAR Intents pattern:

- **Intent** = an employer's role requirement, expressed as
  a need object (role family / role / category / focus /
  domain / stage / segment / minimum assessment score).
- **Solvers** = candidate supply — **both human profiles and
  agentic services** respond to an intent with offers
  (candidate offers: the matched profiles, scorecard-ranked).
- **Settlement of a match** = the placement record (§4.3):
  an ACCEPTED application feeding Enterprise Services.

```json
POST /api/v1/talent/intents/solve
{ "need": { … } }
→ {
    "intent": {"kind": "ROLE_REQUIREMENT", "need": { … }},
    "solver": "deterministic_matcher_v1",
    "offers": [ …scorecard results… ],
    "routing": "native | affiliate_expert",
    "inference": {"provider": "NEAR AI",
                  "status": "unavailable",
                  "detail": "…"}
  }
```

**The current solver implementation is the existing
deterministic matcher** (`match_profiles`), placed behind
this interface unchanged in behaviour. The interface is the
contract; solver implementations can be swapped behind it.

**Honesty label (standing state, never softened):** NEAR AI
attested inference on our side is **credit-blocked — HTTP
402, $0 org balance**. No part of this surface performs or
claims live NEAR AI inference. Wherever a surface describes
the matching, it labels the solver as the deterministic
matcher and the NEAR AI inference state as unavailable,
following the repo's existing honesty patterns (labelled
mocks, labelled fixtures, `PRICING_NOT_CONFIGURED`-style
in-band states).

---

## 6. Experience segmentation — a routing rule

Hands-on placement is not for every segment. The routing
rule, modelled as data on the role (need) and the
candidate (profile):

| Segment | Who | Served by |
|---|---|---|
| **PLACEMENT_FOCUS** | Professionals ~27+ with 5–7 years of experience | Hands-on placement — this is where placement concentrates |
| **EARLY_CAREER** | ~19–27, fresh out of traditional university — particularly white-collar roles exposed to AI replacement | **Not** the hands-on placement environment — the autonomous NEAR Intents marketplace matching (§5) |
| **ELITE_EXCEPTION** | AI/ML and highly experienced developers with **≥5 years at a major international firm** | In scope for placement **regardless of the age band** |

As data: a profile's segment is derived from declared
fields — `experience_years`, an AI/ML signal (role/skills),
and the optional `major_firm_years` (years at a major
international firm, strict-when-present like every field
here). A need may declare `target_segment`
(`PLACEMENT_FOCUS | EARLY_CAREER`); an undeclared need
defaults to PLACEMENT_FOCUS.

Routing outcomes (`segment_route`):

- Elite-exception candidate → **placement**, against any
  need (the band does not bind them).
- A need targeting EARLY_CAREER → **intents_marketplace**
  for non-elite candidates.
- An EARLY_CAREER candidate against a placement-focus need
  → **intents_marketplace** (early-career supply is served
  autonomously, not by the placement desk).
- Otherwise → **placement**.

The scorecard (§2.4) carries each offer's route, so both
planes show *where* a match is served, not just *that* it
matched.

---

## 7. Headless surface added by this extension

All under the existing `/api/v1/talent` prefix, in the
existing INSUFFICIENT_DATA discipline (422 naming fields):

| Endpoint | Plane behaviour |
|---|---|
| `POST /api/v1/talent/intents/solve` | The solver interface (§5): intent in, offers + routing + honesty label out |
| `POST /api/v1/talent/assessments` | Record an assessment object against a named profile (§2.3) |
| `POST /api/v1/talent/applications` | Open an application (profile + role reference) at RECOMMENDED |
| `GET /api/v1/talent/applications/{id}` | The application: current state, full event stream, message thread — the two-way view, one record |
| `POST /api/v1/talent/applications/{id}/transition` | Advance the state machine; the transition is recorded as an event; an illegal transition is refused by name |
| `POST /api/v1/talent/applications/{id}/messages` | Append a message to the application's thread |

Storage follows the v1 pattern of the existing build:
append-only JSONL (env-overridable paths), a database table
a later migration — stated plainly, as the existing modules
state it.

---

## 8. What stays unchanged

- The TalentProfile required fields and every existing
  optional field, its validation discipline, and its
  normalization. Existing fixtures validate identically.
- `talent_type`, `asset_class_focus`, `role_category`,
  `domain_focus`, `project_lifecycle_stage` — axes and
  enums untouched.
- The deterministic matcher's matching behaviour
  (`match_profiles`): family, role, category, focus, domain,
  stage compatibility, input order. The scorecard and the
  solver wrap it; they do not alter it.
- `derive_talent_placement` (the underwrite bridge and its
  three paths), `assemble_project_team`,
  `assemble_project_side`, `evaluate_project_bids` (the
  labelled mock), referral edges and chains.
- The gateway's talent track, including the PDF/Word
  January 2nd deferral.
- The existing `/talent` and `/talent/placement` pages'
  design language and structure — extended with sections,
  not redesigned.
- GIRA/SURA confinement: those names appear only on
  real-estate surfaces; nothing in this extension adds them
  to talent surfaces.

---

## 9. As built (2026-11-17)

- `talent_profile.py`: `engagement_class`, `work_mode`
  (employee-only rule), `opportunity_category`,
  `major_firm_years`, and the `assessment` object validated
  and normalized; `validate_assessment` shared with the API;
  `route_category`, `experience_segment`, `segment_route`,
  `scorecard_matches` added. `match_profiles` untouched.
- `talent_ats.py` (new): the application state machine,
  event-sourced JSONL record, message threads, and
  `solve_intent` — the deterministic matcher behind the
  intents interface, with the NEAR AI honesty label in-band.
- `talent_applications.py` (new): the §7 endpoints, wired
  beside `talent_bids` in `app.py`.
- Web: `/talent` gains the category structure;
  `/talent/placement` gains the categories, the
  pre-assessment, two-way tracking, segmentation, and the
  solver description with its honesty label.
- Tests: `tests/test_talent_headsin_extension.py` — taxonomy
  validation (incl. work_mode rejected for non-employees),
  assessment recording, lifecycle transitions and events,
  category routing (native vs affiliate-routed), segment
  routing (placement / intents marketplace / elite bypass),
  matcher-with-assessment, and the solver endpoint.

---

## 10. The DealFi desk — an affiliate's productized placement (SPEC ONLY)

**DealFi leads with funding as it rolls out — a funding
and deals desk: a lead-generation desk for funding,
financial, and talent demand.** Debt, equity, and private
financing sit on the funding side; crossing into the
Talent plane, the desk also serves talent referral
demand. In Talent terms the desk is a **productized
placement**: companies worldwide staff sales associates
to sell debt financing, equity, or private equity. The
answer offered on this platform is that the demand-side
employer uses the DealFi desk **instead of hiring**
business development / growth / salespeople to place
their financial or funding services. The desk cures the
need to hire financing salespeople.

**Whose desk it is (owner correction, 2026-11-17):** the
DealFi desk is **not a UZEmarkets build** and does not live
in this monorepo. DealFi is an **affiliate solution in its
own right — its own entity and its own repo**:

- **Entity: DealFi (DFI)** — the Wyoming affiliate entity
  behind the desk (written DealFi (DFI); the term "LLC" is
  not used, per the owner's correction, 2026-11-17).
- **Ownership & licensing:** the separate DealFi repo is
  still part of **our** repo structure — it lives in
  **DEVBUILDSTACK**, separately branded. All IP is
  **completely owned by 456iP** and **perpetually,
  non-exclusively sub-licensed** to others; DealFi (DFI)
  operates under that sub-license. The repo separation
  exists precisely so the asset can be sub-licensed
  cleanly as a bounded unit — separation is a licensing
  boundary, not an ownership boundary.
- It integrates **into** the UZEmarkets platform the way
  **Fundio** does (Fundio (FVC) — FVC short for Fundio VC,
  its own affiliate entity, built into the platform but not
  UZEmarkets): an **API-level integration** between the
  affiliate's own system and the platform, consistent with
  how this spec treats other affiliate surfaces.
- **DealFi and Fundio are two of the first affiliates for
  A/B testing** on the UZEmarkets platform.

Modelled against this extension's objects:

- **The role it fills** is the financing-sales function
  itself (business development / growth / sales for
  financial and funding services) — a demand category, not
  a person-shaped need.
- **The "candidate" is the desk itself**: where a placement
  need is answered by matched TalentProfiles, a
  financing-sales need is answered by engaging the
  affiliate's desk. In category-model terms (§3),
  financial-services demand of this shape does not enter
  the native matcher or the OTHER routing — it is served
  by the desk as a standing affiliate product, reached
  through the platform's affiliate integration.
- **Demand side**: the employer (a company with financing
  or funding services to place) engages the desk through
  the platform the way it would engage a placement — the
  affiliate's desk is the supply.
- **Timeline on record:** the desk is built **prior to the
  April 2 launch** and A/B tested on the standing A/B
  testing track (mid-November 2026 → April 1, 2027).
  "DealFi One deal flow desk operational" is one of the
  four UZD launch-acceleration factors.

**Scope flag:** this section is the spec-level inclusion
only. **No DealFi code is scaffolded in this monorepo** —
the desk is the affiliate's own build, in its own repo,
integrated at API level; its build is its own workstream,
sequenced on the timeline above.
