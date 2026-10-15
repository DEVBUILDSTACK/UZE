# KVM2 Tri-Level Agentic Voice — Specification

**Date:** 2026-10-14. **Status:** SPEC for build. **Author:** SoSeem, per James.
**Host:** Hostinger KVM2 (comms & messaging VPS). **Voice stack:** Grok Voice /
Telnyx / LiveKit, Hermes Native Gateway (per stack spec).

---

## Architecture: three levels

### L1 — Entry: Hospitality team pool

- First voice of the concierge. Human-expert pool covering **all markets**
  and **all languages** (per James: Male-only level).
- Triage: welcome, identify intent, route to the right specialist desk.
- Owns the warm handoff — never a cold transfer; context travels with the call.

### L2 — Specialist desks

| Desk | Domain |
|---|---|
| **GIRA** | General concierge guidance — events, tickets, touring, stay, cancellations, secondary-market resale |
| **GIRAx** | Secondary & Preowned — UZED.si resale, listings, buyback, advance-listing |
| **ONE** | Physical assets intelligence, brokerage, sealed-bid auctions |
| **SoSim** | DJ & experiential music agency talent |
| **SoSim Sisters** | Local-metro creator contractors: artists, performers, comedians, celebrities, security & secure transport services |

Each desk is an agent persona with its own knowledge scope, but all share
the caller context from L1 and the UZE backend (events, listings, user profile).

### L3 — Execution

Booking, payment, and confirmation handoff to the backend:
- Ticket/event booking → `services/api` (tickets, listings)
- Resale listing → UZED.si flow
- Talent booking → SoSim agency pipeline
- Settlement → x402 / USDC rails (per treasury spec)

L3 never negotiates — it executes what L2 arranged and confirms.

---

## Call flows (v1)

1. **Marketplace assist (GIRA):** "I need to cancel my Friday tickets and
   resell two" → L1 → GIRA desk → verifies booking → L3 cancels + lists on
   UZED.si → confirmation by voice + WhatsApp.
2. **Talent booking (SoSim):** "Book a DJ for our corporate event in Miami"
   → L1 → SoSim desk → availability, quote → L3 books → confirmation.
3. **Creator request (SoSim Sisters):** "We need a comedian and secure
   transport for Saturday" → L1 → Sisters desk → metro-matched contractors.
4. **Asset brokerage (ONE):** "I want to sell my preowned console bundle"
   → L1 → ONE desk → valuation, sealed-bid auction setup → L3 lists.
5. **Resale (GIRAx):** "What's my ticket worth now?" → L1 → GIRAx desk →
   pricing intelligence → L3 lists or holds.

---

## Technical notes

- Runs on KVM2 alongside the technocore-chat agent server (Buzz/Technocore rooms).
- Agent-to-agent coordination between desks over the agent-chat protocol
  (see `docs/AGENT-CHAT-C3-EVALUATION.md`).
- Caller identity: the mobile captured in the SocialFi onboarding flow;
  WhatsApp follow-ups via Meta Business account (warm/opt-in only).
- Languages: L1 pool covers all launch markets (EN/ES/PT + dialects per i18n spec).
- Recording/consent: per-market call-recording disclosure before L2.

---

## Geographic scope (per James, 2026-10-14)

**Physical markets services: Miami – Fort Lauderdale & Palm Beaches for MVP,
through Q2 2027.** The SoSim Sisters local-metro desks (artists, performers,
comedians, celebrities, security & secure transport) launch confined to the
South Florida triangle. Expansion beyond it opens after Q2 2027.

## Build prerequisites

- [ ] KVM2 SSH access (Phase 0 — James to provide)
- [ ] Telnyx + LiveKit credentials in KVM2 env
- [ ] Grok Voice / Hermes gateway on KVM2
- [ ] Meta Business account (Nov 5) for WhatsApp follow-ups
- [ ] Backend booking endpoints the L3 layer calls (tickets, listings)

## Open questions for James

1. L1 "Male-only level" — confirm the staffing rule as stated.
2. ONE desk: does sealed-bid auction execution use Arcium (per scope) from day one?
3. ~~SoSim Sisters metro coverage at launch: which metros first?~~ Answered 2026-10-14: Miami–Fort Lauderdale & Palm Beaches, MVP through Q2 2027.
