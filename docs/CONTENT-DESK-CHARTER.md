# 456iP Content Desk — Charter & Architecture Decision

**Date:** 2026-10-16 · **Status:** DECIDED, REDIRECTED (per James 2026-10-16:
extend DEVBUILDSTACK/LEAD_GEN instead of a new repo)
**Mandate:** the two Grok stack articles (four-role autonomous content desk;
AI Company-in-a-Box: manager front-door + bounded decision layer + approval
levels + "prove one loop before automating").

## The decision (updated)

**1. Codebase lives in `DEVBUILDSTACK/LEAD_GEN`, extended.**
James redirected the 2026-10-16 CONTENT-DESK-repo decision: instead of a new
repository, the existing LEAD_GEN repo grows into the Content Desk home —
outreach engine (built), content desk roles, growth analytics, video
pipeline, and skills. Rationale: the outreach engine already lives there,
the team is one, and the commercial boundary is enforced by tenant
scoping + access control rather than repo separation. The
`/bots`-`/routines`-`/tests` portable package structure from the
Company-in-a-Box pattern is implemented as directories inside LEAD_GEN.

**2. It co-exists on KVM2 now — and is built to outgrow it.**
KVM2 (Grok Voice / Telnyx / LiveKit / Hermes gateway / Buzz+Technocore
harness) is already the multi-agent home. The Desk's control plane
(orchestrator = the "Projects Manager front door") deploys there today:

- **Phase 1 (now → post-MVP):** orchestrator + the four content roles run
  on KVM2 as isolated containers. Workload fit is clean: voice is
  real-time and bursty-idle; content work is batch and schedulable.
  Heavy jobs (scraping, rendering) are scheduled off voice-peak hours.
  Initial tenants are 456iP-owned brands only — bounded load.
- **Phase 2 (second-order affiliate growth):** when external UZE affiliates
  onboard as Desk clients, content **workers burst to GCP Cloud Run**
  (already the post-MVP deploy target). KVM2 keeps the orchestrator,
  the voice stack, and the approval front-door. Tenant-scoped design
  from day one makes this a scaling move, not a rewrite.

The alternative — a fully separate box from day one — was rejected:
it splits the multi-agent harness, doubles ops overhead, and buys
nothing while the tenants are all 456iP-owned.

## What the Desk is

The **456iP proprietary master Content Desk**: a multi-agent autonomous
content operation + Referral/Commerce/Services (RCS) engine that plans,
researches, verifies, drafts, and queues publication for every brand it
serves — while stamping everything it touches with the assurative-V3
trust substrate. It does not just create content; it creates
**attested** content. That is the moat over a generic bot desk.

### The four worker roles (adapted from the Grok pattern)

1. **Vertical Desk** (Morning AI Desk, per vertical): hospitality, music
   concerts, athletic competitions (LA2028/FIFA/F1), VIP experiences.
   Output: a short brief of what changed in 24h, every item linked to
   its original source, claims flagged as claims. If nothing matters,
   it says so.
2. **Claim Checker**: every viral or influential claim goes through it
   before it can be repeated. Verdicts: supported / partly supported /
   unverified / misleading — with the primary source and the key caveat.
3. **Angle Scout** (Article Scout): research-backed topics worth a
   flagship piece per month per vertical — working title, thesis,
   primary links, why now. Weak topics die here, never become posts.
4. **Voice Editor** (Post Editor): turns verified briefs into drafts in
   the tenant brand's voice, three openings, source links attached,
   most-challengeable claim flagged. Never publishes.

### The decision & approval layer (the "Jev" function, in code)

No separate decision model is bought on day one. Routing, research-gate,
and completion-gate decisions are explicit, inspectable rules in the
orchestrator — upgradeable to a typed decision service later without
touching the workers. Autonomy levels, mapped to standing 456iP rules:

- **L0 read / L1 prepare** (research, draft, queue): autonomous.
- **L2 reversible write** (internal docs, schedules): autonomous,
  tenant-scoped.
- **L3 external action** (post, publish, send): **human approval,
  always.** Same rule as the public mockup: nothing public moves
  without the tap.
- **L4 money / irreversible**: **per-action approval naming account,
  amount, asset, timing.** No standing authority, ever.

### The trust substrate (assurative-V3, under everything)

Every published piece carries: (i) provenance of the source asset via
**Numbers Protocol**; (ii) on-chain attestation of the claim-check
trail; (iii) attribution to originators; (iv) KYC/KYB authentication
of the publishing entity where required. The Desk is the first
production consumer of the GIRAx Layer's trust primitives.

## Tenant model: 456iP first, network second

- **Tenant one: Learn2Launch (@l2launch).** The innovation incubator is
  the Desk's proving ground — content about the builder track, Ink,
  Quotrons, and the creator pipeline, engineered to influence future
  client engagement and affiliate sign-ups. Dogfood first.
- **Tenant two: UZE / UZED.si brands.** Vertical expertise content for
  the demand side.
- **Then: the second-order network.** UZE affiliate client brands —
  solopreneurs, businesses, orgs unrelated to 456iP — buy the Desk as
  the "content innovation offering" (see AFFILIATE-CONTENT-NETWORK).
  One tenant, one voice, one funnel; attribution and settlement stay
  on UZE rails. This is the single most significant growth lever, and
  the architecture serves it from day one via tenant scoping — not as
  a later rewrite.

## Roadmap (plan of attack)

1. **Charter + repo:** this doc (UZE); extend `DEVBUILDSTACK/LEAD_GEN`
   with `/bots`, `/routines`, `/tests`, `/tenants` scaffold (see
   CONTENT-DESK-TEAM-SKILLS-PLAN.md for the team + skills build-out).
2. **KVM2 control plane:** orchestrator + four roles as scheduled
   routines, tenant `l2launch` first.
3. **Prove one loop:** one vertical brief → claim-checked → drafted →
   James's approval → posted on @l2launch. Do not automate until this
   works once, end to end.
4. **Trust wiring:** provenance stamping + claim-check attestation on
   every published piece.
5. **Expand:** add workers/routines only as proven demand requires
   (outbound prep, SEO/GEO desk, stills/clips) — never agents for
   agents' sake.
6. **Burst path:** containerize workers for GCP Cloud Run ahead of the
   first external affiliate tenant.

## Non-goals

- No publishing without human approval. Ever.
- No worker sees more than its tenant. Tenant isolation is a security
  boundary, not an editorial one.
- No 40 routines on day one. Five max, proven one at a time.
