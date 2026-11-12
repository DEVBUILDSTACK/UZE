# Strategic Audit & Innovation Proposal — Talent UI, Referral Networks, Friction

**Status: 🔴 PROPOSAL — design only.** Written 2026-11-12 on
the owner's tap, at his direction that no code be written for
this directive. Nothing here is built unless a section says
so. SoSem's strategic audit of the talent surface as it
stands, and the innovation layer proposed on top of it.

## 0. The audit — where the surface actually is

Built and real: the TalentProfile schema with strict
validation (unknown fields named, never completed by
guessing), the taxonomy (asset-class focus × talent type),
the deterministic matcher, the underwrite→placement bridge
(the report names the roles and the payroll envelope), JSON
ingestion on the gateway's talent track, and a placement
page that explains all of it honestly.

Raw, and this proposal's subject: the unit of the product is
still a *profile looking for a job*. There is no **engagement**
object (the thing a boutique firm actually buys), no
**referral** model (the way this industry actually hires), no
**agent-callable** talent API (the gateway is an API endpoint
taking an email-shaped payload — an ingestion door, not a
query interface), and the page reads as an explainer, not as
a desk you'd trust with a search. Four gaps, four sections.

## 1. Lowering friction for the Critical Six

The six — project managers at boutique firms, hospitality
COOs/CFOs, accounting specialists, tax specialists, insurance
specialists, and the analysts — share one trait: **none of
them is looking for a "job posting."** They buy and sell
*engagements*: scoped, timed, priced against an outcome. The
interface should make the engagement the first-class object.

**Schema addition — the Engagement:**

```json
{
  "engagement_id": "uuid",
  "asset_ref": "underwrite/property reference",
  "need": {"role_family": "operations | knowledge_work",
           "role": "Fractional CFO", "asset_class_focus": "HOSPITALITY"},
  "shape": "W2_HIRE | FRACTIONAL_RETAINER | PROJECT_SCOPED | AGENTIC_TASK",
  "scope": "monthly close + lender reporting, two quarters",
  "cadence": "monthly", "term_months": 6,
  "budget": {"amount": 0, "unit": "USD/month",
             "source": "underwrite payroll envelope | client-stated"},
  "status": "OPEN | SHORTLISTED | ENGAGED | COMPLETED | CLOSED"
}
```

**Schema fix the current profile needs regardless:**
`expected_rate_usd` is a number without a unit — meaningless
across the six. Add `rate_unit: HOURLY | MONTHLY | PER_DELIVERABLE | ANNUAL`,
and on the profile, `engagement_shapes_offered: [...]` and
`availability: {starts, hours_per_week_max}`. A fractional
CFO and a W-2 GM then stop pretending to be the same shape
of supply.

**UI consequence:** the placement page stops asking "post a
job / submit a profile" and starts from the asset: *run the
underwrite → the roles and budget are already known → shape
the engagement → receive a shortlist.* For the six, the
form's first field is the asset, not the person.

## 2. The Referral Engine — the ecosystem moat

Real estate hiring moves along a professional graph:
brokerage ↔ accounting ↔ tax ↔ insurance ↔ legal. The
platform's unfair advantage is that **the underwrite itself
reveals the needs**: a tax bucket far above the micro-region
benchmark is a tax-specialist referral waiting to happen; an
insurance line off benchmark is an insurance-broker
introduction; a refinancing modifier is a lender and a
1031 specialist. Needs detection is arithmetic on the seven
buckets plus the declared transaction intent — the same
never-guess discipline: a need is surfaced only when a number
or an explicit intent supports it.

**Schema addition — the ReferralEdge:**

```json
{
  "edge_id": "uuid",
  "from_entity": "brokerage / firm / profile id",
  "to_profile": "talent profile id",
  "service_category": "BROKERAGE | ACCOUNTING | TAX | INSURANCE | LEGAL | EXCHANGE_1031 | LENDING",
  "context_ref": "the underwrite / engagement that motivated it",
  "detected_need": "taxes at 12.4% of revenue vs 9.1% micro-region benchmark",
  "state": "SUGGESTED | INTRODUCED | ENGAGED | COMPLETED | DECLINED",
  "confirmed_by_both_sides": true
}
```

