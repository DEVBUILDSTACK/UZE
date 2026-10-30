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
