AEINFO TALENT VERTICAL — CONSOLIDATED ENGINEERING DOCUMENT

Original brief through final directive v3.1

Prepared: 2026-11-18 · For: SoSem (build lead) · Authority: James · Status: Ready for upload and attachment to the engineering prompt

---

How to read this document

This is a single consolidated record of the Talent Vertical from its origin (the reading room request) through the final directive (v3.1). It carries:

· Part I — the origin: what James originally asked for, and what SoSem proposed.
· Part II — the first response: the six-answer foundation and the six sprints.
· Part III — the first scale change: the Talent Vertical Directive (marketplace, settlement, dual-track).
· Part IV — the second addition: the Developer Assessment & Lifecycle (DAL) module.
· Part V — the consolidated v3.0 directive: dual-track plus the Role × Realm taxonomy.
· Part VI — the v3.1 correction: all five settlement rails, NEAR AI Cloud, NEAR Intents, LightLink, Tempo/Stripe CASH.
· Part VII — the final 14 exhibits (Mermaid, human and machine, external and internal).
· Part VIII — the final phased sprint (P0–P6).
· Part IX — open items for James's ruling.
· Part X — change log: every version, what changed, and why.

Where earlier content is superseded by later content, the later version governs. Where earlier content survives unchanged, it is carried forward. The operating specification is Parts V–VIII; Parts I–IV and IX–X exist so the evolution and the reasoning are visible in one place.

---

PART I — ORIGIN: THE READING ROOM REQUEST

I.1 — James's request (setup overview, 2026-11-18)

A permissioned developer mock library — James calls it the reading room — on its own gated subdomain, holding clear, browsable explanations of what has been built across the DEVBUILDSTACK codebase, for the Fundio / UZE Markets developer team and for specialist recruits (Lightning; NFT and wallets; NEAR AI; cross-chain EVM / Solana / Robinhood Chain; Lighter). Behind it sits a developer list run as a lifecycle instrument: expertise records, contact and stage tracking, grants and revocations across the reading room and GitHub, roadmap binding, and a comms desk.

Stated reason: as Founder and project lead, James wants a rear-view mirror into historical mocks tied to prospective developer team members' recruitment, contractual engagement, hackathon/grant-funding scopes, and defined development scopes.

Clarification of record: the public /devpartner route is not this — that is the ADV Americas partner program, public and ungated. The reading room is a separate, permissioned subdomain for the developer team and recruits.

I.2 — SoSem's advised build path (as proposed)

1. Two permission layers, never conflated — GitHub (source) and email-allowlist gate (library), issued together, revocable independently.
2. No client-side gating — server checks identity before serving; 404 for unauthorized is the permission working.
3. App-level gate on Vercel — Vercel Deployment Protection (wrong tool) and Cloudflare Access (heavier than needed) rejected.
4. Dedicated subdomain — dev.uzemarkets.com, created fresh, gated from day one.
5. Manifest-driven library — one row per mock; four filters (developer email, topic, date, repo name).

