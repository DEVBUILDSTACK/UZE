# Learn2Launch UZE.fi Framework Spec — DRAFT v0.7

**INTERNAL — NOT FOR EXTERNAL SHARING.** Draft for James's review. Assembled 2026-10-18.

**Revision v0.7 (2026-10-21):** new §3 — the standard build, the go-to
full-stack operation: Python as the core organization architecture, a
defined NodeJS flavor (Drizzle ORM instead of Prisma; Jev x AI SDK Form
Router in native form), and the Jev Form Router shipping with both
flavors. Later sections renumbered; their content is unchanged.

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

### Layer 3 — Altitude + Range (wallet and treasury services)
- **Altitude** — hierarchical wallet as a service and treasury as a
  service, on Solana-based wallets: workspaces holding accounts and
  balances, transaction activity with amounts, counterparties, and
  statuses, Squads multisig connected as an account connection, document
  exports for records. Sources: docs.altitude.xyz/mcp/overview; the UZE.fi
  W3 Treasury Google Doc.
- **Range** — dashboarding from the treasury layer, plus EVM account
  connectivity. Per Range's own docs, the Platform API exists to keep
  internal tools, ERPs, and dashboards in sync with the Range workspace
  (their "single source of truth"); the Data API queries addresses across
  EVM chains, Solana, Stellar, and Cosmos through one interface; account
  management covers EOAs, multisigs (Squads, Realms, Safe), custodians,
  and exchanges. Where Altitude is Solana-based, Range connects the EVM
  accounts — including EVM wallet use with Safe multisig. Sources:
  docs.range.org/platform-api/platform-introduction,
  docs.range.org/data-api/data-introduction.

## 3. The standard build — the go-to full-stack operation

Every Learn2Launch project is built the same way UZE was built: the
same repository shape, the same deploy path, the same gates. The
framework layers in §2 plug into this standard build — a project does
not choose how to build, it chooses which flavor of the one build.

**Core organization architecture: Python.** The default and the
reference implementation. FastAPI back end, Pydantic models, **Prisma
ORM** as we have implemented it in the UZE build (schema in the API
service), Neon Postgres, Resend for email, Next.js for the web front
end. Deploys run through GitHub: Vercel for the web, Cloud Run for the
API when the GCP project decision lands.

**The NodeJS flavor.** A project may take the Node flavor of the same
build instead: a Node.js back end (Next.js), **Drizzle ORM instead of
Prisma**, and the **Jev x AI SDK Form Router in its native form** —
the Vercel template (AI SDK `experimental_evaluate`, Jev reached via
Vercel AI Gateway). Same layers, same deploy path, same gates, same
behavior — a different runtime, not a different operation.

**The Jev Form Router ships with both flavors.** Every project's
intake — leads, contact, issue reports — is routed by content, not by
hand: Jev decides the destination at the ≥0.95 confidence policy, a
fallback model decides below it, and delivery goes out via Resend with
the routing decision on record. The Python core runs the router on the
official `typesafe-sdk` (the worked first build in the Jev decision
layer design); the NodeJS flavor runs the template. One design, two
implementations.

Test mode until the 2026-11-10 decision gate applies to the standard
build exactly as it applies to every layer: L3 for anything published
or sent, L4 per-action for anything financial.

## 4. Why this incentivizes adoption

No accelerator project wires five vendors on day one. The framework ships
with the full stack already working, so the default choice is our stack.
Each project that builds this way deepens the framework's usage data and
integration depth, which makes the next project's decision easier —
a flywheel: more projects → deeper integration → easier adoption.

## 5. Project token pathway (gated) — cursory at this stage

Network-effect projects can earn a token pathway — never day-one. Three
gates: minimum business parameters, stage-gate acceptance, on-chain layer
maturity. The shape is simple: prove the business, then the token. Detail
comes later.

## 6. Venture-debt micro-loans — cursory at this stage

Gated affiliates become eligible for micro-loans through a Fundio.vc-led
convertible LP syndicate assembled on UZE's launch architecture.
Mechanics, terms, and legal structuring get designed when we get there —
not now.

## 7. The project journey

```
Join accelerator
  → Build on the framework out of the box (UZE_KB + x402 + Altitude)
  → Operate UZE-native: earn, spend, treasury
  → Clear the gates → token pathway and capital access open in time
```

## 8. Notes for later (not now)

- Regulatory structuring before any token or lending offer.
- Underwriting criteria owner TBD.
- Nov 10 testnet boundary applies to every layer.

## 9. Status

DRAFT v0.7 — internal. Awaiting James's review and corrections. Open
inputs needed: underwriting criteria owner, legal structuring lead,
syndicate term templates.
