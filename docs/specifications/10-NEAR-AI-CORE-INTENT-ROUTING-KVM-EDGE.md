# 10 — NEAR AI Core, Intent Routing, and KVM Edge Architecture

**Status: ARCHITECTURE SPEC — DeepSeek's refined directive, relayed by
James 2026-11-09. Refines spec 09 (which remains the Sprint 2 kickoff
draft for the team structure and gates). Diagram:
`docs/diagrams/08-hermes-near-architecture.md`. The KVM/Hermes integration
is NOT built during hackathon week; Sprint 2 (Nov 15) begins it.**

UZEmarkets is not a Web2 app that happens to use AI. It is a **NEAR
AI-native framework built on NEAR Intents**. This spec draws the hard line
the identity requires: a **Core Protocol** (the UZE repo) and **Edge
Infrastructure** (the KVM), and states exactly where NEAR AI and NEAR
Intents sit inside the Agentic Team of Response.

## 1. The repo vs. KVM boundary (where things live)

The core monorepo is not polluted with edge infrastructure code.

- **The UZE Monorepo (source of truth)** contains: the Rust smart
  contracts, the FastAPI orchestration layer, the Next.js DevPortal, the
  Postgres database schemas, and the Agent APIs
  (`/api/v1/agents/gira/*`, `/api/v1/agents/sura/*`, the Assuraties claim
  and juror surfaces). **NEAR AI and NEAR Intents are implemented here,
  and only here.**
- **Hostinger KVM (the edge)** contains: the Hermes harness, the Grok
  sensing bots, and the LiveKit/Telnyx voice concierge. These are external
  microservices on separate infrastructure. They hold **no database
  schemas**; they interact with the core strictly via authenticated REST
  APIs and NEAR Intents.

## 2. The NEAR AI engine (the brain)

All inference in the UZEmarkets ecosystem routes through **NEAR AI
Cloud**. There are no direct external LLM calls (no OpenAI, no Anthropic)
in the runtime.

- **Attested inference.** GIRA (A·N·R·D), SURA (HiCRE), and the Juror Team
  (Assuraties) call the NEAR AI REST endpoint (or SDK) with TEE
  attestation.
- **Verification before persistence.** Responses are cryptographically
  verified (the SDK `verify_response` path, per the C-4 transport ruling)
  before anything they produced is written to the Precedent Index or the
  database; a response whose verification did not succeed is recorded
  with that state, never silently treated as verified.

## 3. NEAR Intents (the nervous system)

Agents do not merely call APIs; they broadcast **Intents**.

- **Intent broadcast.** When Grok (on the KVM) senses a market signal, or
  a human needs an underwriting, the system formulates a NEAR Intent
  (e.g. `Intent::Underwrite_A_N_R_D`, `Intent::Verify_Precedent`).
- **Solver matching.** The Hermes harness (or the 1Click API) routes the
  Intent to the appropriate agent — GIRA, SURA, or a specific Juror seat.
- **Settlement.** When the agent completes the work, settlement (and the
  x402 payment) executes on-chain via Chain Signatures. Settlement of
  record remains USDC on Solana; the Iron Rule is unchanged — no claim
  transition executes a financial transaction.

## 4. The multi-agentic team structure

- **The Orchestrator (Hermes, on KVM):** listens for external signals
  (X.com, voice, API), formulates Intents, routes them to the UZE core.
- **The Underwriters (GIRA & SURA, on NEAR AI):** receive the Intent,
  execute inference via NEAR AI, return the attested JSON.
- **The Jurors (Assuraties, on NEAR AI):** when a claim is contested, the
  panel of diverse models is invoked via NEAR AI; verdicts write back to
  the Precedent Index, and panel TEE attestation hashes anchor on-chain
  (DeepSeek audit directive, in build).

## 5. Current state vs. this architecture (honesty table)

This spec is the Sprint 2 target. What is true in the hackathon build
today, stated plainly so the spec never overclaims:

| Element | Hackathon state (Nov 9) | This architecture (Sprint 2) |
|---|---|---|
| Juror Team inference | NEAR AI path built (REST + SDK verify, C-3/C-4); live runs blocked on org credits (402) | Same path, live, with panel verdicts + on-chain TEE hash anchoring |
| GIRA / SURA | Deterministic assessors over filed data (ProviderSnapshot cache; compose market state) behind x401/x402 gates — **no live inference today** | NEAR AI attested inference as their reasoning step |
| Intent routing | Direct REST to the agent endpoints; the Intent Gateway package is planted (`services/compose/src/intent_gateway/`, not wired) | Intents formulated/routed via the gateway + 1Click; Hermes pushes Intents from the edge |
| Hermes / Grok / KVM | Not integrated; specs 09 + 10 and diagrams 07 + 08 only | KVM microservices live; sensing → sanitizer → Intents; Double-Tap on all drafts |
| Sanitization | Juror-path slice in build (Unicode stripping + canary on claim/precedent text) | Full pipeline on all edge→core flows |

## 6. Execution plan

- **Immediate (hackathon):** no KVM/Hermes integration this week. This
  spec and diagram are filed; the core (GIRA, SURA, Jurors) keeps calling
  NEAR AI and preparing TEE attestation hashes (anchoring in build).
- **Sprint 2 (Nov 15):** KVM Hermes setup begins. Grok bots and the voice
  concierge are built as separate microservices that push Intents to the
  UZE core, under spec 09's gates (Double-Tap; sanitization before
  ingestion; James's taps on posting policy and Grok spend still open).

## 7. Addendum — geographic scope (2026-11-09)

The paired US primary HiCRE markets:

- **Market 1 — Mid-Atlantic:** Baltimore, MD + Washington, DC metro.
- **Market 2 — South & Central Florida:** Miami, Fort Lauderdale,
  Tampa, Orlando.

The hierarchy around them: **Tier 1 (US)** — the paired markets.
**Tier 2 (US Diaspora)** — the East Coast corridor Boston→Miami:
Portuguese-speaking (primarily Brazilian) entrepreneurs, HNW
individuals, cross-border real-estate investors. **Tier 3 (South
America)** — Brazil, extending immediately into Paraguay and
Uruguay. The demo micro-regions (Brickell, Aventura, Bethesda,
Arlington, Baltimore-NW, Kissimmee, Tampa, and the seeded
Baltimore City / Towson / Fort Lauderdale additions) are the
micro-region layer inside Tier 1.

## 8. Addendum — the Messaging & Intelligence VPS (MIV) (2026-11-09)

The MIV architecture includes the Meta-Business API. The flow:

**Meta-Business API (WhatsApp) → MIV Hermes Harness → UZE Core
(GIRA/SURA) → NEAR AI inference & underwriting.**

The channel is the lead-generation and distribution funnel for
HiCRE and A·N·R·D: owners and operators reached where they
already communicate, routed through the harness into the same
core and the same underwriting — one record, not a side pipe.
The stated target sets are the 80,000-member Brazilian
business-owner network and the US Portuguese-speaking investor
corridor (Boston→Miami). Recorded here as strategy; the MIV
build is Sprint 2+ work, behind spec 09's gates.
