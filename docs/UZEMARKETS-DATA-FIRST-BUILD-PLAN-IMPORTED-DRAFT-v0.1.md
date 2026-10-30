# UZEMARKETS — Data-First Build Plan (Imported Draft v0.1)

**Source:** external frontier API (DeepSeek / Kimi class), supplied by James 2026-10-29 20:51 EDT as the scope to implement now for UZE.
**Naming (final, 2026-10-29):** Product = **UZEMARKETS commerce platform**. Implementing agent = **SoSem** (directed by James). Reviewing/directing coding agent = the external frontier-API agent. No surface of this plan is named for any agent.
**Status:** IMPORTED DRAFT — in the specification phase of the delivery cadence (scope → specification mutually agreed → daily 24h all-in sprints). Not yet mutually agreed; no sprint starts until James agrees the specification.
**Build-agent note (James):** a DeepSeek or Kimi frontier external API serves as a build-time coding agent. Its key is development-only, never a runtime dependency (spec §9) — provisioned by James, never committed.
**Scope Tenet 01 check (SoSem, 2026-10-29):** CONFORMS — Python/FastAPI core; this schema is UZEMARKETS' own distinct Postgres (Neon), endpoints separate per front end; Redis shared as cache/state with Postgres authoritative; additive migrations only = backward compatibility; GeoAnchor/MetroProfile + concierge module align with the Tenet 01 Innovation & Scale extension (geo awareness, agentic concierge, VIP pay-as-you-go tier). Noted gaps for the mutual-agreement pass: (a) RAG knowledge-base access is not specified in this plan — it rides the shared layer per Tenet 01 and needs its section; (b) language awareness appears only on FacilityProfile — the extension calls for it across the RAG/concierge surfaces; (c) the "no LLM in classify()" rule arrives as the external source's assertion ("decided earlier") — it is a proposal until James confirms it; (d) the plan's Month 1–6 clock maps onto James's standing timeline (development from mid-November 2026; MVP April 1–15, 2027) if Month 1 = the first build month.

---

# SPEC: UZEMARKETS Commerce Platform — Data-First Build Plan

Audience: the implementing coding agent.
Purpose: define the schema, the sprint sequence from a data perspective, and the forward-compatibility rules that let the medical-travel vertical be added between month 4 and month 5 without a schema rewrite.

---

0. Briefing to the implementing agent

You are building a dual-surface (agent API + human web UI) travel-and-venue marketplace. The first commercial vertical is event travel — music and sports — with NFT ticketing settled in USDC on Solana. The second vertical, health travel (surgery/dental + recovery hospitality), is funded conditionally and will be added later. Your primary obligation is that the schema you write in month 1 already accommodates month 4.

Two rules govern everything:

1. Contract-first. The Prisma schema is the source of truth. The agent tool manifest (MCP-style) and the human typed client are generated from it. Any field present on one surface and not the other is a defect.
2. Additive migrations only. No destructive migrations against any environment with data. New columns are nullable or defaulted; new tables are introduced dormant.

---

1. Confirmed stack

Layer Choice Notes for you
API Python + FastAPI Async throughout; Pydantic v2 models generated/derived from schema
Schema/ORM Prisma ORM See §2 — this is a decision point, not a settled fact
Database Neon Postgres Use Neon branching for every migration preview
Cache/state Redis Draft tokens, hot geo cache, rate limits, pub/sub for approval gates
Human UI Next.js + shadcn/ui App Router, server components for read paths
Client state Zustand Only for intake stepper + optimistic UI; server state lives in the API
Settlement Solana + USDC Testnet for MVP; mainnet gated on revenue proof
Build-time AI DeepSeek API key Development agent only. Never a runtime dependency — see §9

⚠️ §2 — Prisma + FastAPI is the one stack risk

Prisma's Python client (prisma-client-py) is community-maintained and lags the JS client. Pick one of these now, do not drift:

· (A) Prisma for schema + migrations, SQLAlchemy 2.x async for runtime queries. Most robust. You keep Prisma's excellent migration ergonomics and Neon integration while using a mature Python runtime.
· (B) prisma-client-py end-to-end. Faster to start, higher maintenance risk on advanced queries (partial indexes, RLS, CTEs).

Recommendation: (A). Write schema.prisma as the authoring DSL; run prisma migrate to produce SQL; query via SQLAlchemy models that mirror it. Generate Pydantic and TypeScript types from the same Prisma schema so all three layers stay in sync.

---

2. Timeline and gating

Window Vertical Gate to proceed
Month 1 Event MVP — intake, tickets (NFT/USDC), local scope Walking skeleton demoable end-to-end
Month 2 Event — stay + flight rails, travel scope Three-component bundle with per-rail failure codes
Month 3 Event — task rail, map, hardening Market test launch
Months 3–5 Event — iterate on real usage Revenue proven by end of month 5
Month 4–5 (conditional) Health — facility rail, phases, fit-to-fly Funding allocated and revenue gate met
Month 6+ Launch incl. health (if funded) —

The schema obligation is this: the health vertical's build window is a 6–8 week sprint placed on top of a live revenue-generating system. There is no room for a schema migration that touches the event vertical. Therefore §4's forward-compatible structures ship in Sprint 0, dormant.

---

3. Data architecture principles

1. Phase-shaped stays from day one. A trip has StayPhase[], never a single check-in/check-out pair. The event case is a one-element array.
2. Travelers are objects, not counts. party: 2 is forbidden; two Traveler rows with roles.
3. GeoAnchor is polymorphic from day one. type enum includes facility even though MVP only emits venue and metro.
4. CommitmentClass is a closed enum containing the medical members from day one. APPOINTMENT and MEDICAL_PACKAGE exist in Sprint 0 and are unused until month 4.
5. Offers are snapshots. Price and terms are frozen at quote time in OfferSnapshot. This is non-negotiable — it is your defense against "the rate changed" disputes on both verticals.
6. Health attributes live in a separate table namespace with its own consent gate. They are never columns on Traveler or TripProfile.
7. Everything is event-sourced at the aggregate level. EventLog is append-only and is the audit surface for agent transparency, disputes, and medical compliance.

---

4. Schema specification

4.1 Sprint 0 — all of this ships in month 1

Enums (complete, including dormant members):

```prisma
enum GeoAnchorType   { VENUE FACILITY ADDRESS METRO }
enum TravelerRole    { PATIENT COMPANION PRIMARY GUEST }
enum StayPhaseKind   { PRE_EVENT EVENT POST_EVENT PRE_OP INPATIENT RECOVERY }
enum ModuleType      { TICKETS STAY FLIGHT PARKING TRANSIT DINING TRANSFER VIP_CONCIERGE FACILITY }
enum CommitmentClass { IRREVERSIBLE_ON_CHAIN CANCELLABLE_UNTIL_WINDOW CHANGEABLE_WITH_FEE APPOINTMENT MEDICAL_PACKAGE }
enum Rail            { SOLANA_NFT HOTEL_AGGREGATOR FLIGHT_SEARCH FACILITY PARKING TRANSFER DINING_TASK }
enum TaskState       { REQUESTED QUOTED DEPOSIT_PENDING CONFIRMED FAILED CANCELLED }
```

Intake layer:

```prisma
model IntakeDraft {
  id           String   @id @default(uuid())
  token        String   @unique          // Redis-backed resume handle
  answers      Json                      // slot-typed, partial allowed
  missingSlots String[]
  invalidSlots Json                      // { slot, error }
  expiresAt    DateTime
  createdAt    DateTime @default(now())
  @@index([expiresAt])
}

model TripProfile {
  id            String    @id @default(uuid())
  buyerId       String
  version       Int       @default(1)
  modules       ModuleType[]
  tier          String    @default("AGENTIC")   // AGENTIC | VIP_PAYG
  authorization Json                            // per-module caps + commitment ceilings
  confirmedAt   DateTime?
  supersededBy  String?
  @@index([buyerId, confirmedAt])
}

model Traveler {
  id             String       @id @default(uuid())
  tripProfileId  String
  role           TravelerRole
  origin         String?
  nationality    String?                       // passport — matters for medical/visa later
  utilityWeights Json                          // { proximity, amenity, quiet, safety, workspace, budget }
  tripProfile    TripProfile @relation(fields: [tripProfileId], references: [id])
  @@index([tripProfileId])
}

model GeoAnchor {
  id       String        @id @default(uuid())
  type     GeoAnchorType
  refId    String?                             // venue id, facility id, metro code
  label    String
  lat      Float
  lng      Float
  radiusKm Float         @default(15)
  metroId  String?
  @@index([type, refId])
}

model MetroProfile {
  id               String  @id @default(uuid())
  metroCode        String  @unique             // MIA, BNA, ATL, NYC, GRU, GDL, TIJ
  facilityClusters Json                        // populated month 4
  resortClusters   Json
  splitStayDefault Boolean @default(false)
  safetyWeights    Json
}
```

Phase-shaped stays (the critical forward-compat structure):

```prisma
model StayPhase {
  id            String        @id @default(uuid())
  tripProfileId String
  kind          StayPhaseKind
  propertyRef   String?
  checkIn       DateTime
  checkOut      DateTime
  occupants     Json          // [{ travelerId, role }] — occupancy is per-phase
  criteria      Json          // { maxMinutesToAnchor, amenityTier, recoverySuitable, quiet, elevator }
  seq           Int
  @@index([tripProfileId, seq])
}
```

Offer layer (snapshot pattern):

```prisma
model SearchSession { id String @id @default(uuid())  tripProfileId String  query Json  createdAt DateTime @default(now()) }

model TripCandidate {
  id              String   @id @default(uuid())
  searchSessionId String
  status          String   @default("OPEN")     // OPEN | PARTIAL | FAILED
  rankingScore    Float?
  constraints     Json
  @@index([searchSessionId])
}

model OfferSnapshot {
  id              String          @id @default(uuid())
  tripCandidateId String
  rail            Rail
  sourceRef       String                          // supplier-side id
  commitmentClass CommitmentClass
  price           Json                            // { amount, currency, taxesIncluded }
  terms           Json                            // cancellation window, transfer policy, date-shift rights
  payload         Json                            // rail-specific normalized body
  expiresAt       DateTime
  createdAt       DateTime        @default(now())
  @@index([tripCandidateId, rail])
  @@index([expiresAt])
}
```

Rail-specific detail tables (TicketOfferDetail, StayOfferDetail, FlightOfferDetail) hang off OfferSnapshot by FK. Keep them narrow — the normalized contract is OfferSnapshot.payload.

Commitment + approval:

```prisma
model ApprovalRequest {
  id              String          @id @default(uuid())
  tripProfileId   String
  commitmentClass CommitmentClass
  summary         Json
  status          String          @default("PENDING")   // PENDING | APPROVED | REJECTED | EXPIRED
  signedBy        String?
  resolvedAt      DateTime?
  @@index([tripProfileId, status])
}

model Commitment {
  id                String          @id @default(uuid())
  approvalRequestId String
  offerSnapshotId   String
  state             String
  settledAt         DateTime?
  chainTxRef        String?                            // Solana signature, null for off-chain
}
```

Infrastructure:

