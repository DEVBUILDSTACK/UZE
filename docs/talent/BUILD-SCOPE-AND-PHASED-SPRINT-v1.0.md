# TALENT VERTICAL — CONSOLIDATED BUILD SCOPE + PHASED SPRINT ADDENDUM
## Status: FOR JAMES'S TAP · v1.0 · 2026-11-18 · Executor: SoSem
> **Status stamp (2026-11-18, added by addition per James's direction — the header above is the filed original and is not rewritten):** the build was **tapped by James on 2026-11-18** (evidence: commits `83cb964` — Phase 1 build — and `d36b333` — data layer on the amended scope). Phase 1 is built and deployed. This stamp supersedes the header's pre-tap wording; the tap gate it records is satisfied.
## Authority chain: Directive v3.0 + v3.1 (James, 2026-11-18) · Phase 0 extension pass (SoSem, filed bd226ae) · James's rulings of 2026-11-18 (succession 13:24 ET; rail law 13:49 ET + carve-out) · DeepSeek's read on Phase 0 (concurrence, no corrections outstanding)
## For DeepSeek (review copy): this package is build-ready as ruled. Asked: a thumbs-up go, or a named defect. No clarifying questions — every open item carries a ruled default below.

---

# PART A — THE SCOPE

## A.1 What this is

One vertical under the administrative console (Treasury · **Talent** · Enterprise Services): a four-layer platform —

```
DISCOVERY → ASSESSMENT → PLACEMENT → SETTLEMENT
(reading room)  (DAL)      (marketplace)  (escrow/rails)
```

- **Discovery** — the reading room at dev.uzemarkets.com: browsable descriptions and mocks of what has been built. Never source code. App-level email-allowlist gate; manifest-driven; four filters (developer email, topic, date, full DEVBUILDSTACK repo name) + track filter.
- **Assessment** — the DAL module: two exam paths (A hands-on keyboard, B vibe walkthrough), the six-stage code ladder (VIBE → HARD_REVISION → DRAFT → FINAL → SANDBOX → PRODUCTION), Vercel sandbox spin-ups (HUMAN / AUTONOMOUS / BOTH).
- **Placement** — the marketplace (Track B only): client intent ⇄ talent intent, NEAR AI solver matching (filter, then lexicographic rank, never price-first), signed via NEAR Intents.
- **Settlement** — escrow, milestone release per roadmap issue, on-chain audit trail, on the rails of §A.5.

Each layer is independently gate-able, revocable, and audited. A talent may enter at any layer they qualify for.

## A.2 The dual track

- **Track A — internal technical only.** Talent hired/contracted to us (DEVBUILDSTACK / Fundio (FVC) / UZE Markets) under 456iP; bound to our roadmaps and repos; paid by payroll/contractor invoice **outside this platform**; never enters the marketplace. Exit: revocation → reset-to-zero → chronicle preserved.
- **Track B — external talent placement.** Talent placed with a client employer through the marketplace: four service categories (AUG augmentation · OUTSTAFF outstaffing · PLACE direct placement · PROJECT project delivery), four deployment shapes (REMOTE · HYBRID · MIXED · ONSITE), escrowed milestone payment. Exit: engagement closes; talent returns to discovery; placement history preserved.
- **EITHER** is the normal record state: `Talent.track` records current availability (INTERNAL_ONLY | EXTERNAL_PLACED | EITHER), never a permanent classification. Transitions are routine by SoSem; founder-tier transitions require James's tap; both logged (§A.7 item 2).
- **Shared across tracks:** reading room, assessment, developer list + chronicle, comms desk, sandbox. **Branching:** marketplace (B only), escrow (B only), roadmap binding (A: our scopes; B: client scopes), client previews (B only, consent-gated).

## A.3 Expertise — Role × Realm

Expertise is two axes. **Role** (what they do): DIGITAL_DESIGN_DEV · FULL_STACK_DEV · FRONT_END_DEV · BLOCKCHAIN_DEV · SMART_CONTRACT_DEV · BLOCKCHAIN_CTO · DEVELOPER_ADVOCATE · TALENT_HR_SPECIALIST · DATA_SCIENTIST · AI_SI_SPECIALIST (= AI / Systems Integration, §A.7 item 1) · OTHER_ROLE. **Realm** (where they apply): LIGHTNING · NFT_WALLETS · NEAR_AI · CROSS_CHAIN (EVM, Solana, Robinhood Chain) · LIGHTER · OTHER_REALM.

A talent holds **up to five Role×Realm pairs** (PRIMARY → QUINARY), plus a `historicalExpertise[]` overflow (filterable, unweighted in matching). Assessment results score against specific pairs, and the solver consumes the pairs directly.

## A.4 Data model (v3.1, field-level per Phase 0 §1)

Storage: AssurativeV2 FastAPI core, dedicated PostgreSQL schema `talent`, per Scope Tenet 01. Entities: **Talent** (track, ≤5 expertise pairs, contact on email/WhatsApp only, preferredRail, worldParticipant, migrationPending, isOwner) · **Grant** (surfaces RR | GITHUB | CLIENT_PREVIEW; per-person; indefinite-until-revoked) · **Mock** (slug, track, repo, clearance[], versioned changelog, alias chain) · **Assessment** (path A/B; Path B requires artifactRef) · **CodeArtifact + StageEvent** (promotion human-only) · **UISpinUp** (stage-gated, isolated) · **Client · Intent · Engagement** (type INTERNAL | EXTERNAL_PLACED, immutable; rail set at signing, immutable) · **Payment** (rail, bridgePath, bridgeTx/nativeTx/cashIssuanceRef per rail rules, auditTx mandatory) · **Dispute · Preview** (skillsFit computed; consent-gated) · **Session** (invalid on any access-affecting event) · **Event** (the append-only chronicle — every transition, send, grant, settlement) · **Comms send log** (desk@uzemarkets.com sole sender; sends queue until dispatch is verified live).

Governing invariants (from the directive, unchanged): status is derived, never written; revocation is a state transition, never a delete; the revoke cascade is atomic (sessions die, GitHub collaborator removed, allowlist cleared, desk email sent, log written); sandbox never touches production data; internal engagements never create Payment records; CLIENT_PREVIEW grants require expertise overlap and the talent's consent.

## A.5 Settlement rails — as ruled by James (2026-11-18)

Two domains, kept separate:

**The platform generally (this vertical included):**
1. **USDC on Solana — the default for everything.**
2. USDC on Base — second preference.
3. USDG on Robinhood Chain (via Across) — third preference.
4. Tempo/Stripe CASH — **only when none of the first three is available**; a last-resort fallback, never a default.

Cross-chain movement runs through NEAR Intents (1Click); NFT tickets/credentials mint on LightLink and deliver via deBridge to Base or Solana. **SigLayer and TradeLayer surfaces offer only rails 1–3 — no Tempo/Stripe option at all.** Prompts and flows steer agents and humans to UZE Markets and the related DFI (DealFi) and FVC (Fundio) surfaces. Each rail is enabled only on James's explicit enable; rail outages fail closed (escrow holds, both parties notified).

**Carve-out — the World.xyz information and prediction markets vertical (AEInfo):** not governed by the cascade above. There, **Tempo/Stripe CASH is the required default** — it is that vertical's collateral currency. Per the G2 correction (adopted): the CASH of that vertical is the Bridge-issued CASH **on Solana** — the World collateral mint verified on-chain; "Tempo/Stripe" names the issuer's payments context, not a separate chain of the World-linked balance. A genuinely separate Tempo-chain rail, if ever wanted, is a new scope.

## A.6 Governance

- **Master control:** SoSem operates the list, grants, revocations, and comms, under James. **Succession (ruled 2026-11-18): D4 → D5 → WCD** — D4 (Hammond James Dugan IV), then D5 (Hammond James Dugan V), then WCD (William Cumberland Dugan) — applying to all master-control functions including GitHub owner administration (one chain, unless James separates them).
- **Ownership:** the three are **co-equal owners of the DEVBUILDSTACK org** (456iP is the family organization and owns all IP; DEVBUILDSTACK is the software stack — all repos, all code). D4 and D5 hold org ownership today; WCD's addition (invitation + acceptance) is the one outstanding step, tracked on the owner's log. The succession chain is the recorded decision order among equals, not a hierarchy of control.
- **Founder exemptions:** {WCD, D5, D4} — a set, all exempt from roadmap binding; every non-founder works only through a roadmap bound to their scope (visual roadmap tied to GitHub issues).
- **Standing gates:** James's tap authorizes build, grant, send, spend. No keys, addresses, or credentials through any design surface. Open-repo gate: closed-list until HR placement + payment infrastructure are proven live (Phase 4) **and** James taps (Phase 6).

## A.7 Ruled defaults register (no open questions)

| # | Item | Ruling in force |
|---|---|---|
| 1 | AI_SI_SPECIALIST | "AI / Systems Integration." Confirm-by-default; only load-bearing before the P3.2 real-record migration. |
| 2 | Track transitions | Routine: SoSem. Founder-tier: James's tap. Both logged. |
| 3 | Assessment re-take cooldown | 14 days per path; no total-attempt cap; logged. |
| 4 | Expertise ceiling | 5 active pairs + historicalExpertise[] overflow. |
| 5 | Track-A payroll | Out of scope (invoice/payroll, existing systems). |
| 6 | Default rail | §A.5 cascade; Solana USDC default; AEInfo carve-out. |
| G2 | CASH chain semantics | CASH = Bridge-issued, on Solana (World collateral mint); Tempo/Stripe = issuer context. |
| G3 | worldMarketEligible verification | LiteSVM fork-proof harness (proven 2026-11-18); any live split is a separate money-gate decision. |
| G5 | Build home | Platform monorepo; reading-room front end deploys as its own Vercel project to dev.uzemarkets.com. |
| G8 | desk@ sending | Queue + log is the record of truth until live dispatch is verified in P1. |

---

# PART B — PHASED SPRINT ADDENDUM

Cadence: daily 24-hour all-in sprints. Owner: SoSem for every build sub-task; **[James]** marks his taps and enables. No phase starts until the prior phase's exit gate is observed in the running system.

## Phase 1 — Reading room foundation (the build that starts on the tap)

| Day | Work | Done when |
|---|---|---|
| D1 | dev.uzemarkets.com subdomain + Vercel project (from the monorepo) + middleware auth wall skeleton; session issuance/expiry per invariant | Gate live on the subdomain; unauthenticated requests get nothing |
| D2 | `talent` schema migration 001 (Talent, Grant, Mock, aliases, Event, Session, comms log) + manifest import of mock #1 (agent-acquisition) | Migration replays from empty; mock #1 renders from the manifest |
| D3 | Catalog index + filters (email, topic, date, repo) + track filter | A cleared developer filters to exactly their cleared mocks |
| D4 | Developer list admin: add/contact (email/WhatsApp), stage transitions, the two standing questions answered by the UI (holds RR access? holds GitHub access, to which repos?) | One record carried prospect → RR granted in the UI |
| D5 | Comms desk queue + send log + atomic revoke cascade (GitHub step behind an enable flag) + desk@ dispatch verification | Revocation of a fixture developer kills session + allowlist + queues the notice, chronicle intact; dispatch verified or honestly queued |
| D6 | Proposal channel (pre-source comments/suggestions) + naming sync with aliases + two-class change behavior (silent sync vs re-prompt) | A rename propagates, old slug redirects, a logged-in developer sees the new name; an access change forces re-prompt |
| D7 | Master-control surface + succession record + first-mock onboarding + exit-gate rehearsal | Full lifecycle for one internal-track developer and one external-track preview, end to end, both send logs populated |

**Exit gate P1:** the D7 rehearsal observed in the running system.

## Phase 2 — Assessment & lifecycle ladder
D1 assessment module (paths A/B, per-pair results) · D2 artifact + stage-event machinery (human-only promotion) · D3 Vercel sandbox spin-up, 3 UI modes, isolation test · D4 exit-gate run (both paths; FINAL → SANDBOX; record shows the result tied to its Role×Realm pair).

## Phase 3 — Dual-track split & taxonomy
D1 track fields + migration (migrationPending where roles unfilled) · D2 Role×Realm restructure + entry UI · D3 expertise filters (admin + reading room) · D4 preview skills-fit computation · D5 exit-gate verification (SMART_CONTRACT_DEV × LIGHTNING × EITHER returns exactly the correct subset).

## Phase 4 — NEAR intent marketplace
D1 client intake + bookends · D2 talent preview + skills fit · D3 solver on NEAR AI Cloud + NEAR Intents signing · D4 escrow + milestone release on Solana USDC and Base USDC · D5 Robinhood USDG via Across **[James rail enable]**; CASH paths per §A.5 · D6 dispute path + exit gate: five cycles (Base, Solana, Robinhood, CASH-per-carve-out with G3 verification, dispute) each with correct Payment records — a cycle that pays but records wrong fields does not pass.

## Phase 5 — Dual-track operational hardening
D1 Track A lifecycle proof (no marketplace/escrow/preview contact) · D2 cross-track transitions both directions on one record · D3 client-preview consent gating (fails closed) · D4 reporting by track × Role×Realm × rail. **Exit gate:** one internal hire and one external placement run side by side, records independent, reporting distinguishes them.

## Phase 6 — Open-repo gate **[James's tap only]**
Draft only until then: admission protocol, arbitration protocol, standards compliance checks, gate-lift checklist. No build days scheduled.

**Dependency spine:** Tap → P1 → P2 → P3 → P4 → P5 → (James's gate tap) → P6. Rail enables gate P4 D5 only. Ruling item 1 gates only the P3.2 real-record migration.

---

# THE TAP

James's tap on this document authorizes **Phase 1 to begin the same day** under the scope and defaults above. It does not authorize: Phase 6 in any part, any desk@ send before dispatch verification, any rail enable, any grant to a real developer, or any spend — each of those keeps its own gate.