Rules that keep it honest: an edge becomes *standing* only
when both sides confirm it or an engagement completes through
it — until then it is a suggestion, labelled as such (the
platform's evidence-gating applied to relationships).
Referral economics ride the attribution machinery the
platform already designs for content: a completed engagement
through an edge records a contribution receipt for the
referrer, in the same ledger language as Assign. The moat is
not the graph's existence — anyone can draw one — it is that
every edge here is anchored to a verified underwriting event.

## 3. The agentic interface — hiring a human like a server

A firm's own agent should be able to do in four calls what a
human does in four meetings. Specified as an MCP surface
(mirrored by REST for non-MCP callers):

```
tools:
  talent.search(need)            → ranked validated profiles
  talent.profile(id)             → the TalentProfile + standing
  talent.engage(need, profile, budget_cap)
                                 → engagement DRAFT (not a hire)
  talent.status(engagement_id)   → state machine position
resources:
  /menu (SKUs + talent contract, as in llms.txt today)
  /schema/talent-profile.json
```

Three guardrails make it safe to let an agent "hire":
**(a)** `talent.engage` creates a draft; commitment requires
the same human-confirmed gate the Commitment Ladder auctions
already enforce (`human_confirmed`, else 422). **(b)** Budget
caps travel with the x401 identity: an agent may commit up
to its principal's cap unassisted; above it, the draft waits
for the human — metering tiers already draw exactly this
line ($29.99 / $199.99 / KYB). **(c)** Every call is
idempotent and every response cites its evidence — a
profile's claimed certifications are labelled *claimed*
until the credential layer exists; an agent reading the API
can never mistake a claim for a verification. That last point
is the difference between an agent marketplace and an agent
rumor mill.

## 4. The executive-search feel — what's missing from the page

A job board lists; a search firm *vouches*. Gaps on today's
page, in the order a COO would notice them:

1. **No confidentiality posture.** Senior people do not
   apply in public. The page should say plainly: profiles are
   never listed publicly; a profile is shown only inside a
   shortlist for a named engagement.
2. **No shortlist.** The product of a search is three names
   with reasons, not a searchable database. Proposed results
   view:

```
┌─ Engagement: Fractional CFO — 340-room hotel, 6 months ──
│ Budget envelope (from underwrite): within payroll band ✓
│
│ SHORTLIST — 3 of 3, matched on focus + shape + rate
│  1. [Name] — HUMAN_CONTRACTOR · HOSPITALITY
│     Precedent: 4 completed engagements, 2 verified
│     Rate: fits envelope · Starts: 2 weeks
│  2. [Name] — AGENTIC_SERVICE · any focus
│     Precedent: 11 completed, standing: verified ×9
│     Rate: per-deliverable · Starts: immediate
│  3. [Name] — HUMAN_EMPLOYEE · HOSPITALITY
│     …would convert from fractional — discuss
│ [ Introduce ]  [ Refine the brief ]  [ Talk to the desk ]
└───────────────────────────────────────────────────────────┘
```

3. **No precedent.** Tier-3 projection verification gives
   underwriters a track record; people need the same —
   completed engagements, verified where the platform can
   verify them, as a *standing* shown on the profile. That
   is the search-firm vouch, mechanized.
4. **No human at the desk.** One named line — "the placement
   desk reviews every shortlist before it reaches you" —
   converts a page into a firm. (True today: matching is
   validated by the desk, not yet automated end-to-end; the
   copy should keep saying so until it changes.)

## 5. Sequencing — what to build first, and what not to

1. `rate_unit` + `engagement_shapes_offered` on the profile
   (small, unblocks honest fractional matching).
2. The Engagement object as a record the bridge can emit
   (the underwrite already computes its budget envelope).
3. ReferralEdges recorded on completed engagements (graph
   grows from events, never from scraped contacts).
4. MCP `talent.search` read-only; `talent.engage` last,
   behind the human-confirmed gate, only after 1–3 stand.

Not yet: public profile browsing (breaks the confidentiality
posture), referral payouts before the attribution ledger is
real, and any "AI-matched" language for what remains a
deterministic field match — the copy stays as honest as the
math.