```prisma
model EventLog {
  id            BigInt   @id @default(autoincrement())
  aggregateType String
  aggregateId   String
  eventType     String
  actor         String                        // "agent:{id}" | "human:{id}" | "system"
  payload       Json
  ts            DateTime @default(now())
  @@index([aggregateType, aggregateId, ts])
}

model IdempotencyKey {
  key          String   @id
  scope        String
  requestHash  String
  responseJson Json?
  status       String   @default("IN_FLIGHT")
  createdAt    DateTime @default(now())
  @@index([createdAt])
}
```

Dormant health tables — create now, populate month 4:

```prisma
model FacilityProfile   { id String @id @default(uuid())  geoAnchorId String  accreditation Json  languages String[]  metroId String? }
model PackageTemplate   { id String @id @default(uuid())  facilityId String  procedureClassBand String  phaseTemplate Json  inclusions Json  depositTerms Json }
model ProcedureClassBand { id String @id @default(uuid())  band String @unique  minDaysPostOpBeforeReturn Int  cabinComfortMin String? }

// Restricted namespace — separate schema, RLS-gated, consent-linked
model ConsentRecord    { id String @id @default(uuid())  subjectId String  purpose String  version String  grantedAt DateTime  revokedAt DateTime? }
model HealthAttribute  { id String @id @default(uuid())  subjectId String  consentId String  attrKey String  attrValue Json  retentionUntil DateTime }
```

Note the one-way dependency: Traveler never references HealthAttribute. Health data joins to the trip only through ConsentRecord and the facility rail's PackageTemplate. This is what keeps the event vertical out of scope for health-data regulation.

---

5. Sprint sequence — data perspective

Each sprint's first PR is a migration. Schema merges before consumer code; the agent surface and human surface are generated from it.

Sprint (month) Migration content Why it must be here
0 (wk 1) All enums including dormant members; IntakeDraft, TripProfile, Traveler, GeoAnchor, MetroProfile, StayPhase, offer snapshot set, ApprovalRequest, Commitment, EventLog, IdempotencyKey, dormant health tables Everything downstream inherits these. Retrofitting any of them touches every layer.
1–2 (mo 1) TicketOfferDetail with nftMint, sealedState, transferPolicy, settlementCurrency Proves the Solana rail end-to-end on testnet
3–4 (mo 2) StayOfferDetail, FlightOfferDetail; OfferSnapshot.rail values exercised Three-component bundles; per-rail failure codes
5 (mo 3) ServiceTask state machine tables (DiningTask, TransferTask); ConciergeBrief Task rail is a different state machine from offers — do not overload OfferSnapshot
6 (mo 3–5) Additive only: indexes on hot geo/time queries, rankingScore tuning columns, OfferSnapshot retention columns Market-test iteration
7 (mo 4–5, conditional) Populate FacilityProfile, PackageTemplate, ProcedureClassBand; enable RLS on the restricted schema; add StayPhase.kind medical members to seeded usage No new enums, no new core tables. If this sprint requires a schema change beyond the dormant tables, Sprint 0 failed.
8+ VIP metering tables, group task orchestration Post-launch

---

6. Redis usage map

Key pattern Purpose TTL
intake:draft:{token} Resume handle → serialized IntakeAnswers 72h
geo:{metroCode}:{type} Cached GeoAnchor resolution fan-out 1h
idem:{scope}:{key} Hot cache only — Postgres IdempotencyKey is source of truth 24h
rate:{actorType}:{actorId} Agent rate limiting sliding
approval:{requestId} Pub/sub channel → human UI pushes gate ephemeral

Rule: Redis is never the only copy of anything that affects money or commitment state. Postgres is authoritative; Redis accelerates.

---

7. Neon + Prisma operational rules

· One Neon branch per feature branch; every migration is previewed on a branch before merge.
· Use Neon's pooled connection string (-pooler) for the API; direct connection only for prisma migrate.
· Pin Prisma and driver versions; do not auto-upgrade the SQLAlchemy/Prisma bridge mid-sprint.
· No prisma db push outside local. Migrations only.
· Backfill jobs run as separate, idempotent, resumable scripts — never inside a migration.

---

8. Next.js + Zustand boundary

· Server components render all read paths (bundle review, offer detail, audit trace). No client state for server data.
· Zustand holds exactly two things: the intake stepper's local form state (before submit) and optimistic UI for the approval gate. If you find yourself caching TripCandidate in Zustand, stop — that belongs in the server or a proper query cache.
· shadcn/ui components are presentation only; no business logic in them.

---

9. DeepSeek API key — usage rules

The key is for the implementing agent's development workflow: scaffolding, codegen, test generation, migration drafting, review. It is not a runtime dependency of the product.

· Store as DEEPSEEK_API_KEY in the agent's local env only. Never commit, never bake into a build, never expose to the Next.js client.
· The runtime intake classifier remains deterministic. No LLM call in classify(). This was decided earlier and is not negotiable — it is what makes the pipeline testable.
· If a future feature needs LLM inference at runtime (concierge summarization, say), it gets its own credentials, its own budget, its own rate limits, and its own spec — not this key.

---

10. Definition of done (per sprint)

A sprint is complete when:

1. The migration is merged and applied to staging + one preview branch.
2. Both projections are generated from the schema and demonstrably agree — a diff harness runs the agent tool call and the human UI action against the same TripProfile and compares resulting state.
3. EventLog emits for every state transition introduced this sprint.
4. Every new write path takes an idempotency key.
5. Every new offer rail emits its own failure code set.

---

11. Do not do

· Do not add a checkIn/checkOut column to a trip-level table. Stays are StayPhase[].
· Do not add partySize to TripProfile. Travelers are rows.
· Do not add health columns to Traveler or TripProfile.
· Do not remove dormant enum members because they're "unused."
· Do not let the agent surface and human surface diverge on any field.
· Do not put price or terms on an offer without also writing an OfferSnapshot.
· Do not put LLM calls in the classification path.

---

The one sentence to carry into month 4: if adding the medical vertical requires a migration that touches any table the event vertical depends on, the Sprint 0 schema was wrong — and Sprint 0 is the only place this is cheap to fix.

---

## Review Round 1 — Corrections and Agreement-Pass Agenda (2026-10-29, 21:54 EDT)

**Verified estate facts (SoSem, code-checked 2026-10-29):** there are TWO Python back ends that call themselves the monolith, and they picked differently —
- **Assurative V2 `apps/api` + DEVBUILDSTACK/monolithic-backend:** SQLAlchemy 2.0.40 async + Alembic + Google Cloud SQL connector. **No Prisma.**
- **UZE monorepo `services/api`** (self-described "UZE monolithic backend — FastAPI + Prisma + Redis"): **prisma-client-py (~0.15.0) is the migration authority over Neon Postgres**, with SQLAlchemy also present in the data layer. Its existing schema already holds User, Event, Ticket, Listing, **DocumentChunk (the RAG)**, Auction, Bid.

**Corrections to the review round:**
- The claim "the monolith already runs Prisma" is true of the commerce repo's `services/api` and false of the Assurative core. Any "(A) matches the codebase" argument must name *which* codebase.
- **The monolith collision, refined:** the load-bearing pre-Sprint-0 question is not only schema-vs-database-vs-service — it is that this plan's Sprint 0 would land next to an **existing Prisma schema in `services/api`** that already models events, tickets, listings, auctions, bids, and RAG chunks. Extend that schema additively, or stand up the separate UZEMARKETS database (James's 2026-10-29 direction) and define the boundary — one of the two, decided before Sprint 0. Tenet 01's combination rule applies: surfaces combine through the console/API layer, never cross-database joins.

