# 09 — The Multi-Agentic Team & Hermes Architecture (Sprint 2 Kickoff Draft)

**Status: ARCHITECTURE SPEC — drafted 2026-11-09 per DeepSeek's directive
(relayed by James). The Hermes build does NOT begin until the Nov 15
Sprint 2 kickoff. Diagram: `docs/diagrams/07-hermes-agentic-team.md`.**

Terminology note: this spec uses James's settled spellings — **Assuraties**
(present, plural-only) and **Assuratized** (resolved). Renderings in the
directive package ("Assuratied", "Assurete") are dictation noise and are
not adopted.

We are not building a single-agent system. We are building an **Agentic
Team of Response**: diverse agents with separated roles, checked by each
other, under a human gate — the same separation-of-roles principle the
Juror Team applies inside Assuraties (no single operator is writer,
moderator, and juror).

## 1. The infrastructure boundary (KVM vs. Build VM)

- **Hostinger KVM — the always-on infrastructure.** The Hermes harness,
  the Grok X-sensing bots, and the cron estate (Content Desk pulses,
  MATTY-P desk, the twice-daily monitors) live here. Persistent services
  require a host that does not sleep or get replaced. The dual-VPS
  best-practices note (2026-10-28) governs placement: media plane vs.
  trust plane, a single Hermes native gateway for the Buzz Rooms and
  Technocore (flopsai.xyz) messaging, kill switch, spend ceilings,
  queued outbound.
- **Build VM — ephemeral development only.** Specs, code, verification.
  Nothing production-persistent runs here.

## 2. The multi-agentic team structure

- **GIRA (NEAR AI)** — the underwriting agent for the A·N·R·D track
  (agriculture, natural resources, development). Live endpoints shipped in
  Sprint 1.5 (`/api/v1/agents/gira/underwrite`, `/debug`).
- **SURA (NEAR AI)** — the underwriting agent for the HiCRE track
  (hospitality + income CRE). Live endpoint shipped in Sprint 1.5.
- **The Juror Team (Assuraties)** — the panel of diverse models that judge
  contested claims and write back to the Precedent Index (specs 07 + 08;
  panels and on-chain attestation anchoring per DeepSeek's audit
  directive). Juror seats are scored publicly; precedents are the shared
  memory.
- **Hermes Harness** — the orchestrator on the KVM. It receives signals
  from the Grok sensing layer and routes tasks to GIRA, SURA, or the
  Juror Team. The harness runs under the Jev framework disciplines
  already specced for the Desk (BRIEF/HANDOFF checkpoints, one owner per
  assignment, two-attempt bounds, done-checklists).

## 3. The Grok sensing layer & the Double-Tap rule

- **Sensing.** Grok AI runs on the KVM, monitoring X.com for market
  signals, mentions, and A·N·R·D / HiCRE news. It feeds sensed data into
  Hermes. Grok's structural advantage is its native live read of X; no
  other model in the stack has it.
- **Drafting.** Grok drafts posts and reports from sensed data plus
  UZEmarkets DB state (micro-region pulses, claim activity, learning-feed
  events).
- **The Gate.** Grok is a drafting assistant, **not an autonomous
  publisher**. Every draft triggers a PENDING_APPROVAL notification to
  James. Public output follows the standing Double-Tap: Tap 1
  (Confirming) freezes the final draft; Tap 2 (Go Public) is a separate,
  later, explicit tap naming the channel. Nothing goes out on silence,
  staging, or scheduling.

## 4. Security: untrusted input sanitization

X content — and any Grok output derived from it — is **untrusted input**.
Nothing sensed enters GIRA, SURA, the Juror Team, the Precedent Index, or
ProviderSnapshots without passing the sanitization pipeline:

- **Unicode stripping** — invisible characters (zero-width, bidi
  controls, tag characters) are removed from all text before ingestion;
  the pattern Hermes itself adopted in its Nov 8 batch (invisible-Unicode
  stripping in MCP metadata, cookie masking in logs).
- **Canary traps** — per-context canary tokens are embedded in prompts
  that carry untrusted text; a canary surfacing in a model's output marks
  the run as compromised and the output is discarded, never stored.
- **Strict schema validation** — Grok output enters the FastAPI backend
  only as schema-validated JSON (the partner-ingest pattern: validate,
  stage, never write through).

**Sequencing inside this rule:** the juror path is protected first,
inside the hackathon build — claim statements and precedent text are
sanitized before they enter the juror prompt, because that surface is
live today. The full Grok-output pipeline lands with the Hermes build at
the Nov 15 kickoff.

## 5. What is NOT decided here (James's taps, in order)

1. X posting policy for the KVM-resident harness (draft-only is the
   default this spec assumes).
2. Grok tier / API spend for the sensing layer (money gate).
3. Whether the Buzz/Technocore Rooms become a routing target for team
   output in Sprint 2 or later.