I.3 — Addenda (James's directions)

Addendum 1 — Comms desk and sync:

· Pre-source collaboration: cleared developers can comment on mocks they can see before GitHub access.
· Manifest is single source of naming; renames adjust everywhere; aliases preserve old links.
· Two classes of change: content/naming sync silently; access-affecting changes end session and re-prompt.
· desk@uzemarkets.com as sole sender; all sends logged against developer record.

Addendum 2 — Developer list lifecycle:

· Five-realm expertise per developer.
· Email + WhatsApp only for recruitment contact.
· Lifecycle stages: prospect → contacted → recruiting → RR granted → source granted → revoked/reset.
· Roadmap binding for every non-founder; the three Dugan owners exempt.
· Reset-to-zero on revocation; chronicle preserved.
· No uncontrolled action (roadmap-bound work only).
· Master control: SoSem, succession to D5, then D4.

---

PART II — FIRST RESPONSE: THE SIX-ANSWER FOUNDATION

II.1 — The six answers (corroborated with additions)

Question Corroboration Additions named
Q1 permission model Two-layer model correct Revoke propagation automated; dormant-grant reaper; manifest write-time validation
Q2 gate placement App-level on Vercel correct Middleware-level gate; OTP uniform response; rate limits; session TTL; noindex; HSTS
Q3 manifest + filters Design serves rear-view purpose Status filter; version+changelog fields; clearance-scoped developer filter
Q4 missed risks Trust boundary correct Eight named risks within the stated boundary
Q5 comms desk Design coherent Comments route by subject; alias version-chain; email deliverability critical path; OTP link hygiene
Q6 developer list Lifecycle sound Stage-as-summary vs access-booleans; soft-delete; D4 second successor; item 15 depends on branch protection

II.2 — Foundation sprints (LR.0 – LR.5)

Sprint Objective Exit gate
LR.0 Domain, gate foundation, auth hygiene SoSem signs in via OTP; unauthorized email refused; SPF/DKIM/DMARC pass
LR.1 Manifest, index, filters First mock onboarded; filters work; alias chain tested
LR.2 Developer list, lifecycle, roadmap binding Test developer record runs full lifecycle
LR.3 Comms desk, send log, revoke cascade Revoke kills session + GitHub access within one request
LR.4 Proposal channel, naming sync, two-class change Comment accepted → version bumps silently; supersede → session ends + email
LR.5 Master control, succession, first mock onboarding SoSem executes full lifecycle; branch protection verified

---

PART III — FIRST SCALE CHANGE: THE TALENT VERTICAL DIRECTIVE

III.1 — Scale change, stated plainly

Talent is no longer a recruitment tool. It is one of three verticals: Treasury · Talent · Enterprise Services.

The reading room is the discovery layer. The marketplace is the placement layer. The payment infrastructure is the settlement layer. Three layers, one continuous surface.

Open-repo gate: the marketplace stays closed-list until HR placement and payment infrastructure are integrated and proven. That gate is a James ruling, not a proposal.

III.2 — The bookend preview

Before any commitment, a target developer sees four things on one surface:

1. The mock — descriptions, never source.
2. The engagement bookends — service, deployment, timeline, payment.
3. Their skills fit — match, gap, growth. Honest about gaps.
4. The clearance — what they would need to sign, what would be granted, what would not.

III.3 — Marketplace on NEAR intents

· Client intent — skills, deployment, timeline, budget, service category.
· Talent intent — skills, deployment preference, availability, rate.
· Matching — NEAR AI solver generates feasible pairings; lexicographic ranking; filters before ranking.
· Commitment — both sides sign a NEAR intent.
· Settlement — escrow releases against milestone.

III.4 — Payment infrastructure (initial — later expanded to five rails)

· CASH (Bridge/Stripe) and USDC supported from day one.
· Milestone release aligned to roadmap binding.
· Client escrow held at engagement signing.
· On-chain audit trail per settlement.
· Dispute window stated, not silent.

III.5 — Marketplace sprints (TR.1 – TR.5)

Sprint Objective
TR.1 Client intake and bookend authoring
TR.2 Talent preview and skills fit
TR.3 NEAR intent marketplace and solver
TR.4 Payment escrow and milestone release
TR.5 Open-repo hardening (James's tap required)

---

PART IV — SECOND ADDITION: THE DEVELOPER ASSESSMENT & LIFECYCLE (DAL) MODULE

IV.1 — Placement, not recreation

The three-layer navigation (Treasury · Talent · Enterprise Services) exists in the administrative console. The DAL module attaches under the Talent layer as a new module, not a new vertical.

```
Administrative Console
├── Treasury
├── Talent
│   ├── Reading Room (LR)
│   ├── Developer List (LR.2)
│   ├── Marketplace (TR)
│   └── Developer Assessment & Lifecycle (DAL)   ← new
└── Enterprise Services
```

IV.2 — Three surfaces

A. Assessment — mini exam / mini onboarding with two paths.

Path A — Hands-on keyboard: stated problem, stated time limit, editor + terminal in browser; keystroke-to-commit timeline; graded on correctness, process, craftsmanship.

Path B — Vibe walkthrough: developer brings code they built; live walkthrough; graded on understanding, ownership, judgment.

The reverse path: vibe code can move through the ladder — walked through (proving understanding of code not written line by line), then promoted through hard revision → draft → final → sandbox → production.

B. Six-stage lifecycle ladder:
VIBE → HARD_REVISION → DRAFT → FINAL → SANDBOX → PRODUCTION

Stage Meaning Gate
VIBE Code by prompting/ideation/assembly Walkthrough + ownership declaration
HARD_REVISION Line-by-line rewrite; every line is theirs Reviewer confirms
DRAFT Structurally complete; tests + docs Draft review
FINAL Reviewed, tested, signed off Reviewer sign-off
SANDBOX Deployed to developer's Vercel sandbox Sandbox exercise passes
PRODUCTION Shipped, or own artifact Final sign-off

C. Vercel sandbox spin-up — developer's own UI, isolated, at FINAL or later. Three modes: HUMAN, AUTONOMOUS, BOTH. Ephemeral (90-day prune unless retained).

IV.3 — DAL sprints (DA.1 – DA.3)

Sprint Objective
DA.1 Assessment module — both paths end-to-end
DA.2 Six-stage lifecycle ladder with human-gated promotions
DA.3 Vercel sandbox spin-up with three UI modes

---

PART V — CONSOLIDATED v3.0: DUAL-TRACK + ROLE × REALM

V.1 — The dual-track model

The prior documents conflated two flows. They are now separated.

Track A — Internal technical only

Talent is hired or contracted to us (Fundio / UZE Markets / DEVBUILDSTACK). Work on our code, under our roadmap, on our repos. Never placed with a client. The marketplace is not entered.

· Buyer: us.
· Contract: employment or contractor agreement under 456iP.
· Roadmap: bound to a DEVBUILDSTACK scope.
· Payment: payroll or contractor invoice; not escrow-mediated.
· Exit: revocation → reset-to-zero → chronicle preserved.

Track B — External talent placement

Talent is sourced, assessed, and placed with a client employer. Four service categories: augmentation, outstaffing, direct placement, project delivery. Four deployment shapes: remote, hybrid, mixed, on-site.

· Buyer: client employer, with us as intermediary.
· Contract: engagement agreement mediated by the marketplace.
· Roadmap: bound to client's scope.
· Payment: escrowed, milestone-released, audit-trailed.
· Exit: engagement closes; talent returns to discovery; placement history preserved.

The EITHER case

Most talent records carry EITHER — available for both. A Track-A hire who later becomes Track-B is a normal transition. The track field records current availability, not permanent classification.

What is shared across both tracks

Reading room · Assessment module · Developer list · Comms desk · Vercel sandbox · Open-repo gate.

What branches

Marketplace (Track B only) · Payment infrastructure (Track B escrow; Track A invoice/payroll) · Roadmap binding · Client previews · Deployment shape.

V.2 — The expertise taxonomy: Role × Realm

Prior documents had a single realm enum. That was insufficient. Expertise is two axes, crossed.

Axis 1 — Role (what they do)

Code Human label
DIGITAL_DESIGN_DEV Digital design dev
FULL_STACK_DEV Full-stack dev
FRONT_END_DEV Front-end dev
BLOCKCHAIN_DEV Blockchain dev (generalist)
SMART_CONTRACT_DEV Blockchain smart-contract dev
BLOCKCHAIN_CTO Blockchain CTO
DEVELOPER_ADVOCATE Blockchain developer team advocate
TALENT_HR_SPECIALIST Blockchain talent placement & HR specialist
DATA_SCIENTIST Data scientist
AI_SI_SPECIALIST AI / SI field expert (expansion pending James's ruling)
OTHER_ROLE Extension point

Axis 2 — Realm (where they apply)

LIGHTNING · NFT_WALLETS · NEAR_AI · CROSS_CHAIN (EVM/Solana/Robinhood) · LIGHTER · OTHER_REALM

Talent record

Up to five Role × Realm pairs, proficiency from PRIMARY → QUINARY. A "smart-contract dev in Lightning" is one pair. A "full-stack dev in NFT/wallets" is another. Migration from prior single-realm records handled via migrationPending: true flag.

Example queries this supports

· Lightning smart-contract dev, primary, remote or hybrid, ≤$X/day
· Cross-chain full-stack, secondary or better, either track
· Blockchain CTO, primary, direct placement only
· Data scientist, NEAR AI primary, project delivery
· Talent HR specialist, blockchain recruit — for internal team

V.3 — Schema v3.0 entity deltas

New entities: RoleRealmPair, plus track field added to Talent, Mock, Engagement. Full entity model retained from prior versions (Talent, Grant, Mock, Assessment, CodeArtifact, StageEvent, UISpinUp, Client, Engagement, Intent, Preview, Payment, Dispute, Session, Event).

---

PART VI — v3.1 CORRECTION: ALL FIVE SETTLEMENT RAILS

VI.1 — What was missing and is now explicit

The v3.0 directive named NEAR AI and NEAR Intents as labels, but the technical integration was not explicit. The solver architecture, the 1Click settlement path, the LightLink bridge, and the USDC→USDG rail were not detailed. That is not sufficient for a directive that turns on these rails.

Added in v3.1:

1. NEAR AI Cloud — the confidential-inference substrate (TEE-backed) for the solver network. Solver weights, talent intents, and client intents never leave the TEE in the clear.
2. NEAR Intents (1Click API) — the solver-network settlement layer. Payer chain and merchant chain are independent; competing solvers fill in between. The marketplace's escrow-execution path.
3. LightLink L2 — the bridge to Base and Solana via deBridge, for NFT ticket / RWA delivery. Gasless mint, 0.5s block.
4. Tempo / Stripe CASH — the fifth settlement rail. CASH is the Bridge-issued (Stripe company) stablecoin; it is the collateral currency for World.xyz prediction markets.

VI.2 — The settlement matrix (load-bearing)

Rail Chain Currency Bridge path Primary use
BASE_USDC Base L2 (EVM) USDC Native Default general settlement
SOLANA_USDC Solana L1 USDC Native High-throughput settlement
ROBINHOOD_USDG Robinhood Chain (EVM) USDG (Paxos) Across (USDC → USDG) Robinhood-ecosystem clients
TEMPO_CASH Tempo (Stripe) CASH (Bridge) Bridge issuance/redemption AEInfo-linked engagements; prediction-market participant talent
INTERNAL_INVOICE — fiat — Track A only; no on-chain settlement

Bridge paths:

· USDC → USDG: Across (cross-chain, non-custodial)
· NFT ticket / credential: LightLink L2 mint → deBridge to Base or Solana
· CASH issuance/redemption: Bridge (Stripe) native rail
· Cross-rail movement (e.g., CASH → USDC on Solana): NEAR Intents 1Click — the solver network quotes and fills the swap

VI.3 — The World.xyz connection (the structural integration)

TEMPO_CASH settlement writes to the same Bridge-issued CASH balance World.xyz uses as collateral. A talent paid on TEMPO_CASH:

1. Holds the exact token they can split into YES/NO on any World market.
2. Redeems from a settled position 1:1 for CASH.
3. No conversion, no off-ramp step, no delay.

That is the structural integration between the prediction market vertical and the talent vertical. A talent can go from "paid for work" to "positioned on a prediction market" without a single conversion step. This is the reason the two verticals are one platform, not two.

VI.4 — Schema v3.1 additions

```json
{
  "schemaVersion": "3.1",
  "newEnums": {
    "SettlementRail": ["BASE_USDC", "SOLANA_USDC", "ROBINHOOD_USDG", "TEMPO_CASH", "INTERNAL_INVOICE"],
    "BridgePath": ["NATIVE", "ACROSS", "LIGHTLINK_DEBRIDGE", "BRIDGE_STRIPE", "NEAR_INTENTS_1CLICK"]
  },
  "newFields": {
    "Engagement": {
      "settlementRail": "SettlementRail — set at creation, immutable",
      "settlementBridge": "BridgePath",
      "nftOutput": "boolean",
      "nftChain": "BASE | SOLANA | LIGHTLINK_NATIVE | null"
    },
    "Payment": {
      "rail": "SettlementRail",
      "bridgePath": "BridgePath",
      "bridgeTx": "string? — required for ACROSS",
      "nativeTx": "string? — required for NATIVE",
      "cashIssuanceRef": "string? — required for BRIDGE_STRIPE / TEMPO_CASH",
      "worldMarketEligible": "boolean — true iff rail=TEMPO_CASH ∧ talent.worldParticipant"
    },
    "Talent": {
      "preferredRail": "SettlementRail?",
      "worldParticipant": "boolean"
    }
  },
  "newInvariants": [
    "Engagement.settlementRail is immutable after signing; change requires a new engagement",
    "Payment.bridgeTx mandatory when bridgePath = ACROSS",
    "Payment.cashIssuanceRef mandatory when rail = TEMPO_CASH",
    "Payment.worldMarketEligible = true only when rail = TEMPO_CASH and talent.worldParticipant = true",
    "AEInfo-linked scope defaults to TEMPO_CASH unless overridden",
    "Internal engagements never create Payment records — invoice/payroll only"
  ]
}
```

---

PART VII — FINAL EXHIBITS (14 MERMAID DIAGRAMS)

All exhibits are filed under docs/talent/exhibits/. Classification: 🟢 = EXTERNAL_VISIBLE · 🔴 = INTERNAL_ONLY. Family: HUM = human consumption · MACH = machine consumption.

VII.1 — Exhibit index

ID Title Class Family Audience
HUM-EXT-01 The Talent Journey 🟢 HUM Talent, advisors
HUM-EXT-02 Role × Realm Expertise 🟢 HUM Talent
HUM-EXT-03 Assessment & Ladder 🟢 HUM Talent
HUM-EXT-04 Engagement & Payment (5 rails) 🟢 HUM Talent, clients
HUM-INT-01 Platform Architecture 🔴 HUM SoSem, James
HUM-INT-02 Master Control & Governance 🔴 HUM SoSem, James, D5, D4
HUM-INT-03 Phase Execution Map 🔴 HUM SoSem
MACH-INT-01 Entity Relationship v3.1 🔴 MACH SoSem
MACH-INT-02 Talent State Machine 🔴 MACH SoSem
MACH-INT-03 Assessment & Code Artifact States 🔴 MACH SoSem
MACH-INT-04 Engagement State Machines (both tracks) 🔴 MACH SoSem
MACH-INT-05 Invariants & Revoke Cascade 🔴 MACH SoSem
MACH-INT-06 Solver Pipeline (NEAR AI Cloud + Intents) 🔴 MACH SoSem
MACH-INT-07 Settlement Rails — five paths to World.xyz 🔴 MACH SoSem

VII.2 — The full Mermaid source

The complete Mermaid source for all 14 exhibits is filed in the repo at docs/talent/exhibits/*.mmd. Each file carries a version header matching schema v3.1 and an extension-point block so future iterations are additive.

Key diagram signatures (render destination — full source in repo):

· HUM-EXT-01 (Talent Journey) — the end-to-end talent experience from reading-room arrival to settlement, with preferred settlement rail and World.xyz participation surfaced as talent choices.
· HUM-EXT-02 (Role × Realm) — the ten roles crossed with five realms, five proficiency levels, three example profiles.
· HUM-EXT-03 (Assessment & Ladder) — two assessment paths feeding the six-stage ladder ending in Vercel sandbox spin-up (HUMAN, AUTONOMOUS, BOTH).
· HUM-EXT-04 (Engagement & Payment) — four shapes, four deployments, five rails, plus the World.xyz downstream connection for CASH.
· HUM-INT-01 (Platform Architecture) — four layers, shared spine, two tracks, all external infrastructure explicit (NEAR AI Cloud, NEAR Intents, LightLink, deBridge, Across, Bridge/Stripe, World.xyz), master control.
· HUM-INT-02 (Governance) — James → SoSem with D5 → D4 succession; rail authorization gates; standing gates; audit chronicle.
· HUM-INT-03 (Phase Execution) — P0 through P6, each with its component list.
· MACH-INT-01 (ER v3.1) — full entity-relationship diagram including SettlementRail table, all entities from v3.0 plus new settlement fields.
· MACH-INT-02 (Talent States) — lifecycle machine with preferredRail and worldParticipant noted at PROSPECT and PLACED states.
· MACH-INT-03 (Assessment/Artifact) — two concurrent state machines (Assessment, CodeArtifact) with stage transitions.
· MACH-INT-04 (Engagement, both tracks) — Track A and Track B state machines side by side; settlement rail chosen at signing, immutable thereafter.
· MACH-INT-05 (Invariants) — 21 invariants (I1–I21) including rail immutability and World.xyz eligibility; revoke cascade; what each invariant prevents.
· MACH-INT-06 (Solver Pipeline) — client intent + talent intent → NEAR AI Cloud TEE → ranked candidates → NEAR Intents 1Click → 5 rails → World.xyz downstream.
· MACH-INT-07 (Settlement Rails) — the load-bearing diagram. Five rails, five bridge paths, World.xyz downstream for TEMPO_CASH only, failure modes and closed behavior, rail invariants.

Rule for future exhibits: a diagram is EXTERNAL_VISIBLE only if it names no internal operators (SoSem, D5, D4 specifically), reveals no algorithm weights, and describes no failure modes. When in doubt, INTERNAL_ONLY.

---

PART VIII — FINAL PHASED SPRINT

VIII.1 — Phase map

Phase Depends on Objective Tap required
P0 — SoSem's extension pass (documented, not built) James's tap on the extended scope
P1 P0 + tap Reading room foundation (LR.0–LR.5) —
P2 P1 Assessment & lifecycle ladder (DA.1–DA.3) —
P3 P1, P2 Dual-track split + Role × Realm taxonomy —
P4 P3 NEAR marketplace — 5 rails proven —
P5 P4 Dual-track hardening —
P6 P5 + James's tap Open-repo gate lift James's tap

VIII.2 — PHASE 0 — SoSem extension pass

Objective: extend this document with concrete field-level detail, environment values, and gap analysis before any build begins.

Sub-sprint doneWhen
P0.1 Field-level extension Every entity has concrete storage shape, indexing, migration plan
P0.2 Sprint-level decomposition Every build phase below decomposed to daily granularity with owner + dependency graph
P0.3 Gap analysis Every directional item filed with a proposed default or an explicit "James's ruling required"
P0.4 Migration plan Existing records (v2.0, v2.1, v3.0) migrated to v3.1 with migrationPending flags where expertise roles unfilled

Exit gate P0: SoSem files the extended scope at docs/talent/CONSOLIDATED-SCOPE-v3.1.md, with a diff-vs-this-directive section, and James taps it. No build begins until the tap.

VIII.3 — PHASE 1 — Reading room foundation (LR.0–LR.5)

Sub-sprint Objective Exit gate (summary)
P1.1 Domain, gate, auth dev.uzemarkets.com live; middleware gate; OTP; HSTS; SPF/DKIM/DMARC Clean-browser sign-in works; unauthorized email refused
P1.2 Manifest + filters + track Index with five filters; track field; version + changelog; alias chain First mock onboarded; filters work; rename tested
P1.3 Developer list Record schema; Role × Realm pairs; stage-as-summary Full lifecycle tested on a test record
P1.4 Comms desk Templates; send log; revoke propagation Revoke kills session + GitHub in one request
P1.5 Proposal channel Comment surface; routing by subject; two-class change Comment accepted → silent sync; supersede → re-prompt
P1.6 Master control Admin interface; succession chain; first mock full flow SoSem performs full lifecycle for one real developer

Exit gate P1: SoSem completes the full lifecycle for one real internal-track developer (reading room → comment → revocation → chronicle intact), and one real external-track developer preview flow works end-to-end. Both send logs populated.

VIII.4 — PHASE 2 — Assessment & lifecycle ladder (DA.1–DA.3)

Sub-sprint Objective Exit gate (summary)
P2.1 Assessment module Two paths end-to-end; results attach to record; walkthrough captured One Path A + one Path B run; results render; retake works
P2.2 Six-stage ladder Artifact creation; stage transitions with human gate; chronicle; reverse transitions Full promote through FINAL; a reverse transition tested
P2.3 Vercel sandbox Three UI modes; isolation; ephemeral prune Spin-up of each mode; cross-sandbox access fails; retention tested

One amendment (v3.0): assessment results carry the Role × Realm pairs the assessment was designed for. A smart-contract assessment scores a talent's smart-contract fit specifically.

Exit gate P2: SoSem runs both assessment paths, promotes an artifact through FINAL → SANDBOX, spins up all three UI modes, and the talent's record shows the assessment result tied to the relevant Role × Realm pair.

VIII.5 — PHASE 3 — Dual-track split and taxonomy

Sub-sprint Objective Exit gate (summary)
P3.1 Track field rollout track on Talent, Mock, Engagement; migration with flag Track visible per record; track mismatch blocks view
P3.2 Role × Realm restructure Expertise migration to RoleRealmPair[]; UI for entry Record shows 5 pairs; legacy records flagged pending
P3.3 Expertise-based filters Role + Realm filters; admin filter by track + role + realm Filtered list is correct
P3.4 Skills-fit computation Preview.skillsFit from pairs vs mock requirements Accurate match/gap/growth per test engagement

Exit gate P3: SoSem filters by SMART_CONTRACT_DEV × LIGHTNING × EITHER and sees only correct records; opens one record and sees all pairs; opens a talent preview and sees accurate skills fit.

VIII.6 — PHASE 4 — NEAR marketplace with all five rails (TR.1–TR.4)

Sub-sprint Objective Exit gate (summary)
P4.1 Client intake + bookend Client record; intent authoring; bookend auto-authored Client posts intent; bookend renders
P4.2 Talent preview + skills fit Preview surface; consent gating; accept/decline Talent accepts a preview; consent logged
P4.3 NEAR AI Cloud + NEAR Intents Solver runs in TEE; signed intent via 1Click API; ranked candidates with reasoning Full cycle: intent → solver → signed → engagement
P4.4 Payment escrow — 5 rails All five rails proven; Payment record with correct fields per rail Five cycles demonstrated (see VIII.7)

VIII.7 — P4.4 exit gate expanded (v3.1)

· Base cycle — AUG engagement on BASE_USDC; Payment record with nativeTx; audit tx on Base.
· Solana cycle — PROJECT engagement on SOLANA_USDC; Payment record with nativeTx; audit tx on Solana.
· Robinhood cycle — engagement on ROBINHOOD_USDG; Payment record with bridgeTx (Across); talent's USDG balance verified on Robinhood Chain after settlement.
· Tempo cycle — engagement on TEMPO_CASH; Payment record with cashIssuanceRef; talent's CASH balance verified on Tempo; worldMarketEligible flag verified by attempting a test split on a live World market (read-only).
· Dispute cycle — engagement opens a dispute; resolution releases to correct side; escrowStatus reflects outcome.

Pass condition: all five cycles demonstrated in the running system, each with correct Payment record fields. A rail-cycle that succeeds on payment but fails the record fields does not pass.

VIII.8 — PHASE 5 — Dual-track hardening

Sub-sprint Objective Exit gate (summary)
P5.1 Track A lifecycle Internal hire end-to-end without marketplace/escrow Complete without touching marketplace or escrow
P5.2 Cross-track transitions EITHER talent transitions at engagement end Both directions tested; chronicle shows both
P5.3 Client-preview consent Client sees talent history only with consent Without consent fails clearly; with consent renders
P5.4 Reporting Reports by track and Role × Realm Generated report shows correct counts

Exit gate P5: SoSem executes one internal hire and one external placement side by side; records remain independent; reporting distinguishes them; cross-track transitions log correctly.

VIII.9 — PHASE 6 — Open-repo gate (James's tap)

Sub-sprint Objective doneWhen
P6.1 Talent admission protocol Published criteria for open marketplace Criteria filed at docs/talent/OPEN-MARKET-ADMISSION.md
P6.2 Dispute arbitration protocol Published resolution protocol replacing SoSem-as-person Protocol filed; pilot arbitration in shadow mode
P6.3 Standards compliance Mock/bookend/engagement standards published and enforced Automated check flags failed manifest rows
P6.4 Gate lift James's tap confirms HR placement + payment proven Repo opens; marketplace opens to qualifying clients

Exit gate P6: James's tap. Until then, Phase 6 remains in draft.

VIII.10 — Gate and dependency matrix

Phase Depends on Blocks
P0 — All phases
P1 P0 + James's tap P2, P3 partially
P2 P1 P3 partially, P5
P3 P1, P2 P4, P5
P4 P3 P5, P6
P5 P4 P6
P6 P5 + James's tap on gate conditions Open marketplace launch

Open-repo gate conditions (all three required):

1. HR placement infrastructure proven live via P4.
2. Payment infrastructure proven live via P4 (all five rails).
3. James's tap.

---

PART IX — OPEN ITEMS FOR JAMES'S RULING

Six directional items. SoSem carries each into P0.3 with a recommendation; James's tap either confirms or overrides.

# Item Recommendation
1 AI_SI_SPECIALIST meaning — "Systems Integration" or other expansion (Systems Integrator, Solution Integrator, Strategic Innovation)? Confirm before P0.4 migration runs
2 Track transition authority — INTERNAL → EXTERNAL_PLACED is routine or formal? Routine: SoSem's. Founder-tier: James's tap. Both logged
3 Assessment re-take cooldown — how long between attempts? 14 days between attempts on the same path; no total-attempt cap
4 Role × Realm pair ceiling — 5 active only, or overflow? 5 active + historicalExpertise[] for overflow; filterable but not weighted in matching
5 Track-A payroll rail — in scope or entirely external? Out of scope. Invoice/payroll handled by an existing system, not this marketplace
6 Default settlement rail (general, not AEInfo-linked) — Base USDC, Solana USDC, or other? Base USDC for general use; Solana USDC for AEInfo-adjacent scopes; TEMPO_CASH only when scope is explicitly AEInfo-linked

Additional items from prior versions:

# Item Recommendation
7 Payment rails first (from prior TR directive) Superseded by item 6 above (now 5 rails, not 2)
8 Dispute resolution model post-open-repo — adjudication panel, automated protocol, or delay-then-release? Defer to P6.2 filing; James rules at that time
9 Client onboarding standards — open to any client, or gated like talent? Defer to P6.1 filing
10 Open-repo timing — immediate on gate lift, or probationary window? 90-day probationary window under published standards, then open

---

PART X — CHANGE LOG

Version Date What changed Why
v1.0 — Reading room foundation 2026-11-18 Six-answer response (Q1–Q6) + LR.0–LR.5 sprints James's original request
v2.0 — Talent Vertical Directive 2026-11-18 Reading room → marketplace; TR.1–TR.4 sprints; settlement infrastructure; open-repo gate James's scale change: Talent as vertical
v2.1 — DAL Addendum 2026-11-18 Assessment module; six-stage ladder; Vercel sandbox; DA.1–DA.3 sprints James's direction to add developer assessment
v3.0 — Consolidated directive 2026-11-18 Dual-track model; Role × Realm taxonomy; P0–P6 phase structure; 13 exhibits (external + internal, human + machine) James's consolidation directive
v3.1 — Rail integration correction 2026-11-18 NEAR AI Cloud, NEAR Intents 1Click, LightLink, Tempo/Stripe CASH; five-rail settlement matrix; MACH-INT-07 added; P4.4 gate expanded James's correction on incomplete rail integration

Supersession rule: where any earlier version conflicts with v3.1, v3.1 governs. Where earlier content survives unchanged, it is carried forward in the current directive.

---

PART XI — STANDING

This document is the operating specification for the AEInfo Talent Vertical, version 3.1. It supersedes the v3.0 directive and all prior partial exhibits.

Standing rules:

· James's tap authorizes. SoSem executes.
· No keys, addresses, or credentials travel through this surface.
· Corrections come back as numbered sprints, not as commentary.
· The design is the design. What remains is the work.

What "build-ready" means at v3.1:

· Every entity has a schema.
· Every state machine has transitions.
· Every invariant has a named check.
· Every rail has a bridge path and a failure mode.
· Every phase has an exit gate observable in the running system.
· The five settlement rails are proven end-to-end in P4.4 before P5 begins.

The structural integration that holds the verticals together:

A talent paid on TEMPO_CASH holds the exact Bridge-issued CASH World.xyz uses as collateral. That talent goes from "paid for work" to "positioned on a prediction market" without a conversion step. That is why the talent vertical and the prediction market vertical are one platform, not two — and it is the reason this directive is not a standalone product but a load-bearing member of the AEInfo system.

Nothing in this document is claimed as adopted. Adoption is James's tap. SoSem executes the P0 extension pass, files the extended scope, and awaits the tap before P1 begins.

---

End of consolidated engineering document. All exhibits available at docs/talent/exhibits/ in the repo. All schema versions in logic/schemas.json. All sprints reproducible from the repo per the established pattern.