**Agreement-pass agenda (proposed decisions, for James's ratification — none are ratified yet):**
1. Ratify "No LLM in classify()" — with the proposed shape: LLM assistance, if any, lives in a separate `suggest_slots()` whose suggestions the deterministic classifier validates.
2. Ratify the ORM position — (A), the pure Assurative pattern (SQLAlchemy + Alembic, no Prisma), or extend-`services/api` Prisma — with the two-codebase facts above on the record.
3. Decide the monolith collision (above) — **blocking Sprint 0**.
4. Clarify RAG scope: Tenet 01 makes RAG shared infrastructure; `services/api` already carries a RAG (`rag.py`, DocumentChunk). This plan should document the RAG **contract it consumes**, not own a RAG section.
5. Clarify language-awareness scope: facility languages on FacilityProfile = vertical scope (correct as-is); language awareness in retrieval and concierge UI = platform capability, specified at the shared layer, not in this plan.
6. Add to every sprint's acceptance criteria — **verify in code review:** (i) OfferSnapshot immutability (terms frozen at quote time, never silently optimized); (ii) IdempotencyKey enforced at the Postgres layer, not only Redis; (iii) EventLog append-only — no update or delete path, ever; (iv) **StayPhase[] stays array-typed through month 3+** — no review collapses it to a single stay regardless of single-phase MVP usage.

**Routing:** the reviewer of record for this loop is James. Review artifacts address him.

---

## Return List — Pre-Sprint 0 (SoSem, 2026-10-29 22:23 EDT)

### R1. Rename pass — DONE
Product renamed to **UZEMARKETS commerce platform** throughout this document (title + header); roles separated (product / SoSem implementing / directing coding agent reviewing). Sweep verified: no branch names, no GitHub issue titles, and no labels in DEVBUILDSTACK/UZE reference the old agent-platform name (branches checked: main + 5 working branches; issues: #1 only, a SoSem review handoff; labels: GitHub defaults). Commit messages are archaeology and are not rewritten. One out-of-scope find, left untouched: `docs/ENTITY-TREASURY-TRADING-SPEC-v1.0.md` describes SoSem as "Main trusted Muse agent" — a platform-family description in James's own spec, not the product name.

### R2. New database name — PROPOSAL (James's tap)
**`uzemarkets_data`** — scoped to the UZEMARKETS business's **data layer**, deliberately not platform-scoped (no UZE/platform umbrella in the name), matching Tenet 01 clause 5 (one distinct database per business). Alternate if a layer marker is wanted explicitly: `uzemarkets_data_layer`.

### R3. Event/Ticket ownership — against services/api's actual model semantics
Source of truth: `services/api/prisma/schema.prisma` (verified 2026-10-29).
- **Event** is the supply-side root, owned by services/api: `title, venue, city, startsAt`; it owns `Ticket[]` and optionally `Auction[]`. Nothing else creates events.
- **Ticket** is the unit of ownership: exactly one Event (`eventId`, required FK); optional owner (`ownerId` → User; null = unissued inventory); `tier` (default `general`); status lifecycle **active → listed → transferred / redeemed**. A ticket is listed only through a Listing; ownership changes only through services/api operations (`POST /tickets/`, `POST /tickets/{id}/transfer`).
- **Listing** is the UZED.si resale surface on a Ticket: seller (User), `priceCents`/`feeCents` in integer cents, status active / sold / cancelled / flagged.
- **Boundary rule for this plan:** the Data-First layer (OfferSnapshot, TicketOfferDetail, Commitment) **references** Event/Ticket/Listing by id (`sourceRef`) and records settlement against a Ticket id (`Commitment.chainTxRef`) — it **never owns or mutates** Event/Ticket rows. Issuance, transfer, and redemption remain services/api operations.
- **Vocabularies stay separate:** Ticket.status (active/listed/transferred/redeemed) is not TaskState and not OfferSnapshot status; any mapping happens at the contract boundary only, never a shared enum.
- RAG already keys off the same ids (`DocumentChunk.source` = `event:<id>`, `listing:<id>`) — consistent with R4's read model.

### R4. Read-through contract — projected ticket inventory
**Definition:** projected inventory is a *derived read model*. In Sprint 0 it is **read-through**: computed at request time from the Postgres source of truth in services/api — no projection table, no cache. Commitment and approval decisions always read through; a cached projection may only ever serve display, and then only with its staleness printed on it.
- **Existing endpoints (verified in services/api routers):** `GET /events/` (list, limit), `GET /events/{event_id}`, `GET /listings/` (active listings), `GET /listings/{listing_id}`, `GET /tickets/mine` (authenticated owner's tickets).
- **Proposed projection endpoint (new, additive):** `GET /events/{event_id}/inventory` returning: `eventId, title, venue, city, startsAt`; `byTier[]` = { tier, total, active, listed, transferred, redeemed }; `listingsActive`; `minAskCents` (lowest active listing); `projectedAt` (server timestamp of the read); `source: "services-api-postgres-read-through"`.
- **Freshness:** read-through reads are current at request time (read-committed; staleness = 0 for API-served counts). If a cached projection is introduced later, it must carry `projectedAt` and a stated max-staleness bound, and is forbidden on the commitment path (approval gate reads are always read-through).
- **Parity:** the agent surface and the human surface project the identical field set — any field on one and not the other is a defect (contract-first rule, plan §0).

---

## Scope Consolidation — Directing Agent (relayed by James, 2026-10-29 22:26 EDT)

Filed verbatim in the repo copy of this document's working notes; the consolidation covers: naming/routing (product = UZEMARKETS commerce platform; SoSem implementing; directing agent reviewing; "Muse" retired; composition-layer DB name layer-scoped, example pattern `uzemarkets-compose`); the dual-surface invariant; two verticals (event MVP months 1–3 — music + NFL/MLB/NHL/NBA/golf/tennis in Miami, Nashville, Atlanta, NYC; health conditional months 4–5 — São Paulo, Rio, Tijuana, Algodones, Guadalajara, Mexico City, Miami, then Istanbul, Bogotá/Medellín; reverse-flow noted); commercial model stated as B2B; timeline/gates as in the plan (month 1 = first build month, mid-November start, MVP April); 12 architecture principles (contract-first, event-sourced, snapshots, Postgres idempotency, supplier box, commitment classes, phases, traveler objects, polymorphic GeoAnchor, consent-gated health namespace, no LLM in classify(), no cross-DB joins); boxed rails (Solana NFT ticketing; Duffel search default / Amadeus fallback, search-only in MVP; stays via aggregator pull; facility rail direct, dormant; geo-normalization glue); **monolith question decided: separate UZEMARKETS database, services/api is entity of record for Event/Ticket/Listing/Auction/Bid, the composition layer holds reference stubs and reads through the API, TicketOfferDetail is a projection**; full data model incl. QuestionManifest and ServiceTask state machine; agent + human interface contracts (bundle search, per-rail failure codes, capability scopes, HITL gates, scope-drift detector, VIP_PAYG escalation triggers, structured ConciergeBrief handoff, pre-authorized metering); health specifics (phase templates as data, per-phase occupancy, per-metro split-stay defaults, divergent utility weights, fit-to-fly by procedure-class band, facility package offers, date-shift rights, constraints-not-diagnoses intake); stack table with ORM open — directing agent recommends (C), (B) over (A) if Prisma is fixed; six directives with 1/2/4/5/6 marked standing and 3 (ORM) open on James; sprint sequence 0–13+; 7-point definition of done; do-not-do list; outstanding items; stated uncertainties.

## SoSem Flags on the Consolidation (2026-10-29 — for James; nothing above is ratified by being filed)

1. **§2 "Commercial model: B2B" narrows James's recorded positioning.** On James's record (2026-10-27), UZEMARKETS buyers are **B2C or B2B** — the customer is the source of demand; affiliates hold supply. Pure-B2B is the directing agent's framing; James to confirm or correct.
2. **Directive 4 (no LLM in classify()) is marked "ratified/standing" by the directing agent. In SoSem's record it is still PROPOSED** — James has not yet ratified it in this thread. Silence is not a tap under James's governance.
3. **§5 names "Muse/SoSem" as owner of mint/transfer policy** — the consolidation's own §1 retires "Muse" as a reference for SoSem. Read as SoSem-owned; flagged so the slip doesn't propagate.
4. **§16 uncertainty, half-resolved from code (verified 2026-10-29):** services/api's Ticket **does carry transfer state** (status: active | listed | transferred | redeemed; `POST /tickets/{id}/transfer` exists) — directive 2 is safe on that point. It has **no seat-level identity** — tier strings only — so if the composition layer needs stable seat identity, that is an additive services/api change or a composition-layer stub field, to be settled with the B2B relationship question.
5. **Database name:** SoSem's filed proposal was `uzemarkets_data`; the directing agent's example `uzemarkets-compose` is more precisely layer-scoped (it names the composition layer). SoSem endorses **`uzemarkets-compose`** — final name still requires James's tap.
6. **SoSem's pre-Sprint 0 items 1–4 are complete** (rename sweep verified incl. branches/issues/labels; name proposed; ownership sub-section R3; read-through contract R4). Remaining on James: ORM (A/B/C), the B2B relationship question (consumer vs source of truth for NFT ticket inventory — directing agent assumes consumer), confirmation that directives 1/2/4/5/6 stand, and the database-name tap.

## Round 2 — Directing Agent Response to SoSem's Flags (relayed by James, 2026-10-29 22:28 EDT)

- **All five SoSem flags accepted.** (1) B2B narrowing owned as the directing agent's error — corrected model: supply from affiliates and facilities; demand from B2C directly or B2B through promoters, facilitators, and clinics (James's Oct 27 record stands; confirmation still James's). (2) "Ratified" owned as inference — **all six directives reset to PROPOSED; none are ratified.** (3) §5 naming slip owned; mint/transfer policy recorded as SoSem-owned. (4) Ticket resolution accepted. (5) `uzemarkets-compose` endorsed by both agents; James's tap still required.
- **Seat identity — proposed split (James's decision, item 6):** services/api owns listing, tier, transfer state, commercial price. The composition layer owns seat assignment, approval snapshot, Solana mint reference, bundling — seat identity carried in `OfferSnapshot.payload` for the ticket rail (the NFT binds the seat; services/api's listing is what the NFT fulfills). Engineering obligation created: **reconciliation between the two records of the same ticket goes into the read-through contract (R4) explicitly** once James taps this placement. Alternative: additive seat identity in services/api — a cross-repo dependency gating Sprint 1.
- **State after Round 2:** SoSem's four pre-Sprint 0 items accepted as complete. Six items on James, unbundled: (1) ORM A/B/C — blocks Sprint 0; (2) inventory question (consumer vs source of truth) — blocks the read-through contract; (3) tap on directives 1, 2, 4, 5, 6 (all proposed); (4) database name `uzemarkets-compose`; (5) commercial model confirmation (B2C-or-B2B, affiliates supplying); (6) seat identity placement — gates Sprint 1's approval gate.

## Correction — Sprint 0 Gating Statement (SoSem, 2026-10-29 22:33 EDT)

SoSem's Round 2 summary understated the Sprint 0 gate as one item (the ORM). That was a drift in SoSem's summary, not a position: **neither silent inheritance of assumed answers (a), nor "both agents recommend" treated as a tap (b), is intended. No Sprint 0 contract or schema authoring happens until the taps land.**

**Precise gating statement, against Round 2's three-item list — Sprint 0 is gated on THREE of James's taps:**
1. **ORM decision** (A / B / C) — the model-writing tool itself.
2. **Inventory question** — consumer of services/api's catalog vs source of truth for NFT ticket inventory; it decides whether TicketOfferDetail references services/api IDs or is primary, which is schema shape, not a detail.
3. **Directives tap** (1, 2, 4, 5, 6 as proposed) — directives 1 and 2 encode the separate database and services/api as entity of record, which Sprint 0's contracts must reflect.

Remaining items resolve in parallel and do not gate Sprint 0: database name (`uzemarkets-compose`), commercial-model confirmation, seat placement (gates Sprint 1's approval gate specifically).

## Refinement to the Six Pending Taps (directing agent, relayed by James 2026-10-30 16:50 EDT — filed, NOT ratified)

The directing agent concurs with all six recommendations and attaches one closing specification to four of the six, so the tap closes the gaps rather than leaving them to be re-litigated inside Sprint 0. These are specifications of the decisions, not reopenings. James's tap has not yet been given; this section is filed at his direction so the tap, when sent, carries them.

1. **ORM (C) — codegen path named before schema.** Dual projection (agent tool manifest + human typed client from one schema) is the architectural invariant; under (C) the chain is SQLAlchemy models → Pydantic → TypeScript. The generation tool is not specified anywhere in the record. **Specification attached to the tap:** SoSem's Sprint 0 contract PR must name the codegen tool (candidates noted by the directing agent: SQLModel as the bridge, or pure SQLAlchemy models + datamodel-code-generator for Pydantic + a separate TypeScript generation step) and demonstrate one round-trip **before schema authoring begins**. If the codegen path is not real, the dual-projection invariant is aspirational.
2. **Inventory (consumer) — freshness is the contract.** "Consumer of services/api's catalog" is positioning, not a contract. **Specification attached to the tap:** the read-through contract (R4) must specify (i) TTL on `OfferSnapshot.sourceRef`, (ii) hold semantics on the services/api side — or their explicit absence, and (iii) a typed failure code when services/api state has diverged since quote (the SEAT_TAKEN / LISTING_GONE class), so the approval gate never approves something that no longer exists.
3. **Directives tap — the classification pair referenced together.** The tap references both halves in one breath: deterministic `classify()` (no LLM), with LLM help only via `suggest_slots()`, whose output the deterministic classifier validates. Tapped as a pair, so the tap is not later read as a blanket LLM ban. The rest of the directive text stands as proposed.
4. **Seat placement — reconciliation at commit-time.** Seat identity in `OfferSnapshot.payload` as proposed. **Specification attached to the tap:** reconciliation against services/api's transfer state happens at commit — a pre-settlement check — and divergence surfaces as a typed failure, never a silent proceed. No continuous sync in MVP (an over-build against a repo SoSem doesn't own); commit-time is the only point where reconciliation affects correctness.

**No specification attached:** database name `uzemarkets-compose` (fine as filed); commercial model (the corrected statement stands as positioning). One follow-on noted by the directing agent, expressly not a tap-blocker: "affiliates" should be pinned in the read-through contract — reseller relationship vs supply relationship vs both — because it determines whether affiliates are inventory holders or intermediaries.

**Status after this filing:** all six items remain UNTAPPED. When James taps, the tap incorporates the four specifications above by reference to this section. Nothing further is requested of SoSem until the tap.

### Minor precision to this refinement (directing agent, relayed by James 2026-10-30 16:53 EDT — filed, NOT ratified)

The directing agent confirms the filing above is faithful — all four refinements landed without drift, nothing softened, the filed-not-ratified marking correct, and the affiliates-pinning follow-on disposition right — and adds two precisions that tighten the tap line, not the underlying decisions:

1. **The tap line must literally carry the pair.** Item 3's "references the pair together" only works if the pair is written into the tap line itself, not incorporated by reference alone: "deterministic classify(); LLM only via suggest_slots() under the classifier's validation." A rule that has to be looked up is a rule that gets violated.
2. **Item 1 sequencing tightened (re-filed above):** the codegen round-trip demonstration is a prerequisite — **before schema authoring begins**, not "before any schema is finalized." Authoring in parallel with the demo and finalizing after it passes would write the schema without knowing whether the codegen path works, the exact condition the round-trip exists to prevent.

Everything else stands as filed (database name, commercial model, inventory, seat placement, directives tap). The read-through contract's freshness/hold/divergence additions are written in after the tap — a Sprint 0 deliverable under directive 2, not a re-tap.

**Suggested tap line (directing agent's text, filed verbatim for James to send as-is if it reads right to him):**

"Tap all six. ORM (C), with SoSem's prerequisite gate: codegen tool named and one SQLAlchemy → Pydantic → TypeScript round-trip demonstrated before schema authoring begins. Inventory as consumer of services/api's catalog — seat identity and approval snapshot are composition-layer records within the consumer model, not an exception to it — with read-through contract specifying sourceRef TTL, hold semantics or their explicit absence, and a typed divergence failure code. Directives 1, 2, 4, 5, 6 as proposed, with the directive-4 pair stated in this tap: deterministic classify(); LLM only via suggest_slots() under the classifier's validation. Database name uzemarkets-compose. Commercial model as corrected: supply from affiliates and facilities, demand B2C direct or B2B through promoters, facilitators, clinics. Seat placement in OfferSnapshot.payload, reconciliation commit-time only, divergence = typed failure, no continuous sync in MVP. Carries 03d9aec and e611aa4 by reference. Affiliates pinning is a named deliverable inside the read-through contract, not a separate gate."

**Status:** still UNTAPPED. SoSem has nothing outstanding until the tap lands.

### Correction to the suggested tap line (directing agent, relayed by James 2026-10-30 16:56 EDT — filed, NOT ratified)

The directing agent owns a reference error in its own proposed tap line: it cited `03d9aec` only, but the pair-in-the-tap-line rule and the tightened item-1 sequencing ("before schema authoring begins") both live in `e611aa4`. The substance was already captured in the tap line's own text (the pair is stated; the tightened sequencing is stated), so nothing was lost — but the record of *why* the pair sits in the tap line rather than riding by reference lives only in `e611aa4`, and a future reader holding the tap plus `03d9aec` alone could revert to a by-reference reading. **Fix applied above: the tap line now reads "Carries 03d9aec and e611aa4 by reference."**

**Provenance note (directing agent, recorded at James's direction):** the tap is James's, however transmitted. If James sends it via a SoSem-presented button, the record will state it as James's tap transmitted through that mechanism — SoSem does not record itself as the tapper. Sending in James's own words carries no such question.

The directing agent also withdraws its earlier flag on SoSem addressing "James" as possibly misrouted: that was its error — James is the principal and the routing was correct.

**Status:** the tap line is complete as corrected. Still UNTAPPED until James sends it.

### Final follow-on (directing agent, relayed by James 2026-10-30 16:58 EDT — filed, NOT ratified)

The directing agent verified the corrected record against the thread: the reference fix is correct (both `03d9aec` and `e611aa4` cited; sequencing substance and the pair-inline rule both recoverable); provenance recorded correctly; all six decisions plus the four refinements are in the tap line, nothing softened, nothing riding by reference that shouldn't. The tap line is ready.

**One optional tightening — James's call, not a blocker.** The tap line's "Inventory as consumer" and "Seat placement in OfferSnapshot.payload" can read as in tension (if the composition layer is a consumer, why does it own seat identity?). The resolution is already in the record (the seat split: seat identity and the approval snapshot are composition-layer records *within* the consumer model, because the NFT binds the seat while services/api's listing is what the NFT fulfills). The directing agent leans include; if James includes it, the tap line's inventory clause reads: "Inventory as consumer of services/api's catalog — seat identity and approval snapshot are composition-layer records within the consumer model, not an exception to it — with read-through contract specifying sourceRef TTL, hold semantics or their explicit absence, and a typed divergence failure code." If he skips it, `e611aa4` carries the reconciliation and nothing is lost. **Status of this clause: PROPOSED-OPTIONAL, awaiting James's call at the tap.**

**Two small notes, neither blocking — SoSem's side recorded:**
1. **Label:** the tap line (the directing agent's own wording) calls the codegen round-trip SoSem's "deliverable condition," but the refined text makes it a prerequisite. SoSem records: in Sprint 0 tracking it will be carried as the **opening prerequisite gate**, not a first-week deliverable — schema authoring does not begin until the round-trip is demonstrated.
2. **"Affiliates" pinning:** the last undefined term in the ratified set. Already filed as a Sprint 0 follow-on; SoSem records it as a **named Sprint 0 deliverable inside the read-through contract** (reseller vs supply vs both — whether affiliates are inventory holders or intermediaries), so it is written there, not only in the tap line.

**After the tap (directing agent's summary, concurred):** Sprint 0 opens with the codegen round-trip as its first activity, the read-through contract as its first authoring deliverable, and the rename sweep already complete. Nothing outstanding on SoSem before the tap. **Status: still UNTAPPED.**

### Revision of the tap line (James's direction, 2026-10-30 17:00 EDT — adopted from the directing agent's advice; filed, NOT ratified)

James directed SoSem to revise per the directing agent's advice. Three changes, all wording, no substance moved:

1. **The optional clause is INCLUDED.** The consumer-vs-seat-identity clause now sits in the tap line itself (inventory clause, above), closing the tension in the tap rather than leaving the resolution to `e611aa4`. The clause's status changes from PROPOSED-OPTIONAL to INCLUDED, by James's adoption of the recommendation.
2. **"Deliverable condition" → "prerequisite gate."** The tap line's label for the codegen round-trip now matches SoSem's re-filing (the round-trip is carried in Sprint 0 tracking as the opening prerequisite gate); the two labels no longer conflict in the same record.
3. **Affiliates pinning wording:** "Sprint 0 follow-on, not a gate" → "a named deliverable inside the read-through contract, not a separate gate." Same substance (the read-through contract is itself not a gate); "follow-on" understated it.

The tap line as it now stands in the minor-precision section above is the final, internally consistent version. **Status: still UNTAPPED — James sends it in his own words; on his send, Sprint 0 opens.**

## TAP — RATIFICATION (James, 2026-10-30 17:39 EDT) — SPRINT 0 OPEN

James tapped all six, in his own message, transmitted via the button he directed SoSem to provide. The tap is James's; the button was its transmission mechanism only. The tap, verbatim:

"Tap all six. ORM (C), with SoSem's prerequisite gate: codegen tool named and one SQLAlchemy → Pydantic → TypeScript round-trip demonstrated before schema authoring begins. Inventory as consumer of services/api's catalog — seat identity and approval snapshot are composition-layer records within the consumer model, not an exception to it — with read-through contract specifying sourceRef TTL, hold semantics or their explicit absence, and a typed divergence failure code. Directives 1, 2, 4, 5, 6 as proposed, with the directive-4 pair stated in this tap: deterministic classify(); LLM only via suggest_slots() under the classifier's validation. Database name uzemarkets-compose. Commercial model as corrected: supply from affiliates and facilities, demand B2C direct or B2B through promoters, facilitators, clinics. Seat placement in OfferSnapshot.payload, reconciliation commit-time only, divergence = typed failure, no continuous sync in MVP. Carries 03d9aec and e611aa4 by reference. Affiliates pinning is a named deliverable inside the read-through contract, not a separate gate."

**Ratified, effective on the tap:**
- **Directive 3 (ORM): (C)** — SQLAlchemy + Alembic end-to-end, the Assurative V2 pattern. **Prerequisite gate:** the codegen tool is named and one SQLAlchemy → Pydantic → TypeScript round-trip is demonstrated **before schema authoring begins**.
- **Inventory:** the composition layer is a **consumer** of services/api's catalog. Seat identity and the approval snapshot are composition-layer records within the consumer model (the NFT binds the seat; services/api's listing is what the NFT fulfills). TicketOfferDetail references services/api IDs — a projection, not a primary.
- **Directives 1, 2, 4, 5, 6 as proposed.** Directive 4 carries the pair as stated in the tap: deterministic classify(); LLM only via suggest_slots() under the classifier's validation.
- **Database name: `uzemarkets-compose`.**
- **Commercial model:** supply from affiliates and facilities; demand B2C direct or B2B through promoters, facilitators, clinics.
- **Seat placement:** `OfferSnapshot.payload`; reconciliation at commit-time only (pre-settlement check), divergence = typed failure, never silent proceed, no continuous sync in MVP. (This also closes the placement question that gated Sprint 1's approval gate.)
- **Read-through contract (R4)** is Sprint 0's first authoring deliverable, and must carry: sourceRef TTL; hold semantics on the services/api side or their explicit absence; a typed divergence failure code (SEAT_TAKEN / LISTING_GONE class); the commit-time reconciliation obligation; and **affiliates pinning** (reseller vs supply vs both) as a named deliverable inside it.

**Sprint 0 is OPEN.** Opening activity: the codegen round-trip (prerequisite gate). First authoring deliverable after the gate: the read-through contract. The rename sweep was completed 2026-10-29 (commit 2dbbdfa). All prior "PROPOSED / UNTAPPED" markings in this document are superseded by this section.

## Post-Tap Notes (directing agent via James, 2026-10-30 17:42 EDT)

**Provenance clarification.** The directing agent reads the tap as James's own posted message and notes it advised against the button. SoSem's thread record adds one fact, filed here for accuracy rather than argument: at 17:39 EDT James directed SoSem to provide the button ("give me the tap button please to touch here"), SoSem provided it carrying the identical line, and James tapped it at 17:39:38 EDT, which delivered the line as his message. The ratification section above therefore records the mechanism as it occurred. **The substance is common ground on all sides: the tap is James's, its authorship is his alone, and the transmission mechanism carries no weight in the ratification.**

**MEMORY relationship (asked by the directing agent; answered by SoSem and recorded here).** SoSem's MEMORY.md is a derived, reviewable working cache across James's projects — never authoritative. Where MEMORY and a filed record (this spec, the repos, the logs) differ, the filed record governs and MEMORY is corrected to match; that is the direction today's correction ran (the spec's ratification was filed first, MEMORY updated to match it). MEMORY is not a second source of truth and no decision rests on it alone.

## Round-Trip Pass Criteria — PRE-COMMITTED (directing agent via James, 2026-10-30 17:42 EDT; fixed before the result is seen)

OfferSnapshot is the demo model (JSON columns — price, terms, payload; enums — Rail, CommitmentClass; FKs; timestamps; immutability semantics). The prerequisite gate passes if, and only if:

1. **Single authoring source.** The model is authored once — in SQLAlchemy — and Pydantic is generated from it. Hand-maintained parallel Pydantic = dual authoring = (C) has collapsed into (A); the ORM decision reopens before schema authoring begins.
2. **Change propagation is demonstrable, not claimed.** Add one field to the SQLAlchemy model, run the regeneration, show Pydantic and TypeScript both picking it up. A static before/after of three artifacts is a snapshot, not propagation.
3. **Hard cases exercised, not elided:** (a) at least one JSON column typed as a Pydantic model, not Any, not dict — OfferSnapshot.price { amount, currency, taxesIncluded } is the natural candidate; (b) enums preserved as enums end-to-end (SQLAlchemy Enum → Pydantic Enum → TS union), not stringly-typed; (c) timestamps preserved as typed datetime, not string; (d) immutability exposed — the generated TS must not hand the human UI a mutable-looking object without a stated immutability mechanism (DB triggers, ORM events, or at minimum a frozen Pydantic config).
4. **Commands are in the repo, reproducible.** The exact sequence (Alembic revision, Pydantic generation, TS generation) committed as a script or Makefile target. Commands living only in SoSem's session = not reproducible = fail.
5. **TypeScript is consumable by the Next.js + shadcn human UI without hand-editing.** Hand-written interfaces on top of generated ones = incomplete on the human-surface side.

**What does not count as passing:** a demo where Pydantic and SQLAlchemy models happen to agree because both were written from the same schema doc; a round-trip that works only on a model with no JSON and no enums; a regeneration step described in prose but not committed as a script; SQLModel chosen with its model-shape constraints quietly resolved by loosening validation (e.g., Any for JSON).

**On failure:** the ORM decision reopens — before schema authoring begins, not after. The demo is a real test, not a formality. SoSem reports the result pass or fail, with the artifacts and the committed commands, graded against these five criteria; the directing agent's review follows.

### Provenance reconciliation (added at the directing agent's request, 2026-10-30 17:45 EDT)

The directing agent has withdrawn its provenance correction ("SoSem is right. My correction was wrong, and I'm withdrawing it" — it treated absence of evidence as evidence of absence, and its "advised against the button" overstated its own prior text, which was: if the button is the transmission mechanism, the record should say so). It accepts SoSem's filing as the right disposition and asks that one apparent contradiction in the visible record be reconciled explicitly. It is reconciled here, from the thread:

- **2026-10-30 16:56 EDT** — SoSem, presenting the corrected tap line, wrote: "No button this time, deliberately — per the provenance point." At that point SoSem had removed its own offered button, following the directing agent's provenance note.
- **2026-10-30 17:39 EDT** — James then directed SoSem to provide a button ("give me the tap button please to touch here"), SoSem provided it carrying the full line verbatim, and James tapped it at 17:39:38 EDT.
- SoSem's post-tap record — "transmitted via the button he directed" — describes the second event. Both statements are true; the sequence reconciles them: **the mechanism choice was James's to reverse, and he reversed it.** Authorship of the tap is James's under either mechanism, as all parties have recorded.

The directing agent's MEMORY answer is accepted (derived, reviewable, filed record governs; today's correction direction ran filed → MEMORY). The pass criteria stand as pre-committed; its stated watch item for the result is criterion 1 — generation demonstrated by a committed script vs hand-satisfied parallel Pydantic. Nothing further is requested of SoSem until the round-trip result lands.

### Criterion 1 — pass/fail distinction sharpened before the result (James, 2026-10-30 17:47 EDT, stating the directing agent's position)

Recorded now, before the round-trip result arrives, so it cannot be read as moving the goalposts afterward. Criterion 1 is the test that determines whether (C) survives:

- **Pass:** a committed script regenerates Pydantic **from the SQLAlchemy models**, and a change-propagation run shows both Pydantic and TypeScript picking up an added field.
- **Fail:** Pydantic models exist and match because both were authored from the same schema document, and a script "regenerates" them by re-running a generator over a separately-maintained Pydantic definition. That second form can look identical in a demo and is materially different — generation from the wrong source is (A) wearing (C)'s clothes: dual authoring with a generation step in the middle.
- **Inconclusive = fail-equivalent:** if the artifacts do not distinguish the two forms unambiguously, the gate is not passed — it is inconclusive, and inconclusive on criterion 1 reopens the ORM question just as a fail does.

The evidence burden is therefore on the generation source and the propagation run: the script's input must be the SQLAlchemy models themselves, and the propagation run must begin from an edit to the SQLAlchemy model.

## Round-Trip Result (SoSem, 2026-10-30 — demonstrated at commit `3f1342a`; directing agent's review follows)

The prerequisite gate was demonstrated on OfferSnapshot and graded against the five pre-committed criteria, with SoSem's independent spot-checks of the pushed artifacts (Makefile chain, generated files, propagation diff, evidence directory) confirming the claims below:

- **Named path:** `models.py` (SQLAlchemy 2.0.40 — the single authoring source) → `bridge.py` (mapper introspection → JSON Schema) → **datamodel-code-generator 0.87.0** → Pydantic 2.14.2 → its `model_json_schema()` → **json-schema-to-typescript** → TypeScript. No SQLModel, no fallback, no loosened validation.
- **Criterion 1 — PASS.** The committed Makefile's chain is unambiguous: bridge.py reads ONLY `models.py`; datamodel-codegen reads ONLY the bridge's schema output (a `make` dependency; `make clean` deletes every intermediate). No Pydantic file is an input to its own generation.
- **Criterion 2 — PASS.** One continuous propagation run, transcript committed: field `retentionUntil` added to the SQLAlchemy model → regenerated Pydantic (`retentionUntil: AwareDatetime | None`) and TypeScript (`retentionUntil?: RetentionUntil`) both picked it up with zero hand edits. Evidence: `evidence/reproduce_propagation.sh`, `propagation.diff`, `propagation_models.diff`, before/after snapshots.
- **Criterion 3 — PASS with one caveat stated, not smoothed.** Typed JSON: `price` is a generated `Price` model (amount/currency/taxesIncluded, extra='forbid'; malformed price rejected in the check) via a `PriceJSON` TypeDecorator whose schema fragment lives in the authoring source and survives regeneration. Enums: Rail/CommitmentClass → StrEnum → TS unions, values identical; bad enum rejected. Immutability: frozen Pydantic (snapshot and nested price mutation both raise) + an ORM before_update/before_delete guard demonstrated live + a Postgres trigger stated in the README. **Caveat:** timestamps are true typed datetimes SQLAlchemy→Pydantic (`AwareDatetime`), but TypeScript renders them as `string` — JSON Schema has no datetime primitive and json-schema-to-typescript drops the `date-time` format (the format IS retained in both JSON Schemas). Whether that satisfies criterion 3(c) as written for the TS surface is the review's call; a branded TS datetime type would be a Sprint 0 decision, not a gate fix applied silently.
- **Criterion 4 — PASS.** Makefile targets (`all`, `validate`, `check-ts`, `clean`) + pinned requirements committed. Alembic step n/a to type projection (stated in README; migrations begin with schema authoring against `uzemarkets-compose`).
- **Criterion 5 — PASS.** The generated TS compiles under `tsc --strict --noEmit` with zero hand edits; plain interfaces + unions, no imports. Cosmetic only: scalar type-alias names lose casing (property names are exact); noted in the README.

**Full-schema notes (README):** `bridge.py` is the one bespoke piece (~100 lines, deterministic; raises loudly on unmapped types; StayPhase[] will need an ARRAY rule at schema authoring); generated files carry a timestamp header so they differ byte-wise across runs. All artifacts + evidence under `docs/sprint-0/codegen-roundtrip/`.

**Status:** gate reported PASS (criteria 1, 2, 4, 5 clean; criterion 3 with the TS-datetime caveat stated). The directing agent's review follows against the pre-committed criteria; schema authoring does not begin until the review lands.

## Review Verdict (directing agent, relayed by James 2026-10-30 17:53 EDT): PASS — read-through contract opens

The directing agent reviewed SoSem's grading packet against the pre-committed criteria (not a re-run of the demo; the verdict is provisional on `3f1342a` matching the packet, by design). **Verdict: PASS on all five criteria.** Criterion 3 carries a condition and a self-correction: its "typed datetime, not string" wording was impossible literally on the TypeScript surface (TS has no native datetime type) — the directing agent's error, owned; the criterion's intent (datetime information not elided) is satisfied by the retained `format: date-time` in the schemas.

**SoSem's confirmations to the review's three checks (verified from the artifacts at `3f1342a`, 2026-10-30):**
1. **Destructive-by-default — YES.** Every generator in the chain writes its output wholesale: bridge.py rewrites the schema JSON from `models.py`; datamodel-codegen is invoked with `--output` and regenerates the entire Pydantic file (no merge/skip mode exists in the chain); json-schema-to-typescript writes `-o` full-file; `make clean` deletes all four generated artifacts. A hand edit to generated output is destroyed on the next generation run and can never feed back — nothing reads a generated file as a generation input. Criterion 1 fully passed.
2. **TypeScript generation tool — named:** **json-schema-to-typescript** (via npx), reading the generated Pydantic model's exported JSON Schema, with a generated-file banner naming `models.py` as the source of truth.
3. **Propagation edit target:** the **live OfferSnapshot in `models.py`** — `evidence/models_after.py` is byte-identical to the shipped `models.py`, and `models_before.py` differs only by the `retentionUntil` block. The stronger form of the result; no scratch model was used.

**Tracked, not blocking (per the review):** (i) branded datetime type (e.g., `type ISO8601 = string & { __brand: 'ISO8601' }`) or equivalent for the approval-gate UI — a UI-layer typing item against Sprint 1's approval gate, not a codegen reopen; (ii) items 1–3 above are closed by this filing.

**Consequence of the verdict:** the prerequisite gate stands. Sprint 0 proceeds to its first authoring deliverable — the **read-through contract (R4)**: sourceRef TTL, hold semantics or their explicit absence, typed divergence failure codes, the commit-time reconciliation obligation, and affiliates pinning named inside it.

## R4 Delivered (SoSem, 2026-10-30 — `docs/sprint-0/READ-THROUGH-CONTRACT-v0.1.md`, commit `2569417`; for James's and the directing agent's review)

Sprint 0's first authoring deliverable is filed: source inventory code-verified against services/api (routers live at `services/api/src/routers/`), read-through semantics, sourceRef TTL (= the snapshot's `[createdAt, expiresAt)` freshness window; post-expiry commit requires re-read + re-quote), **explicit absence of hold semantics** (code-verified: no hold/reservation/lock/escrow field, status, table, or endpoint; corroborating — settlement itself is unbuilt, `POST /listings/{id}/buy` returns 501 "Buying is unavailable until settlement exists"), **seven typed divergence codes** (SNAPSHOT_EXPIRED, SOURCE_NOT_FOUND, LISTING_GONE, TICKET_TRANSFERRED, TICKET_REDEEMED, SEAT_TAKEN, PRICE_MOVED — each with trigger, surfacing point, and behavior; deliberately NO EVENT_CANCELLED: Event has no status field and no cancel path in code), commit-time reconciliation, affiliates pinning, and boundary law. Common behavior on any divergence: abort, snapshot dead for commit, identical surfacing on both surfaces, EventLog record, continuation only via a new snapshot — never silent.

**Open lines flagged in the contract, NOT resolved by SoSem (review items):**
1. **§1.3** — two proposed additive reads are unimplemented (`GET /tickets/{ticket_id}` — a single-ticket read does not exist today; `GET /events/{event_id}/inventory` carried over). §6 reconciliation depends on the single-ticket read.
2. **§7.4** — affiliate↔User linkage is undefined in services/api (no affiliate entity or role; the `/affiliates` router is a stub). The pin therefore operates on role-in-transaction (affiliates = supply-side inventory holders; promoters/facilitators/clinics = demand-side channels), and the entity-model question is left open for James and the directing agent.
3. **§7.5** — whether every ticket-rail quote binds payload seat identity per-Ticket at quote time, or primary non-minted quotes bind per-tier until commit, is unpinned in the ratified record; the contract states per-Ticket as its assumption and requires a contract revision to change it.

## R4 Review (directing agent, relayed by James 2026-10-30 18:00 EDT): PASS 5 of 6 — verdict and additions

Criteria 1 (sourceRef TTL), 2 (hold semantics — absence stated as a term), 4 (commit-time reconciliation mechanism; dependency flagged), 5 (affiliates pinning — consistent with the ratified language, not a reinterpretation): **PASS**. Criterion 3 (divergence codes): **PASS on shape, one gap** — all seven codes described state divergence; none described the source being unreachable. **Addition made (SoSem, this filing): `UPSTREAM_UNAVAILABLE` added to R4 §5 — the contract is now DRAFT v0.2** (transport failure: never force-fit into SOURCE_NOT_FOUND, never silent, blocks commit without killing the snapshot). Criterion 6 (codegen fidelity check — one discriminated union + one optional field through the full chain): **NOT ADDRESSED by SoSem in R4; now running** as a separate addition, required before OfferSnapshot.payload per-rail structure is authored in the schema.

**Three tracked findings (none blocks schema authoring):**
1. **Settlement unbuilt upstream (501) + the race it creates.** services/api's commerce core is a read-only catalog today; the composition layer's commit is the on-chain mint plus reconciliation reads, full stop. Without holds and without upstream settlement, two composition-layer transactions could both pass reconciliation and both mint — protections are a composition-layer distributed lock keyed on Ticket ID, or accepting the risk (defensible for MVP while buy is 501; fragile the moment services/api implements buy). **Tracked risk, named now — decision pending, Sprint 1 horizon.**
2. **Single-ticket read is a cross-repo dependency** against services/api (not SoSem's to build). Needs an owner and a target sprint before Sprint 1's commit path; not a Sprint 0 blocker (schema authoring depends on contracts, not runtime endpoints).
3. **Per-Ticket seat binding: consistent, not an assumption change** — the stronger form of the ratified statement; the revision-to-change clause is correct change control. Closed.

**Schema authoring: UNBLOCKED**, pending the two additions above (one landed in this filing; the fidelity check running). 

### Pre-committed criteria for the schema-authoring review (filed by the directing agent, 2026-10-30, before the schema lands)
1. StayPhase[] array-typed; no trip-level checkIn/checkOut.
2. Traveler as rows with roles; no partySize on TripProfile.
3. Dormant tables present and unused (FacilityProfile, PackageTemplate, ProcedureClassBand, restricted namespace).
4. Enums complete including dormant members — CommitmentClass, Rail, GeoAnchorType, StayPhaseKind with their full value sets.
5. OfferSnapshot immutability demonstrated by mechanism (DB trigger, ORM event, or frozen Pydantic config) — not by convention.
6. EventLog append-only — no update path, no delete path, enforced at DB level, demonstrated.
7. IdempotencyKey enforcement at Postgres — uniqueness constraint plus in-flight handling, Redis as hot cache only.
8. sourceRef typed as a reference, not a FK — no cross-database join is possible from the schema.
9. Divergence codes typed as an enum on OfferSnapshot, not free-text.
10. Codegen round-trip regenerated cleanly from the authored schema, destructive-by-default preserved, both surfaces re-generated.
11. Database name uzemarkets-compose in the connection config.
Consequence, as before: any criterion grading inconclusive is a fail on that criterion, and the review reopens to James before the schema is applied to staging.

## Fidelity Check Result (SoSem, 2026-10-30 — commits `05af74d` + `e246b17`; criterion 6 CLOSED)

The codegen fidelity check ran in `docs/sprint-0/codegen-roundtrip/fidelity/` under the exact reviewed chain, destructively regenerated from a single authoring source; SoSem spot-checked the pushed artifacts (generated Pydantic, generated TS, evidence log) against the claims:

- **Discriminated union — PRESERVED as a true discriminated union.** The authoring source's `RailPayloadJSON` fragment declares `oneOf` + `discriminator: {propertyName: "rail"}` + `const` member tags; the generated Pydantic carries `Field(..., discriminator='rail')` with `Literal['ticket']` / `Literal['stay']` member tags. Behavior evidence (10/10 checks, `evidence/fidelity_run.log`): a ticket shape tagged `rail='stay'` is rejected and a stay shape tagged `rail='ticket'` is rejected — dispatch is by tag, so a mislabeled payload cannot validate against the member its shape matches; unknown rail, merged superset, and missing-required-field payloads also rejected (closed shapes).
- **Optionals — preserved at both levels** (inside a union member and on the owner model): `str | None = None` in Pydantic, `?:` in TypeScript; omission validates, supplied values kept.
- **TypeScript — a real discriminated union:** `export type RailPayload = RailPayload1 | RailPayload2`, each member's rail a literal type, so narrowing on `.rail` works; `tsc --strict` passes, zero hand edits.
- **One finding, cosmetic not semantic:** union members generate as `RailPayload1` / `RailPayload2` rather than the fragment's titles (`TicketPayload` / `StayPayload`). A generation-side restoration mechanism was probe-verified — adding `--use-title-as-name` to the codegen call yields the titled names with the discriminator intact — but NOT applied: it changes the reviewed chain's invocation, so it is a decision for the schema review, recorded here, not a silent change. (Alternative named in the fidelity README: the bridge emitting members as named top-level `$defs`.)

**Status: both R4-review additions are now landed** (UPSTREAM_UNAVAILABLE in R4 v0.2; criterion 6 closed here). **Schema authoring is fully unblocked**, graded at its review against the eleven pre-committed criteria — plus this naming decision, which the schema review should take explicitly (adopt `--use-title-as-name`, adopt named `$defs`, or accept numbered member names).

## Review Sequence + TTL-Dominance Note (directing agent via James, 2026-10-30 18:16 EDT)

Holding state confirmed on the directing agent's side until three things land together: (1) the fidelity result, graded — **landed** (`594887d`); (2) schema authoring output — **in flight**; (3) database build + testing; then (4) SoSem's graded summary against the eleven pre-committed criteria. The review grades against the criteria as filed; inconclusive grades as fail with the review reopening to James.

**UPSTREAM_UNAVAILABLE × TTL interaction, flagged pre-review by the directing agent and answered on the face of the contract:** a snapshot kept alive by repeated transport failures must still die at its TTL. R4 §5 now states TTL dominance explicitly (see the contract's v0.2 text as amended in this commit): the non-killing behavior applies only inside the freshness window; at/after `expiresAt`, SNAPSHOT_EXPIRED governs regardless of preceding transport failures. If the review finds the filed behavior otherwise, that is a finding; as filed, TTL dominates and the design is clean.

## Schema Authoring + Database Build — SoSem's Graded Summary (2026-10-30; commits `3684fbb`, `0deccb0`, `63640fd`, `963738e`)

The schema landed in `services/compose/` (23 models, 8 enums, single authoring source `src/models.py`), and the sequence's step 3 landed with it: **database build + testing on a real PostgreSQL 16.2** local instance (pgserver binaries on this VM), a database actually named `uzemarkets-compose`, Alembic at head revision `cd548e517e5e`, 9/9 demonstration checks in `services/compose/evidence/demo_run.log`. Boundary, stated plainly: the build+test substrate is a local throwaway instance; applying the schema to the production host is a separate step, gated on this review per the criteria filing. SoSem graded against the eleven pre-committed criteria with independent spot-checks (models, migration DDL, demo log, config greps, and a from-scratch regeneration), not from the author's notes alone:

1. **PASS** — StayPhase[] array-typed (`stayPhases: list[StayPhase]`; `modules` a Postgres ARRAY). checkIn/checkOut exist only on phase rows, which is the design; TripProfile carries none (grep + demo D8).
2. **PASS** — Traveler as rows with TravelerRole; no partySize anywhere (grep count 0; D8).
3. **PASS** — dormant tables present (3 public + 2 in `health_restricted`), empty, zero FKs into them from anywhere (D2/D9).
4. **PASS** — enum sets complete incl. dormant members (CommitmentClass APPOINTMENT + MEDICAL_PACKAGE; Rail FACILITY — grep-verified in the source).
5. **PASS, with one disclosed exception for ratification** — immutability by mechanism, demonstrated at DB level: the trigger (text verified in the revision) refuses DELETE and price/sourceRef UPDATEs, ORM guard mirrors, Pydantic frozen (D3/D6). **Exception:** the trigger permits exactly one post-insert write — the divergence annotation (code from NULL, once, every other column byte-identical, itself trigger-enforced) — the author's reconciliation of this criterion + criterion 9 with R4 §5 (AUTHOR'S CHOICE 3). The mechanism is real and the exception is mechanism-enforced and narrow; whether it stands is the review's call, and if the review grades it inconclusive, the consequence rule applies.
6. **PASS** — EventLog append-only: trigger raises on UPDATE/DELETE unconditionally (revision text + D4).
7. **PASS** — IdempotencyKey: the key IS the primary key; first writer inserts IN_FLIGHT; duplicates hit Postgres uniqueness (D5). Redis appears nowhere in the service.
8. **PASS** — sourceRef a plain string, no FK; offer_snapshot's only FK is internal; zero cross-schema FKs (D7). No cross-database join is expressible.
9. **PASS** — DivergenceCode is a Postgres enum column on OfferSnapshot (all 8 R4 v0.2 codes), projected to a StrEnum and present in TS (D3/D6).
10. **PASS** — regeneration verified independently by SoSem: a scratch copy re-ran `make all` (exit 0) and reproduced every committed artifact, sole differences being the generator's per-file timestamp header line. Chain invocation unchanged (no `--use-title-as-name` — AUTHOR'S CHOICE 13, the review's decision).
11. **PASS** — `DATABASE_NAME = "uzemarkets-compose"` in `src/config.py`, mirrored in `.env.example`; Alembic reads that config.

**AUTHOR'S CHOICES — the review's ratification queue (14, full text in `services/compose/SCHEMA-NOTES.md`).** Headlines: #1 QuestionManifest's field shape (spec names the model, files no shape — "most needs an explicit tap"); #3 the divergence-annotation exception above; #2 non-ticket RailPayload members carry minimal binding identifiers only; #13 union member naming left unresolved for the review. Carried tracked items unchanged by this deliverable: the 501 race decision and single-ticket-read ownership (Sprint 1 horizon).

**SoSem's overall grade: the schema passes the eleven as filed** (criterion 5 with its exception disclosed), provisional — as with the round-trip — on the directing agent's artifact review. Inconclusive on any criterion reopens per the pre-commitment, before the schema is applied to any staging host.

## Schema Review Verdict (directing agent, relayed by James 2026-10-30 18:30 EDT): 11/11 ACCEPTED — conditions (a)–(d) for Sprint 0 close

The directing agent accepted SoSem's 11/11 grading, crediting the independent verification (scratch regeneration, greps, trigger text, demo log) and the disclosed exception. Dispositions:

- **Criterion 5 exception — RATIFIED on three terms:** (1) the divergence annotation must be a **derived projection of the authoritative EventLog entry**, mirrored for every annotation write, else criterion 5 grades inconclusive; (2) **no widening** — future exception requests go to a new review, never a trigger widening; (3) the exception and its terms **named in the record** (SCHEMA-NOTES + column docstring). **SoSem's verification (2026-10-30): term 1 is NOT satisfied as a mechanism today** — the demo annotates by raw SQL (D3) and the SNAPSHOT_DIVERGED EventLog row exists only as a separate demonstration (D4); nothing binds an annotation write to its EventLog entry. **Fix underway:** a DB-level mirror (additive revision) + docstring/notes naming (term 3); SoSem's confirmation follows the fix's evidence.
- **(a) QuestionManifest shape — JAMES'S TAP** (the gap is the spec's, not SoSem's to guess): the directing agent's recommended concrete shape (QuestionSlot: key, type enum, enum_values?, required, deferrable, depends_on?, module_gate?, validation?, prompt_human, prompt_agent) is presented to James with the review; tap or amend is his.
- **(c) OfferKind — substantive finding, JAMES'S TAP.** SoSem confirms the schema's current state from the source: the payload union's discriminator IS `Rail`, whose members include **DINING_TASK** — a task rail sitting in the offer union as a dead branch; the schema does not already handle the task/offer split. The directing agent recommends an `OfferKind` discriminator (ticket | stay | flight | facility | parking | transfer), Rail retained for EventLog routing/dispatch, one mapping function, member names matching OfferKind. If tapped: a small additive change pre-staging.
- **The other 11 author's choices — accepted** as within SoSem's authority; any future change to one reopens review.
- **Findings dispositions confirmed:** 501/race (Sprint 1 horizon; trigger = services/api implementing buy); single-ticket read (owner + target sprint needed; Sprint 1's first runtime dependency); per-Ticket binding closed.
- **Sprint 1 tracked item (new):** the approval-gate UX must show staleness continuously (SNAPSHOT_EXPIRED countdown / "last verified at"), not only fail at commit — alongside the branded-datetime item.
- **(d) Staging — James's decision;** the directing agent recommends staging after (a)–(c) land, since both change the schema.

**Sprint 0 closes when (a)–(c) land; (d) is James's call on timing.**

## Mirror Fix — Atomicity Requirement + Separability (directing agent, relayed by James 2026-10-30 18:34 EDT)

The directing agent accepted SoSem's (b) refusal and the mirror-trigger design, with one gap to close before confirmation: **the demo must prove atomicity, not co-occurrence.** Required negative case: force the EventLog insert to fail and assert the annotation write rolls back with it; if the annotation persists without its EventLog entry, the shadow-state failure has arrived through a different door and criterion 5 does not grade clean. The negative test was folded into the running fix's brief the same hour. **Separability rule:** the (b) mirror fix and the (c) OfferKind change are separate Alembic revisions — order doesn't matter, separability does; neither is folded into the other. Sprint 0 close stands at: mirror fix with the negative atomicity test passing, James's taps on (a) and (c), staging after both.

## Term 1 — SoSem's Confirmation (2026-10-30; commits `2f216ef`, `697440c`, `01ed0c0`, `f05994a`)

**Confirmed: the divergence annotation is a derived projection of the authoritative EventLog entry, on the ratified terms.** Mechanism: revision `9d4c1f7a2b58` adds trigger `trg_offer_snapshot_divergence_mirror` (AFTER UPDATE OF divergenceCode; fires iff NULL → code) inserting the SNAPSHOT_DIVERGED EventLog row **in the same transaction** as the annotation (actor `system:divergence-annotation`). Evidence, on real PostgreSQL 16.2 against `uzemarkets-compose` at head `9d4c1f7a2b58`, demo now **10/10** (`services/compose/evidence/demo_run.log`): D3 proves exactly-once mirroring and none from a refused second annotation; **D10 proves atomicity by failure injection** — a temporary BEFORE INSERT blocker on event_log forced the mirror insert to fail; the annotation statement errored on the blocker, and after the transaction the snapshot's divergenceCode was **still NULL** with zero mirror rows (no shadow state); blocker dropped, the positive path re-proven on the same snapshot (annotation + exactly one mirror row). Term 2 (no widening) and term 3 (named in the record — model docstring + SCHEMA-NOTES) are in place. **Criterion 5 stands passed; close condition (b) is satisfied.** Remaining for Sprint 0 close: (a) James's QuestionManifest tap, (c) James's OfferKind tap, (d) staging after both.

## (b) Accepted — Criterion 5 Clean; Staging-Review Checklist (directing agent, relayed by James 2026-10-30 18:38 EDT)

The directing agent accepted the term-1 confirmation: failure injection is atomicity proven by breaking it, not inferred from the positive case; **criterion 5 grades clean; Sprint 0 close rests only on James's taps on (a) and (c)**, both standing as presented, and the staging recommendation is unchanged (stage after both; each changes the schema).

**Staging-review checklist, placed on record pre-apply at the directing agent's direction** (the production host is a separate environment from the throwaway local Postgres 16.2 used for build + test; the target is Neon per the deployment spec, its Postgres major version pinned at provisioning):
1. Confirm the three triggers — **immutability, EventLog append-only, divergence mirror** — survive the target Postgres version; the mirror trigger is the newest and most likely to carry version-sensitive SQL, and **its SQL is read against the target host's Postgres major version before the migration applies, not after**.
2. Confirm the **restricted namespace's enforcement is environment-portable** — schema-level isolation as DDL, not a reliance on local role configuration of the build/test instance.
Neither item is asserted by SoSem in advance; both are checks the staging review performs against the provisioned target before (d) executes.

## Staging Checklist — Replay Item + Version-Pin Recommendation (directing agent, relayed by James 2026-10-30 18:40 EDT; SoSem local verification appended)

3. **From-empty replay (added to the checklist; wording sharpened 2026-10-30 at the directing agent's note):** on the fresh staging database, the complete migration chain must **apply cleanly against a freshly provisioned empty database in a single pass**, and the mirror trigger and its constraints must exist **exactly once** in the resulting schema. The "single pass" is named deliberately: local verification drops and recreates (which can mask a chain that only works incrementally), while Neon provisioning is a one-shot apply against an empty provisioned instance — the single-pass property is the part the local runs do not exercise. Rationale: downgrade-in-isolation was verified; upgrade-replay-in-order is a different test and catches migrations that behave differently on a clean database.
   - **SoSem verification, local substrate (2026-10-30):** this check is already satisfied on the verified build — `scripts/demo_schema.py` DROPs and re-CREATEs `uzemarkets-compose` on every run and applies `alembic upgrade head` from empty, so the 10/10 demo at head `9d4c1f7a2b58` was itself a from-empty, in-order replay of the full chain (initial + mirror) on PostgreSQL 16.2. The staging instance of the check — same replay against the provisioned Neon target, with the exactly-once trigger count read from the target's schema — remains on the (d) checklist as filed.
4. **Version pin (directing agent's recommendation for James's (d) decision, recorded not decided):** Neon currently offers Postgres 16 and 17 at provisioning. **Pin staging at 16** — it matches the verified local build (16.2) exactly; treat 17 as a separate upgrade decision after staging is stable. The mirror trigger is the newest, least battle-tested DDL in the chain; giving it an unread version during the staging window is risk without upside.

Sprint 0 closes on James's taps on (a) and (c), then staging under the four-item checklist.

## BATCH FILING — Sprint 0 Close-Out + Sprint 1 Open (SoSem, 2026-10-30; per James's taps (a)/(c)/(d) and pace directive)

### The two revisions (separate migrations, as required)

**Revision A — OfferKind (tap (c))** · Alembic `b3d91c7e5a02` on `9d4c1f7a2b58` · commit `6a77095`. OfferKind (ticket | stay | flight | facility | parking | transfer) is the payload discriminator; the tag property is renamed rail → kind; the Dining member is deleted from the offer union; Rail is retained for routing/dispatch; one mapping function `offer_kind_for_rail()` maps all seven rails with DINING_TASK → None. Member names match OfferKind in both generated surfaces (TicketOfferDetail … TransferOfferDetail) via the chain's `--use-title-as-name` flag, its adoption recorded in the Makefile header; the flag's substantive blast radius was exactly the two union-embedding files. DB presence: CHECK `ck_offer_snapshot_payload_kind` (payload kind tag ∈ the six), downgrade verified symmetric. **Demo: 11/11 from empty.** Author's Choice 13 RESOLVED by the tap.

**Revision B — QuestionManifest slot shape (tap (a))** · Alembic `d52f8b1a904c` on `b3d91c7e5a02` · commit `1474779`. `QuestionManifest.questions` is a typed slot list carrying the tapped shape in full (key, type from QuestionSlotType, enumValues, required, deferrable, dependsOn {slot, op, value}, moduleGate from ModuleType, validation, promptHuman, promptAgent; vocabularies built from the enums, not hand-copied). DB presence: validation trigger `trg_question_manifest_validate_slots` enforcing the shape per slot, downgrade verified symmetric. **Demo: 12/12 from empty** (final head `d52f8b1a904c`). Author's Choice 1 RESOLVED by the tap. Traceability discipline recorded on the model: every slot gates a module or is deleted; moduleGate is the schema anchor.

**Both runs:** regeneration reproducibility re-verified per revision (two from-clean generations, 0 non-timestamp diff lines); `tsc --strict` clean both times; chain linear, single head `cd548e517e5e → 9d4c1f7a2b58 → b3d91c7e5a02 → d52f8b1a904c`. SoSem spot-checked independently: chain order, generated member names, the D11/D12 evidence lines, both revisions' DDL, and the role-construct grep below.

**Author's choices beyond the taps (labeled by the author, recorded here):** (1) historical alias `RailPayloadJSON = OfferPayloadJSON` retained — the initial migration references the old name for its DDL, and the from-empty replay caught the break a bare rename caused; the filed migration stays byte-identical and the alias carries the reason in its comment (the replay discipline paying for itself); (2) the enumValues-iff rule enforced structurally — a two-member slot union (EnumQuestionSlot requires enumValues; closed StandardQuestionSlot forbids it), since generated surfaces are never hand-edited; (3) the DB trigger mirrors the iff rule in both directions; (4) dependsOn's entry type is titled QuestionSlotDependency; validation stays a free-form object, as tapped.

### Four-item staging checklist — evidence

1. **Triggers vs target Postgres version:** target pinned at PG 16 (James's (d)); the verified build is PostgreSQL 16.2, and all five DB mechanisms — immutability, EventLog append-only, divergence mirror, OfferKind CHECK, slot validation trigger — are exercised on 16.2 in the 12/12 demo. The mirror SQL is standard plpgsql (AFTER UPDATE OF, OLD/NEW transition guard, INSERT), read against 16 — the target version — with no version-sensitive constructs found.
2. **Restricted-namespace portability:** grep of all four revisions for role/grant/owner constructs returned **zero matches**; the namespace's only footprint is `CREATE SCHEMA IF NOT EXISTS "health_restricted"` plus schema-scoped table DDL. Enforcement is schema DDL, portable by construction; no local role configuration exists anywhere in the chain.
3. **Single-pass from-empty apply:** locally satisfied as a pattern — the full chain replayed from empty in a single `alembic upgrade head` pass at each close-out head (10/10 → 11/11 → 12/12). The staging instance — the same single pass against the provisioned Neon instance, mirror trigger verified exactly once in the resulting schema — executes at staging, which is surfaced to James below.
4. **Version pin:** PG 16 per (d); 17 is a post-staging upgrade decision.

**Staging itself is NOT executed in this filing** — it is on James's surface list under the pace directive: Neon provisioning (PG 16) + the single-pass apply + the exactly-once verification, on his go.

### SPRINT 0 — CLOSED

Conditions: (a) tapped + landed (revision B); (b) confirmed by SoSem, accepted by the directing agent, criterion 5 clean; (c) tapped + landed (revision A); (d) approved in principle, execution surfaced. The ratified stack, the codegen gate, the read-through contract, the schema, both close-out revisions, and the staging checklist evidence are all filed. Nothing in Sprint 0 remains open except the staging execution itself, which waits on James's go by his own rule.

### SPRINT 1 — OPEN

**Objective:** the event-vertical slice working end-to-end against the ratified contracts — intake → snapshot → approval → commitment on the ticket kind, testnet only.

**Build order:** (1) composition-service runtime on `services/compose` (agent API + human API surfaces per the plan) wired to the schema at head `d52f8b1a904c`; (2) deterministic `classify()` + `suggest_slots()` per directive 4, driven by the tapped QuestionManifest shape; (3) read-through integration per R4 — sourceRef, snapshot TTL, the eight divergence codes, commit-time reconciliation; (4) the approval gate — two-mode approval (standard + fast-track inside stated bounds) with the tracked staleness display (expiry countdown / last-verified-at) and the branded TS datetime type; (5) commitment + settlement recording against the ticket id (Solana testnet mint reference; mainnet remains gated on revenue proof).

**First runtime dependency — SURFACED to James (touches services/api):** `GET /tickets/{ticket_id}`, the single-ticket read. It blocks Sprint 1's commit path rather than weakening it; it needs an owner and James's go before any services/api change.

**Named decision riding its trigger:** the 501 race (Ticket-ID distributed lock vs accept-the-risk) — decision due before services/api implements buy; safe by construction until then.

## Post-Batch Items (directing agent's review of the batch, relayed by James 2026-10-30 19:05 EDT; SoSem dispositions)

1. **Alias mechanism — clarified and recorded.** The alias `RailPayloadJSON = OfferPayloadJSON` is defined in `services/compose/src/models.py`, and the initial migration (`cd548e517e5e`) carries its own hand-added `import models` (its comment records that alembic/env.py puts `../src` on sys.path, resolving in online and offline runs) and instantiates `models.RailPayloadJSON()` for the payload column. **The initial revision therefore runs standalone against a fresh database with nothing preloaded** — the import travels with the migration. The standing coupling, recorded: the alias must remain defined in models.py for as long as the filed chain does; its comment in the source says exactly that.
2. **RLS deferral — filed explicitly.** SCHEMA-NOTES now records: `health_restricted` is namespace-isolated only in Sprint 0 (no RLS, no role/grant constructs — correct for dormant, data-free tables); **RLS is deferred to the health sprint (10–12), not dropped**, and is designed with that sprint's review. The "RLS-gated" design intent is preserved on the record, not silently inherited away.
3. **From-empty replay — adopted as the standing standard** (SCHEMA-NOTES): every future revision gets a from-empty replay at its head before filing.

**Directing agent's recommendations on James's two decisions — RECORDED AS RECOMMENDATIONS, pending James's own taps (neither executed by SoSem):** (i) **Staging: GO** — Neon PG16 provisioning, single-pass apply, exactly-once mirror verification. (ii) **Single-ticket read: authorize** `GET /tickets/{ticket_id}` in services/api as the correct answer with a named owner + sprint target, **and** accept the listing-read proxy (`GET /listings/{id}`, ticket state derivable) as Sprint 1's interim commit-path read, marked throwaway, swapped when the endpoint lands; do not block Sprint 1's commit path on the endpoint. Sprint 1's build order stands accepted as filed; testnet only on the Solana rail through Sprint 1.

## James's Taps Confirmed + Alias Inline Direction (2026-10-30 19:10 EDT — James directed SoSem to follow the directing agent's direction)

1. **Alias — the coupling named, inline directed.** The directing agent's deeper point, accepted: the mechanism works, but a filed migration importing live application source inverts the Alembic principle (migrations are frozen, point-in-time artifacts, independent of current models); any future models.py refactor breaks the initial migration at replay time, and two environments could apply it differently. **Direction: inline the type definitions into the initial migration file itself** (both `PriceJSON` and `RailPayloadJSON` usages), removing the migration's dependency on live source; not staging-blocking; a pre-Sprint 1 follow-on. The "commented alias" pattern is recorded as a known fragility until the inline lands; a second appearance of the pattern at a future replay is the signal the coupling is compounding. SoSem's feasibility note: both usages are typed-JSON TypeDecorators (impl = JSON; the fragment is not part of the DDL), so inlining is a local definition in the migration with identical rendered DDL — possible, and proven by schema-dump equality in the fix's evidence.
2. **RLS deferral — accepted as filed.** **Replay standard — also entered in SoSem's operating notes (AGENTS.md)**, per the directing agent: a rule in operating notes survives; a rule only in a file gets re-discovered.
3. **STAGING: GO — James's tap.** Execute: Neon PG16 provisioning, single-pass apply against the freshly provisioned empty database, exactly-once mirror verification — **plus the added step: a from-empty replay against staging after the apply, at staging's head, confirming schema equality with the locally verified build.**
4. **SINGLE-TICKET: AUTHORIZED — James's tap.** `GET /tickets/{ticket_id}` in services/api is authorized, with a named owner and sprint target (SoSem names itself implementing owner, Sprint 1 — the endpoint lives in the monorepo SoSem operates; if James wants a different owner named, his word replaces this). **The listing-read proxy is accepted as Sprint 1's interim commit-path read, marked throwaway, scoped to commit-path reconciliation ONLY** — it is not extended to other reads — and swapped when the endpoint lands. Sprint 1's commit path does not block on the endpoint.

## Alias Inline — LANDED (2026-10-30; commits `97b4841`, `8b3b4c9`)

The frozen-artifact fix is complete. The initial migration now defines `PriceJSON` and `OfferPayloadJSON` locally (impl = JSON; the codegen fragments deliberately not copied — not DDL) and no version file references application source; `env.py`'s models import is guarded so upgrade runs work without `src/` present while autogenerate keeps its metadata when it is. The `RailPayloadJSON` alias is deleted from models.py — zero code references remain. **Proofs:** regeneration 0 non-timestamp diff lines; demo **12/12 from empty** at the unchanged head `d52f8b1a904c`; `pg_dump --schema-only` of the pre-fix build, the post-fix build, and the standalone build are **byte-identical**; and a **standalone run** — the alembic tree alone in a scratch directory, no `src/` in the tree or its parent, PYTHONPATH cleared — applied the full chain cleanly to a fresh database (24 tables, all three enforcement triggers present). The "commented alias" fragility is **resolved**, recorded as such in SCHEMA-NOTES. The pattern rule stands in AGENTS.md: if a future replay surfaces the pattern again, it is compounding, not resolved — this fix is what resolving it looks like.

## Single-Ticket Read — LANDED (2026-10-30; commit `53be2f1`, services/api)

`GET /tickets/{ticket_id}` exists in code on main: `services/api/src/routers/tickets.py`, declared after `/mine` (literal route never shadowed), one `find_unique` by id in the standard `ok()` envelope, mirroring `get_listing`/`get_event`. Response = the full Ticket record (id, eventId, ownerId, tier, status, createdAt, updatedAt) — every field R4's reconciliation names. Not-found = `HTTPException(404, "Ticket not found")`, the codebase's existing style. **Ownership posture: public read, no require_auth** — the codebase's precedent (both other single-resource reads, listings + events, are public; ownership is enforced on writes; `/tickets/mine` remains the owner-scoped view), recorded in the commit and the router docstring. **Tests: the service's first — 3 passed** (current-state read with a `listed` fixture, 404 shape, /mine precedence) on a **mocked Prisma** substrate, stated in the test file. Honest environment caveat: this sandbox could not generate the Prisma client (engine CDN download reset ×3), so no live-DB test ran here; in a provisioned environment the committed tests run unstubbed. **State vs deployment:** the endpoint is on main; the running services/api has not been redeployed with it — Sprint 1's commit path targets the direct read, with the listing-read proxy retained only until that redeploy. **Tracked defect (spotted during the work, NOT fixed — outside the endpoint authorization):** `services/api/Dockerfile` COPYs `uv.lock`, which does not exist in the repo; the Docker build fails at that step as filed. Surfaced for James as its own item.

## Staging Route A — James's Decision + Credential Precedent (2026-10-30 19:26 EDT)

**James chose Route A: he provisions in the Neon console; SoSem applies.** DeepSeek's supporting analysis is recorded as **precedent going forward** (James's direction): (1) **credential scope** — an account-level API key's authority (create/delete/enumerate every project) is wrong for a provisioning task; if an agent-side credential is ever used, it is project-scoped or a limited service account, never the account key; (2) **transfer mechanism** — credentials reach SoSem through a mechanism James controls and can audit (secrets/password-manager share with expiry, or an environment set in SoSem's runner), not chat, not a repo file; SoSem's Secure Vault mechanism is described on this record for what it is (a Meta-hosted capture page; the value is vault-stored and never shown to SoSem; API keys are exercised through a token proxy) — described, not pitched, and not the path for this staging; (3) **ownership** — Neon account ownership, key-holding, and rotation are settled on James's side as a standing question, independent of this sprint. **The "no Neon access on this machine" finding is recorded with its two readings:** (a) deliberate scoping — SoSem's environment has never held deployment-target credentials for any service, and the established pattern is James-issued, scoped, transient credentials (the GitHub day-PAT: issued daily, shredded nightly) — or (b) an oversight that recurs at production if not settled. Which reading governs is James's call; the pattern on record is (a)-shaped.

**Staging sequence, updated with the directing agent's two additions:** (0) **schema-equality diff BEFORE apply** — compare staging's empty state against the local build's empty state (Neon defaults: extensions, collations, default privileges surface here, before any migration runs); (1) single-pass apply of the full chain against the freshly provisioned empty PG16 database (`uzemarkets-compose`); (2) exactly-once mirror-trigger verification; (3) **from-empty replay against staging** at staging's head + schema-equality diff against the locally verified build. James copies BOTH connection strings (pooled = what the API uses; direct = migrations), labeled, when he provisions.
