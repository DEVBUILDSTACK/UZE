# UZE-MASTER-COMPOSITE

> **Historical archive — a single-file concatenation of the modular documentation, generated 2026-11-12.** The living documents are the modular files linked from the root README; this composite is a snapshot record, regenerated from them, and is not the hackathon submission document (the submission narrative is filed separately in SUBMISSION.md). Status labels (🟢 VERIFIED BUILT · 🟡 BUILT AS MOCK · 🔴 PROPOSAL / ROADMAP) apply section by section, exactly as in the source files. Relative links inside each section are preserved verbatim from their source files and resolve at those files' locations in the repository.

---

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

*   [**UZE Underwrite Spec**](./docs/specifications/underwrite/README.md) — The 7-bucket P&L taxonomy, multi-year T-12 normalization, and the CoStar-shaped adapter (synthetic data, license pending).
*   [**UZE Assign Spec**](./docs/specifications/assign/README.md) — The assignment marketplace surface, fractional syndicate contribution receipts, and the Commitment Ladder.
*   [**UZE Auction Spec**](./docs/specifications/auction/README.md) — The confidential auction design, the Commitment Ladder schedule, and the Temporal Trigger with its human execution gate.

---

### Status legend — truth in documentation

UZEmarkets labels the state of every surface honestly, in the docs and in the code:

