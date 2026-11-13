# Final Architecture Map — Lifecycle, With Honest Stage Labels

Filed 2026-11-13 on the owner's tap. This map combines the
lifecycle the platform is built around and states, per
stage, what is **built**, what is **mock**, and what is
**proposal**. Where this map and any narrative disagree,
this map — written from the code — governs.

Status key: 🟢 BUILT (code + tests) · 🟡 MOCK / PARTIAL
(labelled fixtures or shape only) · 🔴 PROPOSAL (designed,
not built). A separate deployment caveat applies platform-
wide: the compose API is real and tested but **not yet
publicly deployed** (the Render step is the owner's), so
API-backed behaviour is demonstrable in the test suite, not
yet from the public internet. Public pages are live.

## The lifecycle

### 1. Land & development intent (A-N-R-D) — 🟡 PARTIAL
A development enters as an **Intent** carrying the HIADR
fields filed in the Nov 8 addenda: asset subclass, target
area, and subterranean context, with ingestion enforcement
in `intents.py` (polygon required for A/D/R; radius-or-
polygon for H/I; subterranean context mandatory where the
addenda require it). The ratified **HICRE | ANRD**
taxonomy restructure lands **Nov 15**. Not built: parcel-
level development underwriting, and any development-cost
calculation — no such calculation exists in the engine.

### 2. UZE Underwrite (the money) — 🟢 for HiCRE, by scope
For operating Hospitality & Income CRE the engine is
built and blind-test verified: seven-bucket P&L mapping
(OpEx never absorbs Taxes, Insurance, or Interest),
unlevered NOI, three-tier projections and verification,
Yardi dialect pack (165/165 lines mapped on the verified
blind test). By the owner's Nov 10 scope ruling the
underwrite surface is **HiCRE only**: A-N-R-D intakes
receive a polite 422 there and are handled by direct
engagement. Claims that the engine "calculates development
costs" for raw land are false and must not be made.

### 3. Talent — Development routing (D → H&I) — 🟢 code
`derive_talent_placement()` in `talent_profile.py`,
attached to every multiyear underwrite, emits three paths.
The development path is **context-routed**: given a
*declared* project context (lifecycle stage, domain focus,
asset-class focus — `development_requirements()`),
it names the categories that stage requires — entitlement
and finance at acquisition, the design team at
DESIGN_ARCHITECTURE (with the wellness consultant added
for resort/wellness domains), general contractor and
construction management at CONSTRUCTION_EXECUTION. Without
a declared context it is the platform's standing project-
team offer. Nothing is inferred from the asset's
financials; the routing is rules over declared inputs.
Matching is `role_family()` + `match_profiles()`:
deterministic, family/focus/domain/stage-filtered.

### 4. Talent — Operations (H&I) — 🟢 code
The operations path is **derived from the asset itself**:
roles are read from the underwrite's own payroll line
labels (manager → Property Manager, maintenance, leasing,
security, housekeeping) and the payroll budget is summed
from those lines. No role lines, no requirement — the
engine never invents a staffing need. Knowledge Work is
the third standing path (outsource the asset's ongoing
financial analysis, to a human contractor or an agentic
service).

### 5. Project-side bidding — 🟡 MOCK
`POST /api/v1/talent/project-bid` ranks submitted bids
against a stated budget and names the lowest in-budget
bid. It awards nothing, records nothing, and checks no
yield figure — evaluation logic only, labelled mock.

### 6. Creative & pre-sales (L2Launch surface) — 🟡 PARTIAL
Software and creative capabilities are embedded invisibly
in the same TalentProfile taxonomy (software engineer, web
developer, animator, drone operator, filmmaker…) and route
through the same matcher families — one engine from
architect to drone operator. The /development-stack page
presents the turnkey stack under generic titles; its
time-based compute rental is **shape only** (tiers named,
no prices, no checkout, no provisioning). Affiliate
white-label pages (/affiliates, /affiliates/[slug]) run on
labelled demonstration fixtures.

### 7. Inference & privacy — 🟢 code, 🟡 live state
Inference routes through the attestation-verified NEAR AI
client (`inference.py`); the Private AI Mode toggle on
/treasury reflects exactly that, with the honest account
state shown ($0.00 balance; live calls return HTTP 402
until credits land). The Trace Commons gateway pattern and
tiered data-sharing consent are a filed 🔴 PROPOSAL
(`private-inference-gateway-proposal.md`); the opt-in
endpoint is a labelled mock that records intent only.

## Claim discipline (for any public narrative)

**Backed by code:** the underwrite names an operating
asset's team from its own payroll · one taxonomy routes
operations, knowledge work, development, software, and
creative profiles · development routing follows the
project's declared stage and asset class · attestation-
verified inference with an honest 402.

**Not backed — do not claim:** development-cost calculation
from a land parcel · inference of a development team's need
from financials · a bookable compute rental · a live public
API (pending deployment) · NEAR AI credits of any kind.
