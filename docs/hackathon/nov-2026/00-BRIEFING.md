# SOSEM BRIEFING — Read This First

**From:** James (founder) and DeepSeek (directing agent)
**To:** SoSem (implementing agent)
**Date:** 2026-11-07
**Purpose:** Orient you to changes made after your last state. Everything below supersedes your prior understanding where it conflicts.

---

## What you already know

- The October 30 sprint series: Sprint 0 closed, Sprint 1 open with Slices 1–2 in progress
- The six ratified directives (ORM C, inventory consumer, deterministic classify(), uzemarkets-compose, commercial model, seat placement)
- The compose schema: 23 models, 8 enums, Alembic head d52f8b1a904c
- The R4 read-through contract with eight divergence codes
- The USDC-only settlement invariant (af20ad9)
- The Chain Signatures architecture as a concept
- The NEAR AI Inference SDK at a tools level

## What you do not know — the changes made tonight

Between roughly 17:00 and 21:00 Eastern on November 7, 2026, the following decisions were made. They are ratified.

### 1. Product pivot to income commercial real estate

UZEMARKETS is not a generic travel-and-venue marketplace. It is a **dual-surface marketplace for income commercial real estate** serving three asset classes:

- Residential rental apartments (30 doors up to 1,500–2,000+ building or cumulative community)
- Residential condos (same scale, HOA/board oversight)
- Hospitality and resort (same scale, short-stay market, extended stay only for relocation)

One analytical methodology across all three: model every role, model every opex line A–Z, account for brand fees, benchmark to micro-region.

### 2. Two service lines, one marketplace

**Service Line 1 — Assessment and Advisory.** A client posts a specification. A human specialist, an attested AI agent, or both bid to fulfill it. Deliverable: operating budget + property manager spec, micro-region benchmarked, verifiably produced.

**Service Line 2 — Talent Placement.** Once the advisory produces the operating budget and PM spec, the same marketplace places the property manager, management company, or operating talent against that spec. The advisory output is the hiring blueprint.

**The advisory feeds the placement. The placement fulfills the advisory.**

### 3. Micro-region is the analytical unit

Not "Miami" — **Brickell**. Not "DC metro" — **Bethesda, Arlington, Northwest Baltimore**. Micro-region is where tax jurisdiction, labor rates, opex, and brand fee comparables actually diverge. This is the differentiation against national CRE firms, which benchmark at metro level.

### 4. Dual-surface, not headless-only

The marketplace serves both agents and humans. One backend, two projections. Agent gets JSON API. Human gets rendered HTML. Any field on one and not the other is a defect.

For the hackathon: **agent surface fully interactive. Human surface read-only for SEO/GEO.** Interactive human UI lands in Sprint 2.

### 5. Hackathon extended to November 14

Original deadline: November 10. Extended: **November 14, 2026, 11:29 UTC** (approximately 06:29 Eastern).

Seven days instead of four. The extension adds:
- **NEAR AI inference moves from narrative to built** (Day 4)
- **Read-only HTML surface fully in scope** (Day 6)
- **x402/x401 mock flow as stretch** (Day 5)
- **Diagnostic retry window** if Chain Signatures fails on Day 1

### 6. Hackathon is Sprint 1.5 — encapsulated, not a fork

The seven-day hackathon is a bounded pull-forward of Sprint 2 content. Sprint 2 (filed) remains intact and unchanged. Sprint 1.5 produces Sprint 2's seed artifacts. Merge to `main` by November 13 EOD Eastern. Sprint 2 inherits everything structural and discards only demo fixtures and the recording.

### 7. All work happens in the existing repo

**Repo:** `DevBuildStack/UZEMARKETS`
**Branch:** `hackathon/nov-2026`
**Do not create a new repo.** The schema, frozen migrations, and ratified directives all live in the existing repo. The hackathon is an additive migration plus new directories, not a new project.

### 8. The demo

A syndicate acquiring a 340-room Aloft-branded hotel in Miami-Brickell posts a spec. A human CRE analyst ($22,500, 60 days, on-site + remote) and an AI agent ($4,200, 48 hours, autonomous, attested inference) both bid. The syndicate selects. Settlement is Solana USDC, authorized by a NEAR identity via Chain Signatures. The agent's analysis is verifiably produced inside NEAR AI Cloud's attested enclave. Every property analyzed becomes a comparable in a micro-region dataset.

### 9. The diagrams

Four Mermaid diagrams live in `docs/diagrams/` and are the visual reference for everything in this briefing:
- `01-marketplace-flow.md` — business view
- `02-technical-stack.md` — layer view
- `03-end-to-end-sequence.md` — demo walkthrough
- `04-intent-lifecycle.md` — contract state machine

Read all four before starting Day 1.

---

## What this means for you

**Your prior Sprint 1 work continues.** Slices 1 and 2 are not invalidated. The compose runtime, intake, classify(), suggest_slots(), the USDC invariant, the read-through contract — all still correct and still in `main`.

**Sprint 1.5 is additive work on a branch.** The branch `hackathon/nov-2026` adds:
- Rust contract scaffold in `contracts/near/`
- Intent schema (additive migration to compose)
- Intent API endpoints in `services/compose/api/`
- Chain Signatures settlement in `services/compose/api/`
- NEAR AI inference integration in `services/compose/`
- Read-only Next.js pages in `apps/web/`
- Documentation in `docs/diagrams/` and `docs/hackathon/nov-2026/`

**Nothing in Sprint 1.5 modifies the frozen migrations.** Any compose change is a new additive revision with from-empty replay verification. That rule has not changed.

**The rules that carried over from Sprint 0:**
- Additive migrations only
- From-empty replay before filing
- Statement-identical proof for edits claimed behavior-neutral
- Bidirectional tests for ledger-class bindings
- Kitchen Standard: evidence from the running system, verifiability and reversibility graded separately
- No tautological tests
- Frozen migrations never import live application source

**Your working authority:** You have standing authority for routine reversible code work inside ratified scope. Surface to James only on: ambiguity in a ratified decision, schema-invariant changes, staging/provisioning inputs, live services/api deployment effects, no-undo actions.

---

## What happens when you finish reading

Go to `01-PICKUP-TONIGHT.md` for today's work. Then `02-SPRINT-1.5-PLAN.md` for the seven-day plan. Then `03-PICKUP-NOV-15.md` for how the project resumes after the hackathon.
