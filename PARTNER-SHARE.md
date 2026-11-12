# UZEmarkets: Partner Architecture Framework

A navigation index for partners. Each link goes directly to the section it names.

### Status legend — truth in documentation

* 🟢 **VERIFIED BUILT** — code is live, tested, and passing in the current branch.
* 🟡 **BUILT AS MOCK** — code structure and API endpoints exist and are tested, but execution or external integrations are mocked (e.g., the CoStar-shaped adapter's synthetic data; UZE Assign and UZE Auction — no funds move, no custody is taken).
* 🔴 **PROPOSAL / ROADMAP** — architecture and design are finalized, but code is held for future sprints (e.g., the Yield Matrix database build, live confidential auction execution).

## 1. The Business & Underwriting Engine

*   [Executive Business Overview](https://github.com/DEVBUILDSTACK/UZE/blob/main/docs/01-business-overview.md) — 🟢 the dual-track engine (SURA/GIRA), the Mid-Atlantic proof of concept, HiCRE and ANRD
*   [UZE Underwrite Technical Spec](https://github.com/DEVBUILDSTACK/UZE/blob/main/docs/specifications/underwrite/README.md) — 🟢 the 7-bucket P&L taxonomy and T-12 normalization · 🟡 market data via the CoStar-shaped adapter (synthetic, license pending)

## 2. The Inference Economy & Treasury

*   [Autonomous Front End & Inference Economy](https://github.com/DEVBUILDSTACK/UZE/blob/main/docs/02-inference-economy.md) — 🟡 mocked execution with live swap quotes · 🔴 live attested inference at scale

## 3. Assignments, Auctions, & The Americas

*   [UZE Assign, Auction & Brazil Roadmap](https://github.com/DEVBUILDSTACK/UZE/blob/main/docs/03-assign-and-auctions.md) — 🟡 Assign & Auction surfaces · 🔴 Brazil agricultural test market
*   [UZE Assign Technical Spec](https://github.com/DEVBUILDSTACK/UZE/blob/main/docs/specifications/assign/README.md) — 🟡
*   [UZE Auction Technical Spec](https://github.com/DEVBUILDSTACK/UZE/blob/main/docs/specifications/auction/README.md) — 🟡 the Commitment Ladder and the human-gated Temporal Trigger · 🔴 live MPC execution

## 4. Integrated Ecosystem Layer — Ticketing & Information Markets

*Integrated 2026-11-12 by the owner's explicit override of the hackathon boundary, as mocks — the submission narrative in SUBMISSION.md is unchanged.*

*   **Venue Ticketing (per-seat NFT tickets)** — 🟡 BUILT AS MOCK: venue-as-data events, per-seat minting, listing, provenance-invariant transfers (the original NFT moves; no re-mint), verification, and recorded bridge intents across NEAR / LightLink / Solana / Ink / Base / Robinhood — `services/compose/src/ticketing.py`, all responses labelled `mock`, nothing settles
*   [GENSYN Bridge Spec](https://github.com/DEVBUILDSTACK/UZE/blob/main/docs/GENSYN-BRIDGE-SPEC.md) — 🟡 the mock derivation (scalar holder calls → distribution → threshold binary markets) · 🔴 the production information-market bridge it specifies

---

The full documentation in a single file: [UZE-MASTER-COMPOSITE.md](https://github.com/DEVBUILDSTACK/UZE/blob/main/UZE-MASTER-COMPOSITE.md) (historical archive).
