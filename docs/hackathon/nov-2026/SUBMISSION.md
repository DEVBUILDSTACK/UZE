<!--
  DRAFT — Sprint 1.5 Day 7 deliverable, drafted early (Nov 8) per
  DeepSeek's unblocked-work directive. Bracketed [STATE] notes must
  be refreshed against the live build at filing (Nov 13-14) before
  this text is submitted anywhere.
-->

# UZEMARKETS — a multi-asset spatial finance engine (HIADR)

**An information market for real-estate work across five tracks —
Hospitality, Income, Agriculture, Development, Resource — where a
specification is priced competitively by human specialists and
attested AI agents, and settlement is authorized on NEAR and paid
in USDC on Solana.**

## The HIADR taxonomy

The marketplace is organized as five tracks (schema-enforced —
Addendum A, shipped in this sprint):

- **H — Hospitality & I — Income:** operating assets, evaluated by
  micro-region expense analysis (the demo's 340-room Aloft is
  Track H). A target area may be a 37.5-mile radius or a polygon.
- **A — Agriculture & D — Development:** raw land, evaluated by
  polygon spatial underwriting (soil, zoning, financing). A
  GeoJSON polygon is required — radius is invalid for land.
- **R — Resource:** subterranean assets, evaluated on subsurface
  rights and geology (water, minerals, oil/gas). Polygon required,
  plus a mandatory subterranean context: soil depth, resource
  types, water source and rights, and the jurisdiction that
  determines the legal split (e.g. Brazil's mineral regime). The
  subterranean context is mandatory across A, D and R — a data
  center cannot be underwritten without its cooling-water rights
  and bedrock data.

By design, each track routes to its capital: H/I to operating
lenders, A/D to land and development funds, R to resource
extraction financiers.

## The problem

Acquiring or operating an income property starts with analysis: an
operating budget, a property-manager specification, benchmarked
against the immediate surroundings. Today that work is slow,
opaque, and priced by relationship — a human analyst quotes weeks
and five figures, and the buyer has no competitive tension and no
verifiable provenance for the numbers.

## The micro-region thesis

Real estate value is local at a granularity the industry talks past:
not "Miami" but **Brickell**; not "DC metro" but **Bethesda**,
**Arlington**, **Northwest Baltimore**. UZEMARKETS makes the
micro-region the analytical unit. Every analyzed property, once
settled, is written back as a comparable in its micro-region
dataset — so the marketplace compounds: each engagement makes the
next benchmark in that neighborhood better.

## What it is

One marketplace, two service lines (the second feeds on the first):

1. **Assessment & Advisory** — a client posts a specification
   (property, micro-region, budget range, availability). Human
   specialists and AI agents bid competitively. The deliverable is
   an operating budget plus a property-manager specification,
   micro-region benchmarked and verifiably produced.
2. **Talent Placement** — the marketplace places the property
   manager / management company / operating talent against that
   specification. The advisory output is the hiring blueprint.

Two surfaces, one backend (a field on one surface and not the
other is a defect):

- **Agent surface** — a fully interactive JSON API.
- **Human surface** — read-only rendered HTML with schema.org
  JSON-LD, built for search and agent discovery (SEO/GEO).
  Interactive human UI lands in Sprint 2.

## How it works (the demo)

A syndicate acquiring a **340-room Aloft in Miami-Brickell** posts
its spec. A human CRE analyst bids **$22,500 / 60 days**. An AI
agent bids **$4,200 / 48 hours** — and its bid is not a promise: it
is backed by an executed NEAR AI Cloud inference (the spec rendered
to a prompt, analyzed inside an attested enclave), with the
attestation receipt attached to the bid and verified before
submission. The syndicate selects the agent. Settlement is
authorized by the NEAR contract and executed through **Chain
Signatures**: the MPC signer signs for a Solana address derived
from the NEAR account, and USDC moves on Solana devnet to the
winning bidder's derived address. At settlement, the analyzed
property is recorded as a comparable in the Brickell dataset.

Five phases: spec posted → bidding → selection → cross-chain
settlement → delivery + comparable written.

## The Assurative V2 Foundation vs. UZEmarkets

The stack separates trust from transactions:

- **Everything is an Entity** — the top of the hierarchy. Human
  partners within a syndicate are its **Affiliates**.
- **Assurative V2 (the Foundation)** is the trust layer: it handles
  entity-level authentication, human attestation, attribution, and
  provenance (for fractional rights and licensing). It is the
  system of record for who an Entity is and who gets credited.
- **UZEmarkets (the Marketplace)** sits on top of Assurative V2,
  consuming Entity/Affiliate identities. It handles the intents,
  bidding, and multi-party matching — its own transaction state
  machine, in its own database, carrying trust-layer references
  on every intent (`entityId`, `affiliateId`,
  `executionEnvironment`, `agentAttestation` — shipped in this
  sprint).
- **Execution (TEE / REE)** is powered by Arcium (sealed-bid
  auctions) or NEAR (intents and matching). An agent's identity is
  attested via **x401**: the agent acts on behalf of an Entity,
  and that attestation travels with its bids.

[STATE: a forensic audit of the Assurative V2 repo is filed at
docs/audit/assurative-v2-gap-analysis.md — the Entity/Affiliate
tables and the x401 verification path are the mapped trust-layer
build; the intent-side references and the x401 stub ship here.]

## Architecture

- **NEAR** — the intent, identity and agent-control plane: a Rust
  smart contract (`uzemarkets-talent.testnet`) holds intents, bids
  and settlement authorization; Chain Signatures (v1.signer) is the
  hinge that lets NEAR identities direct Solana addresses.
- **Solana** — settlement of record. USDC only; the marketplace
  never holds a Solana key — the MPC network signs for derived
  addresses (client-side Ed25519 derivation cross-verified against
  the contract's own `derived_public_key` view).
- **NEAR AI Cloud** — attested inference for agent bids: the
  analysis runs in a TEE enclave; completion id, verification
  result and parsed analysis are captured onto the bid. If
  inference is unavailable, the bid carries that honest state —
  never a fabricated receipt.
- **Assurative V2 compose core** — Python/FastAPI + PostgreSQL:
  specs, bids, matches, an append-only event log, and the Diagram 4
  intent lifecycle (POSTED → BIDDING → SELECTED → SETTLING →
  SETTLED → DELIVERED; SETTLE_FAILED is a resting state whose retry
  preserves the client's choice).
- **Metering stubs** — the x402 payment flow (402 → mock
  authorization → retry → proceeds, mock transfer logged as a mock)
  and the x401 identity stub for tier C+ engagements, ahead of
  Sprint 2's real facilitation and identity work.

## What was built in the hackathon window

[STATE — refresh at filing]

- NEAR contract scaffolded, deployed to testnet, and called
  end-to-end (post_intent / submit_bid / settle / get_matches).
- Marketplace schema (micro-regions, intents, bids, matches) as an
  additive migration with a from-empty replay; full API for specs
  and bids; 111 automated tests green.
- HIADR taxonomy extension (Addendum A): the AssetSubclass enum,
  radius/polygon target areas with track enforcement at ingestion,
  the subterranean context layer, and micro-region pulse data —
  additive migration `851420c2adc4`, from-empty replay verified
  (schema demo 12/12), plus the Content Desk's `/pulse` endpoint
  serving schema.org Dataset JSON computed from real records.
- Trust-layer linkage: Intent carries the Assurative V2 references
  (`entityId`, `affiliateId`, `executionEnvironment`,
  `agentAttestation`) as an additive migration (`4efec7ad31a2`),
  and a forensic gap analysis of the Assurative V2 repo is filed
  (docs/audit/) mapping the Entity/Affiliate build the references
  resolve against. Suite at the Day 7 draft refresh: 115 tests.
- Chain Signatures proven end-to-end (MPC signature verified under
  the derived key); the mocked-settlement fallback was retired.
- Settlement endpoint: selection, match state machine, the exact
  devnet USDC transfer built and MPC-signed. [STATE: dry runs rest
  at SELECTED + signed pending devnet funding of the payer address;
  the broadcast fires on funding — update with the Solana tx hash
  once executed.]
- NEAR AI inference module integrated against the real SDK, with
  attestation capture on agent bids. [STATE: live attested run
  pending NEARAI_API_KEY provisioning (Day 4) — update with the
  completion id + verification kind once run.]
- x402/x401 mock flow with an agent retry helper and a dry-run
  script proving the protocol end-to-end.
- Read-only human surface: spec, talent and micro-region pages
  with JSON-LD, indexes, sitemap, robots and llms.txt — verified
  rendering against the live API.

## The HIADR Content Desk — the organic growth engine

Distribution is built into the data layer. Every micro-region
carries a pulse: period aggregates (30/90-day, 18/36-month
lookbacks) served as a schema.org Dataset at
`GET /api/v1/micro-regions/{id}/pulse` — computed from the
marketplace's own specs, settled comparables and volume.

The Desk publishes on a fixed cadence: a **daily** micro-region
pulse (7×/week), a **Sunday** deep-dive spatial analysis (e.g.
aquifer depletion inside a specific agricultural polygon), and a
**Tuesday** X thread distilling the blog. Every post is
dual-surface by construction: a human-readable analysis on top,
the machine-readable JSON payload at the bottom. When an AI
crawler ingests the post it doesn't just read text — it receives
the exact endpoints (`agent_action: POST /api/v1/specs`) to
transact. That is the GEO (Generative Engine Optimization) play:
the content is the API's discovery layer, for humans and agents
alike. [STATE: the data layer — pulse storage + the /pulse
endpoint — ships in this sprint; the publishing Desk runs on it
next, per the filed sequence.]

## What's next

Sprint 2 (already filed): interactive human UI, real x402
facilitation, the redemption writer, Intent Gateway and Tag
Registry, solver policy with pre-settlement screening — the filed
series continues exactly as planned; the hackathon is a bounded
pull-forward (Sprint 1.5), not a fork.

## Submission fields

- **Repository:** https://github.com/DEVBUILDSTACK/UZE (public;
  branch `hackathon/nov-2026`, merges to main Nov 13)
- **Contract:** `uzemarkets-talent.testnet` (NEAR testnet)
- **Demo video:** [LINK — 3–5 min recording, script in DEMO-SCRIPT.md]
- **X demo post:** [JAMES — post URL]
- **Team lead email:** [JAMES — email]
- **NEAR payout address:** [JAMES — address]
