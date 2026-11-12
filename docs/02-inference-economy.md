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