* 🟢 **VERIFIED BUILT** — code is live, tested, and passing in the current branch (`services/compose`, 286 tests passing at the Sprint 1.5 close).
* 🟡 **BUILT AS MOCK** — code structure and API endpoints exist and are tested, but execution or external integrations are mocked (e.g., the CoStar-shaped adapter's synthetic data; UZE Assign and UZE Auction, whose payloads carry `mock: true` — no funds move, no custody is taken).
* 🔴 **PROPOSAL / ROADMAP** — architecture and design are finalized, but code is held for future sprints (e.g., the Yield Matrix database build, live confidential auction execution).

Where a page describes a 🟡 or 🔴 mechanism, the page says so at the point of description.

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

---

# Part 1: The Executive Business Overview

## The Mid-Atlantic Proof of Concept & The ANRD Roadmap

### The Business Problem

Traditional real estate and asset underwriting is highly siloed. The financial mechanics of a 300-room Marriott in Baltimore require an entirely different analytical approach than a 500-acre dormant agricultural tract in rural Maryland. Lenders, investors, and SMEs are forced to use fragmented tools to analyze these distinct asset classes, leaving them with slow, expensive, and often opaque decision-making processes.

UZEmarkets solves this through **UZE Underwrite**, a dual-track, AI-driven underwriting engine powered by our **SURA** (Hospitality & Income) and **GIRA** (Agriculture, Natural Resources & Development) agents.

To prove the viability of this engine, we built our initial mock data infrastructure around the Mid-Atlantic market (Baltimore–Washington Metro). This data model was structurally verified by a practicing real estate financial analyst in that market, ensuring our AI generates institutional-grade metrics.

> **Status:** UZE Underwrite is BUILT — the engine, the P&L normalization, and the valuation metrics below are implemented in `services/compose` and covered by the test suite. The market data feeding the demo is a CoStar-shaped adapter returning synthetic figures, labelled synthetic in every payload; a commercial data license is pending (see the [Underwrite Spec](./specifications/underwrite/README.md)).

---

## Track 1: HiCRE (Hospitality & Income Commercial Real Estate)

**The Focus:** Built assets generating recurring income across both Hospitality and Non-Hospitality sectors.

For this track, the UZE engine is built to the interface of premier commercial data providers. It drills down to the micro-market level — understanding that Brickell is not "Miami," and Bethesda is not the "DC Metro."

What the engine verifies and analyzes:

- **Hospitality Assets:** Evaluates hotels, resorts, motels, and trailer parks. It benchmarks the asset against market Occupancy, ADR (Average Daily Rate), and RevPAR metrics.
- **Non-Hospitality Assets:** Analyzes residential rentals and residential condos (whether rented out or sold). It evaluates NOI (Net Operating Income), lease expiration schedules, and occupancy rates.
- **The P&L Normalization:** The engine ingests messy, multi-year T-12s and maps inconsistent line items into a strict seven-bucket taxonomy, isolating Taxes, Insurance, and Interest from Operating Expenses.
- **Valuation Metrics:** It goes beyond simple Cap Rates, computing the asking price against recent sales comps, specifically measuring Cost per Unit and Price per Square Foot.

---

## Track 2: ANRD (Agriculture, Natural Resources, & Development)

**The Focus:** The evaluation of agricultural land use — whether dormant or productive — subsurface resources, and development potential.

For the ANRD track, the UZE engine (GIRA) pivots from traditional financial operations to spatial, biological, and structural data.

> **Status:** The ANRD taxonomy (the HICRE | ANRD restructure of the earlier HIADR taxonomy) is ratified and lands in the claim model on Nov 15, 2026. The agriculture intake that exists today is evidence-gated by design: referrals are recorded and validated, provider status is held at UNVERIFIED until commercial agreements are signed, and no assessment, financing, or auction step executes without a human gate (see `docs/specifications/06-EVIDENCE-GATED-ARCHITECTURE.md`).

How the engine evaluates the land:

- **Agricultural Use (Active vs. Dormant):** GIRA analyzes the land for its agricultural viability, factoring in soil chemistry, climate data, and crop suitability to establish a baseline for its highest and best agricultural use.
- **Raw Acquisition & Development:** For undeveloped land banking or future development, GIRA evaluates the raw land cost basis against projected completed asset value, factoring in zoning and infrastructure constraints.
- **Natural Resources:** If the land holds subsurface value (minerals, water, etc.), the engine benchmarks the valuation based on extraction rights and local regulatory splits. Subterranean context — soil depth, resource types, water source and rights, jurisdiction — is mandatory for Agriculture, Development, and Resource claims.

---

Next: **[Part 2 — Core Autonomous Front End & Inference Economy](./02-inference-economy.md)**

---

# Part 2: Core Autonomous Front End & Inference Economy

## The Low-Friction Agentic Treasury

UZEmarkets is built natively on the NEAR protocol, utilizing its high-performance infrastructure to solve the critical bottleneck of AI compute funding. We provide a front end for everyone to optimize digital asset holdings for their chosen inference and compute.

> **Status — read this first.** The treasury surface is BUILT with explicitly mocked execution: the on-ramp, wallet, and routing interfaces are real, no real funds move through them, and no dummy credentials are ever configured — an unconfigured rail returns an honest error rather than a simulated success. Cross-chain swap *quotes* are live against the NEAR Intents 1Click API; swap *execution* is not performed. The one settlement that has executed on-chain to date is the Sprint 1.5 demo settle (Solana devnet, USDC), recorded in the submission materials.

- **Pre-Funded Pay-As-You-Go Inference:** Instead of relying on traditional credit cards or subscription models, entities and autonomous agents can pre-fund their compute with digital assets. The system is designed to route cross-chain capital so the most capital-efficient compute is always funded. Access is metered in code today: x402 pay-per-call for standard tiers, with x401 identity credentials required at higher tiers (see `services/compose/src/metering.py`).
- **Encrypted vs. Open Inference Routing:** Not all tasks require the same level of privacy or cost. Our routing design selects between:
  - **Encrypted, Private AI:** Frontier models executed with cryptographic attestation — NEAR AI Cloud inference runs in Trusted Execution Environments (TEEs) with verifiable response signatures; confidential computation beyond the TEE model is designed on Arcium's MPC network, which holds session keys across a multi-party network rather than in a CPU enclave.
  - **Open and Cheap Inference:** Low-cost, open-source models used for data scraping, OCR normalization, and non-sensitive background tasks.

> **Honest note on inference today:** the attested-inference code path is built and verified against the NEAR AI SDK surface. Live inference awaits funded inference credit on the NEAR AI Cloud organization; until a balance lands, the API returns the provider's real response rather than a fabricated result. We do not simulate attestation receipts.

### The treasury rails, as built

- **On-ramp:** Coinbase CDP on-ramp session route (adapted from a production codebase), with a fixed increment ladder ($5–$100 in $5 steps, $101–$250 in $10, $251–$1,750 in $50; amounts above the ladder are refused). Default settlement asset is Solana USDC; the wallet is self-custodial. Send & Receive only — there is no off-ramp.
- **Cross-chain swaps:** live quotes via the NEAR Intents 1Click API. Assets not in the 1Click registry are refused with the reason stated, rather than quoted fictionally.
- **Bridging:** Wormhole Connect with the CCTP route for supported chains (Solana, Base, Ethereum).

---

Next: **[Part 3 — UZE Assign, UZE Auction, & The Americas Roadmap](./03-assign-and-auctions.md)**

---

# Part 3: UZE Assign, UZE Auction, & The Americas Roadmap

## Monetization and Agricultural Yield

> **Status — read this first.** UZE Assign and UZE Auction are BUILT AS MOCK: the listing surfaces, sealed-bid mechanics, contribution receipts, and the Commitment Ladder are implemented and tested, with every payload labelled `mock: true`. There is no custody, no escrow of real funds, and no settlement in the current build, and no auction executes without an explicit human confirmation. The confidential-computation layer (Arcium MPC) is a filed design, not an integrated dependency. Details: [Assign Spec](./specifications/assign/README.md) · [Auction Spec](./specifications/auction/README.md).

- **UZE Assign (Monetizing Contracts):** Move off-market real estate contracts, bankruptcy estates, and raw land into sealed-bid assignment auctions. Listings carry a closed category vocabulary; bids are recorded expressions on an append-only audit log. The production design prices assignments through information markets (the Delphi protocol) and settles with cryptographic proof — that pricing and settlement layer is roadmap, not current code.
- **UZE Auction (Confidential Escrow):** The design uses Arcium MPC for confidential, fractional syndicate escrows. Entities pool capital against strict temporal commitment ladders — 30% by T-7 days, 90% by T-72 hours, 100% by T-12 hours — and a temporal trigger locks the escrow state when the pricing market closes. Execution is human-gated by design: the trigger readies an auction; a person executes it.
- **Increasing Crop Yield (The Brazil Test Market):** The ANRD engine is built to scale into South American markets. Our roadmap includes a test market in Brazil targeting the cattle rancher and feedlot supply chains — optimizing for birth-to-slaughter timing and maximizing feedlot yield harvest. We will integrate scientific soil research and crop yield optimization protocols to increase agricultural productivity before monetization. This is a roadmap item: the agriculture intake live today is the evidence-gated referral surface described in Part 1, and Brazil managed services begin only with signed scientific and commercial partners.
- **Grant & Award Funding:** We are actively pursuing strategic grant funding to accelerate the build-out of these agricultural managed services and scientific partnerships.

---

Back to the **[Documentation Hub](../README.md)**

---

# UZE Underwrite — Technical Specification

**Status: BUILT.** Implemented in `services/compose/src/` (`agents.py`, `chart_of_accounts.py`, `email_gateway.py`, `costar.py`, `juror.py`) and covered by the compose test suite.

## 1. Agents

- **SURA** — the Hospitality & Income (HiCRE) underwriting agent. Routes built, income-producing assets: hospitality (hotel, resort, motel, trailer park) and non-hospitality income (residential rental, residential condo).
- **GIRA** — the Agriculture, Natural Resources & Development (ANRD) agent. Routes land tracks: Agriculture Surface, Natural Resources (Water, Mineral, Rare Earth, Oil/Carbon), and Development Raw Land.
- Routing is by asset track at claim/judging time. (The HICRE | ANRD claim-model restructure is ratified and lands Nov 15, 2026; the HIADR addenda it restructures are filed at `docs/hackathon/nov-2026/07-HIADR-TAXONOMY-ADDENDA.md`.)

## 2. The seven-bucket P&L taxonomy

Every financial-performance claim is normalized into **exactly one** of seven buckets (`chart_of_accounts.py`):

1. Revenue
2. Operating Expenses
3. Taxes (local / state / federal)
4. Insurance(s)
5. Interest Expense / Income
6. Miscellaneous Net Expenses / Income
7. Profit (Net Income)

**Hard rule:** Operating Expenses never absorb Taxes, Insurance, or Interest. Raw, inconsistent T-12 line-item labels from operator financials are mapped into this taxonomy before any metric is computed; unmapped labels surface as review items rather than being silently absorbed.

## 3. Ingestion

- **Email gateway** (`email_gateway.py`): a T-12 sent to the published intake address is parsed into the fixture shape the underwriter consumes — units, square footage, revenue and expense lines — and normalized through §2. Worked fixture on record: $9,400,000 price · 128 units · 96,400 sqft · NOI $504,100 · cap rate 5.5% · price per unit $73,437.50.
- **Valuation metrics:** cap rate, NOI, cost per unit, and price per square foot, computed against sales comps for the asset's micro-region — never against a whole-metro average. Micro-region is the analytical unit throughout ("Brickell, not 'Miami'").

## 4. Market data — the CoStar-shaped adapter

**The standing line: "CoStar-shaped adapter, built to the interface, license pending."**

`costar.py` defines `ICoStarProvider` — the interface the underwriting flow consumes (sales comps; STR hospitality metrics: occupancy / ADR / RevPAR; market trends) — and a mock implementation returning **synthetic** Mid-Atlantic figures. Every payload is labelled `synthetic: true`, `provider: "costar-shaped-mock"`, with the license note attached.

UZEmarkets does **not** claim a CoStar integration. CoStar is enterprise-licensed; there is no license and no live connection. Synthetic figures are illustrative demo data and must never be presented as CoStar data. When a real license exists, a live provider implements the same protocol and the mock is retired; the underwriting flow does not change.

## 5. Judging

Normalized claims are judged by the Juror Team against **same-micro-region benchmarks only** — taxes are the largest driver of micro-market variability, which is why the taxonomy isolates them. Claims that pass resolution are the reliance-grade outputs financing partners consume via the Reliance API (see `docs/specifications/07-ASSURATIES-CLAIM-RESOLUTION-EXTENSION.md`).

---

# UZE Assign — Technical Specification

**Status: BUILT AS MOCK.** Implemented in `services/compose/src/assign.py` and `services/compose/src/contributions.py` (2026-11-11, on the owner's tap: "Build the Assign expansion + contribution receipts as mocks now"). Every payload carries `mock: true`. There is **no custody, no escrow, and no settlement** in this module.

## 1. Listings

- Router: `/api/v1/assign`.
- A listing carries exactly one category from a **closed vocabulary** — unknown categories are refused (422), and the set is extended only by a filed change:
  `REAL_ESTATE_CONTRACT` · `OPERATING_BUSINESS` · `DEFUNCT_BUSINESS` · `BANKRUPTCY_ESTATE` · `COLLECTIBLE_CARDS` · `FINE_ART` · `VEHICLES` · `ON_CHAIN_NFT` · `SECONDARY_TICKETS`
- Listings and bids live in an in-memory registry and are written to the append-only EventLog (`assign.listing_created` / `assign.bid_placed`) as the audit surface.
- A bid is a recorded expression of interest. Closing a listing is out of scope for the mock.

## 2. Contribution receipts (fractional syndicates)

`contributions.py` models syndicate participation in an assignment or auction:

- Escrow **pools** collect member contributions against a target.
- Receipts are issued in basis points and are constrained to sum to **exactly 10,000 bps** across a pool.
- True-up instructions reconcile a member's receipt share against final amounts.
- Receipts execute nothing: they are accounting records over a mock pool, not claims on held funds.

## 3. Scope note

UZE Assign is deliberately **not** part of the hackathon submission narrative (owner's scope ruling, 2026-11-10: the submission stays B2B agentic / RWA). Categories outside that narrative remain an internal build item until the owner rules otherwise.

## 4. Production design (roadmap)

The production assignment market prices contracts through information markets (the Delphi protocol) and settles executed assignments with cryptographic proof. Neither the pricing integration nor settlement is implemented in the current build; §1–§2 are the implemented surface.

---

# UZE Auction — Technical Specification

**Status: BUILT AS MOCK — no live MPC.** Implemented in `services/compose/src/auctions.py` and `services/compose/src/commitments.py` (2026-11-11, Directives 7 + 8 of the owner's scoped set). No Arcium MPC is integrated; the execute step is a mock reveal of the highest sealed bid. All state is in-memory (the persistent EntityPool schema is a deferred post-demo directive).

## 1. Sealed bids

Bid amounts are stored server-side and never appear in any response until a human-confirmed execution reveals the winner.

## 2. The Commitment Ladder

A syndicate auction's capital discipline: partners lock against their target bid on a schedule derived from the close time —

| Checkpoint | Lock required |
|---|---|
| T-7 days | 30% of target bid |
| T-72 hours | 90% of target bid |
| T-12 hours | 100% of target bid |

A partner under the due percentage at a checkpoint falls off the whitelist. Evaluation takes an explicit `now`, so the schedule is deterministic and testable.

## 3. The Temporal Trigger

When the pricing (Delphi) market closes, the trigger:

1. **Locks** the escrow state,
2. **Finalizes** the whitelist, and
3. Raises a **READY_TO_EXECUTE** alert.

The trigger does **not** start any auction execution. Execution requires `POST /execute` with `human_confirmed: true`; without it, the request is refused (422). This human gate is a design invariant, not a placeholder: confidential execution machinery does not remove it.

## 4. Confidential execution (design)

The production design executes the sealed-bid reveal inside Arcium's MPC network, so bid values are computed over without being exposed to any single party, including the operator. That integration is **design only** in the current build; §1–§3 describe what is implemented and tested today.
