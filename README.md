# UZEmarkets: The Autonomous RWA Information Market

Welcome to the UZEmarkets repository. We are building the autonomous, AI-driven underwriting and information market for Income-Producing Real Estate (HiCRE) and Agriculture, Natural Resources & Development (ANRD).

Please select the appropriate track below for a deep dive into the architecture and business logic.

---

### 📖 The Documentation Hub

**1. The Executive Business Overview**
*The Mid-Atlantic proof of concept, our dual-track underwriting engine (SURA/GIRA), and the detailed mechanics of the HiCRE and ANRD asset classes.*
👉 **[Read the Business Overview](./docs/01-business-overview.md)**

**2. Core Autonomous Front End & Inference Economy**
*How we optimize digital assets for pre-funded, pay-as-you-go inference. Routing between encrypted frontier models and low-cost open-source models.*
👉 **[Read the Inference Economy](./docs/02-inference-economy.md)**

**3. UZE Assign, UZE Auction, & The Americas Roadmap**
*Monetizing RWAs through sealed-bid auctions, fractional escrows, and our agricultural yield test-market expansion in Brazil.*
👉 **[Read Assign & Auctions](./docs/03-assign-and-auctions.md)**

---

### 🛠 Technical Specifications (Deep Dives)

For developers and auditors looking for the actual implementation details:

*   [**UZE Underwrite Spec**](./docs/specifications/underwrite.md) — The 7-bucket P&L taxonomy, multi-year T-12 normalization, and the CoStar-shaped adapter (synthetic data, license pending).
*   [**UZE Assign Spec**](./docs/specifications/assign.md) — The assignment marketplace surface, fractional syndicate contribution receipts, and the Commitment Ladder.
*   [**UZE Auction Spec**](./docs/specifications/auction.md) — The confidential auction design, the Commitment Ladder schedule, and the Temporal Trigger with its human execution gate.

---

### Status key — how to read this repository

UZEmarkets labels the state of every surface honestly, in the docs and in the code:

* **BUILT** — implemented and covered by the test suite (`services/compose`, 286 tests passing at the Sprint 1.5 close).
* **BUILT AS MOCK** — the surface, vocabulary, and audit trail are real; execution is simulated and every payload says so (`mock: true`). No funds move, no custody is taken.
* **DESIGN / ROADMAP** — filed architecture and sequenced plans, not yet implemented.

Where a page describes a mechanism that is BUILT AS MOCK or DESIGN, the page says so at the point of description.

---

### Repository layout

Source of truth for the UZE ecosystem. Target org: **DEVBUILDSTACK**.

- `apps/uze-web` — UZE consumer front-end and the UZEmarkets public surfaces (underwrite, micro-regions, treasury)
- `apps/uzed-web` — UZED.si embedded secondary market (resale by UZE)
- `apps/siglayer` — SigLayer treasury + trade layer (vaults, DATs, yield tiers)
- `apps/command-center` — Command & Control Center admin console (incl. W3Treasury → SigLayer)
- `packages/girax` — GIRAx layer (provenance, attestation, attribution, authentication)
- `packages/uzd-token` — UZD multi-chain token (Solana + Robinhood Chain + Base)
- `packages/ui` — shared design system
- `services/voice` — KVM2 Grok voice lead-to-conversion services
- `services/api` — FastAPI/Python backend
- `services/compose` — the UZEmarkets composition layer: UZE Underwrite (SURA/GIRA), the AssurativeV2 trust layer, metering (x402/x401), treasury rails, UZE Assign and UZE Auction
- `docs/` — specs (brand/domain, entity/treasury/trading, wallet, hackathon)

## Stack

Next.js + TailwindCSS · FastAPI · PostgreSQL (Alembic) · NEAR (intent/identity plane) · Solana (USDC settlement of record) · Docker/Compose → Vercel + GitHub Actions.
