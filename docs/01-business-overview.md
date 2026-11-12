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
