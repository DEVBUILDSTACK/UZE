# Learn2Launch UZE.fi Framework Spec — DRAFT v0.3

**INTERNAL — NOT FOR EXTERNAL SHARING.** Draft for James's review. Assembled 2026-10-18.

## 1. Purpose

The Learn2Launch UZE.fi framework is the out-of-the-box stack every
Learn2Launch accelerator project builds on. A project that joins the
accelerator gets knowledge infrastructure, agentic payments, and treasury
operations working on day one — which means it is
**truly building on UZE by default**, not by wiring five vendors together.

The framework is the enticement. Adoption of each layer follows from
bundling: the path of least resistance runs through our services.

## 2. The framework layers

### Layer 1 — UZE_KB (knowledge infrastructure)
- Monolithic, auto-assembling knowledge base across all repos; searchable
  hub with repo/topic filters; weekly re-assembly.
- Offered as a Learn2Launch UZE.fi framework capability: affiliate companies
  get on-the-fly KB builds — when prompted (agent skill) or when clicked on
  the monolithic index (per-company view generation).

### Layer 2 — Agentic x402 (payment rail)
- Agents pay per request in USDC, HTTP-native (HTTP 402), no accounts or
  API keys.
- Permissionless and non-custodial: the accelerated company owns and
  controls its x402 accounts. Learn2Launch does not meter, hold, or
  operate these accounts.
- Cash-based, so no credit risk: a payment clears only if the account
  holds the USDC; otherwise the request errors. The company keeps its
  accounts funded and sets its own programmatic rules — spend limits,
  allowlists — governing what its agents may buy.
- Testnet only until the 2026-11-10 decision gate. Every live charge needs
  per-action approval naming account, amount, asset, and timing.

### Layer 3 — Altitude (treasury as a service)
We operate Altitude's capabilities as a managed service inside the
framework (Altitude provides the APIs; the integration depth is ours):
- **Data** — financial memory: balances, transaction history across
  Solana addresses. The agent knows what it holds.
- **Platform** — treasury operations: counterparties, Squads multisig as
  account connection. The agent manages money like an institution.

## 3. Why this incentivizes adoption

No accelerator project wires five vendors on day one. The framework ships
with all four layers already working, so the default choice is our stack.
Each project that builds this way deepens the framework's usage data and
integration depth, which makes the next project's decision easier —
a flywheel: more projects → deeper integration → easier adoption.

## 4. Project token pathway (gated) — cursory at this stage

Network-effect projects can earn a token pathway — never day-one. Three
gates: minimum business parameters, stage-gate acceptance, on-chain layer
maturity. The shape is simple: prove the business, then the token. Detail
comes later.

## 5. Venture-debt micro-loans — cursory at this stage

Gated affiliates become eligible for micro-loans through a Fundio.vc-led
convertible LP syndicate assembled on UZE's launch architecture.
Mechanics, terms, and legal structuring get designed when we get there —
not now.

## 6. The project journey

```
Join accelerator
  → Build on the framework out of the box (UZE_KB + x402 + Altitude)
  → Operate UZE-native: earn, spend, treasury
  → Clear the gates → token pathway and capital access open in time
```

## 7. Notes for later (not now)

- Regulatory structuring before any token or lending offer.
- Underwriting criteria owner TBD.
- Nov 10 testnet boundary applies to every layer.

## 8. Status

DRAFT v0.1 — internal. Awaiting James's review and corrections. Open
inputs needed: underwriting criteria owner, legal structuring lead,
syndicate term templates.
