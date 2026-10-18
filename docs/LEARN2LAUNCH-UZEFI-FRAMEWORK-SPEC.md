# Learn2Launch UZE.fi Framework Spec — DRAFT v0.1

**INTERNAL — NOT FOR EXTERNAL SHARING.** Draft for James's review. Assembled 2026-10-18.

## 1. Purpose

The Learn2Launch UZE.fi framework is the out-of-the-box stack every
Learn2Launch accelerator project builds on. A project that joins the
accelerator gets knowledge infrastructure, agentic payments, treasury
operations, and risk screening working on day one — which means it is
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
  API keys. Metered per tenant, settled on-chain.
- Testnet only until the 2026-11-10 decision gate. Every live charge needs
  per-action approval naming account, amount, asset, and timing.

### Layer 3 — Altitude hierarchy (treasury as a service)
We operate Altitude's capabilities as a managed service inside the
framework (Altitude provides the APIs; the integration depth is ours):
- **Data** — financial memory: balances, transaction history across
  Solana addresses. The agent knows what it holds.
- **Platform** — treasury operations: counterparties, Squads multisig as
  account connection. The agent manages money like an institution.
- **Risk** — screening: every payment screens the counterparty before it
  clears.

### Layer 4 — Range (security intelligence)
- Independent risk intelligence complementing Altitude Risk: address
  screening and threat signals before funds move.

## 3. Why this incentivizes adoption

No accelerator project wires five vendors on day one. The framework ships
with all four layers already working, so the default choice is our stack.
Each project that builds this way deepens the framework's usage data and
integration depth, which makes the next project's decision easier —
a flywheel: more projects → deeper integration → easier adoption.

## 4. Project token pathway (gated)

Network-effect projects earn the token pathway — it is never day-one.
Three gates, all must pass:

1. **Minimum business parameters** — the project demonstrates real
   operating metrics (to be defined as underwriting criteria).
2. **Stage-gate acceptance** — formal phase review and sign-off.
3. **On-chain layer maturity** — the project's on-chain footprint meets
   the maturity bar (activity, security posture, history).

On passing, the affiliate unlocks its **project token** issuance within
the framework.

## 5. Venture-debt micro-loan facility

Affiliates past the gates become eligible for **venture-debt micro-loans**:

- **Syndicate assembly:** lenders assemble as LPs on the UZE launch
  architecture — standardized, framework-native.
- **Structure:** **Fundio.vc-led convertible LP syndicate.** Convertible
  terms give lenders upside (conversion into token/equity), which is what
  makes micro-loans to early-stage projects economically viable for the
  syndicate.
- **Terms:** standardized convertible note / token warrant templates
  (to be drafted).

This extends Fundio.vc's capital-engine role with Learn2Launch as its
exclusive affiliation: acceleration in, capital out, all on UZE rails.

## 6. The project journey

```
Join accelerator
  → Build on the framework out of the box (UZE_KB + x402 + Altitude/Range)
  → Operate: earn, spend, treasury, compliance — all UZE-native
  → Hit the three gates (business params, stage-gate, on-chain maturity)
  → Project token pathway opens
  → Venture-debt micro-loan eligibility via the Fundio.vc syndicate
```

## 7. Hard parts (named, not deferred)

1. **Regulatory.** Pooled lending plus project tokens is the
   highest-touch piece of this design. Real legal structuring first:
   accredited LPs, offering exemptions, jurisdictional review — before
   anything is offered to anyone.
2. **Underwriting.** "Minimum business parameters" must become actual
   credit criteria, owned and operated as a function. Owner TBD.
3. **Syndicate terms.** Convertible note / token warrant templates must
   be drafted and reviewed before the first assembly.
4. **Gate discipline.** The Nov 10 testnet boundary applies to every
   layer: narrative and framework now, live value movement only after
   the decision gate.

## 8. Status

DRAFT v0.1 — internal. Awaiting James's review and corrections. Open
inputs needed: underwriting criteria owner, legal structuring lead,
syndicate term templates.
