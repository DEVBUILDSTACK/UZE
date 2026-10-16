# Content Desk: Team, Skills & MCP Build Plan

**Date:** 2026-10-16 · **Status:** architecture approved for build
**Home:** `DEVBUILDSTACK/LEAD_GEN` (extended) · **Runs on:** KVM2 multi-agent harness
**Constraint:** everything in **test/testnet mode** until **Tuesday, November 10, 2026** —
no paid live accounts (WhatsApp, Meta Business, or otherwise) before that date.

## 1. The "hire" — agentic principal, not human (corrected per James 2026-10-16)

There is no human hire. The hire **is agentic**: one orchestrator agent
(scaling to multiple cooperating agents) with principal-level technical
Web3 + RAG + marketing expertise. Full résumé: `AGENTIC-HIRE-CV.md`.

- **Learning loops:** voice (KVM2 concierge) → intent models; in-app
  (SocialFi behavior) → feed/onboarding tuning; client feedback →
  RAG + template updates; internal RAG + **Vertex AI notebooks** as the
  working-memory/research bench, cooperating with **Cloud Run** workers.
- **Commercial path:** perfect the service internally on 456iP brands +
  @l2launch, then sell it as the **Content Desk & SI Generative Managed
  Services Suite**.
- The 7 Grok specialist agents below are its team; the 7 skills are its
  hands.

## 2. Grok agent team additions (KVM2 core team)

One front door (orchestrator, already chartered) + these specialists.
Each gets a narrow job, a checkable output, and the same approval levels
as the charter (L0–L2 autonomous, L3 publish needs human tap, L4 money
needs per-action approval).

1. **Growth Analyst** — funnel/attribution/experiment readouts; pairs
   with the hire. Turns LEAD_GEN sequence data into decisions.
2. **x402 Payments Engineer** — agentic payment flows, metering,
   settlement; testnet until Nov 10.
3. **Solana Builder** — Rust/Anchor programs, TS clients; UZE on-chain
   integrations.
4. **Cairo / Starknet Specialist** — privacy primitives, ZK payments
   alignment (UZD track).
5. **Video Director** — owns the GenAI pipeline (n8n scrape → stills →
   Seedance/OpenRouter → sync-2-pro lip-sync → Remotion composite):
   45s–3min films, 10–40s UGC CTAs, platform-cut for IG/TikTok.
6. **SocialFi Feed Architect** — X/crypto-Twitter mechanics + the
   Robinhood-brokerage SocialFi feed model: 20-second profile creation,
   QR share cards, verified-activity status, referral loop.
7. **Dashboard Builder** — Meta Business / Stripe Tempo / Altitude.xyz /
   Range dashboards. **Test mode only until Nov 10** — sandbox accounts,
   no live spend, no production data.

## 3. Our skills + MCP access

**Our skills (built in-house, `~/workspace/custom-skills/`):**
`growth-analytics`, `x402-payments`, `solana-anchor`, `cairo-starknet`,
`genai-video-pipeline`, `socialfi-feed`, `dashboard-builder`.
Scaffolded 2026-10-16; fleshed out as each agent proves its first loop.

**Accessed via MCP (theirs, not rebuilt):** MUZE WhatsApp (own numbers),
Meta Business — both **test/testnet only** until 2026-11-10. The Desk
may draft, queue, and dry-run; it may not send, spend, or publish live.

## 4. Test-mode guardrails (hard, until Nov 10)

- All new skills ship with the LEAD_GEN triple-gate pattern:
  explicit flag + environment authorization + credential presence.
  Anything live refuses without all three.
- No production sends (email, WhatsApp, social), no paid API usage,
  no live ad spend, no mainnet transactions.
- Sandbox/testnet credentials only; production credentials are not
  collected before Nov 10.
- The Nov 10 go-live is a **decision gate**, not a date trigger:
  James reviews test evidence, then authorizes each surface
  individually.

## 5. Build sequence

1. Scaffold skills (done 2026-10-16 — stubs with purpose, scope,
   test-mode constraints).
2. Prove one loop per agent, in this order: Growth Analyst (on real
   LEAD_GEN data) → Video Director (one 10–40s UGC CTA) → x402
   (testnet payment) → Solana Builder → Cairo → SocialFi Feed →
   Dashboard Builder.
3. Wire each proven skill into the KVM2 orchestrator routines.
4. Hire runs the human side in parallel from day one; agents are
   force-multipliers, not replacements.
5. Nov 10 gate: review test evidence per surface → individual
   go-live authorizations.
