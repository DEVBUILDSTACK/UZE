# MCP Descriptive Language v0.1 — the exact language for the MCPs we use

**Status: DRAFT for James's review, 2026-11-18.** Written on James's directive of 22:12 ET: the exact, highly descriptive language comes FIRST — focused purposely on **UZE Underwrite** and **Talent matching** — in advance of the NEAR AI Cloud credits settlement. This language feeds three surfaces, identically: the directory listings (the listings to-do sheet), the site's MCP Tooling & Directories section above the footer, and the Knowledge Base MCP detail. One language, three surfaces — no surface invents its own wording.
**Addressee:** James.

**Authenticity rule (James, 2026-11-18):** every description states what the MCP does and its true status. Nothing here claims a live public endpoint, a live directory listing, or a capability that is not built. Where a tool set is design rather than built, it is labelled design.

---

## 1. UZE Underwrite — the lead product MCP

**Short description (directory one-liner):**
UZE Underwrite — the Autonomous Underwriting desk as an MCP. Submit a Hospitality or Income property with its operating financials and receive an underwriting read benchmarked against its own micro-region: every claim checked, every number in its proper bucket, nothing taken on faith.

**Long description:**
UZE Underwrite is the MCP face of the UZEmarkets Autonomous Underwriting desk — one of the three matching desks that make up UZEmarkets superIntelligence. It underwrites Hospitality and Income real estate (the H and I of the HIADR asset taxonomy) inside defined micro-regions.

Financial claims arrive as **Assuraties** — claims a seller or advisor stands behind — and are tested before they are relied on. Performance is read in exactly seven buckets, never blended: **Revenue; Operating Expenses; Taxes; Insurance(s); Interest Expense/Income; Miscellaneous Net Expenses/Income; Profit (Net Income)**. Operating Expenses never absorb Taxes, Insurance, or Interest. Judgement is made only against benchmarks from the **same micro-region**, because taxes — the largest driver of micro-market variability — make cross-region comparison meaningless. Claims that survive the process are **Assuratized**: reliance-grade, with the evidence trail attached.

**Who it serves:** lenders, buyers, and financing partners who need an underwriting read they can rely on, and sellers whose financials are strong enough to be proven rather than pitched.

**Status:** the underwriting desk is in build on the AssurativeV2 core; the MCP ships as a product MCP with the Markets tier. Product MCPs (Underwrite · Assign · Auction) are a separate family from the trading MCPs (TradeLayer · SigLayer) and are never blended with them.

**Tool set:** design — underwriting submission, benchmark read, claim check, reliance report. (The built catalog of record today is the UZE Instant MCP's, §4.)

---

## 2. Talent matching — the Talent MCP

**Short description (directory one-liner):**
Talent matching — Role × Realm matching with assessment proof. Configure the role you need; the desk matches on role and realm, proves fit through a two-gate assessment, and keeps every candidate blind until engagement and deposit.

**Long description:**
Talent matching is the MCP face of the UZE Talent desk. A role is configured once, as a keyed record in the **Role × Realm taxonomy** — 11 roles across 6 realms of expertise, up to five Role×Realm pairs per professional, ranked primary to quinary. The desk matches against that taxonomy; it does not keyword-search résumés.

Fit is **proven, not asserted**. From the role, the system generates a skills assessment from a curated template library — generation is slot-filling against calibrated templates, never free invention. Two human gates stand before anything runs: **Gate 1**, the engaging employer's confirmation of intent, and **Gate 2**, an approver of record's confirmation that the assessment is valid for the vertical. An agent identity can satisfy neither gate. Runs are scored at a scoring center — an AI grade with a human-review flag against a stated threshold — and results are published **redacted and pseudonymous**: no talent names, no emails, no company names, ever, until the moment identity is earned.

Engagement runs on two money models. **Outstaffing:** UZE Markets pays the talent and bills the client. **Placement:** UZE places for a fee of at least one month (30 days) of salary, and the client pays the individual directly. Under the confidentiality doctrine, a talent target is never exposed — no identity, no contact information — until **both** a signed engagement **and** a deposit are in hand. Until then, talent is presented blind, through the desk alone.

**The three tools (built, live in the UZE Instant MCP tonight):**
- `submit_assessment` — submit a role configuration and generate its assessment.
- `score_assessment` — score a run against the assessment's threshold.
- `publish_assessment_outcome` — publish the outcome, redacted, under an engagement-scoped pseudonym.

**Status:** the Talent system of record is built and live (the UZE Dev Library is its developer instance); the three tools activated on the first assessment outcome published under the two gates. Production Gate 2 opens per vertical as approvers of record are named.

---

## 3. The rest of the family — same language discipline, shorter form

**UZE Assign** (product MCP — the DealFi matching desk): DealFi matching as an MCP — a deal or position is described once, and the desk assigns it to the matched counterparty on the other side of the market. Status: desk in build; brings online first among the desks (DealFi before Fundio, per the standing order).

**UZE Auction** (product MCP): sealed-bid auctions for the secondary market — bids sealed under Arcium MPC on Solana, matched by solvers, cleared at a uniform price. Primary sales are never auctioned: primary is fixed price plus allocation. Status: design of record; the auction surface builds on the Solana + Arcium topology.

**Brokerage MCP** (the TradeLayer door): connect your AI to your brokerage accounts — it reads every account and trades only where you fence it in: a dedicated, separately funded MCP account, every order reviewed before it executes. Built on the Robinhood model — Robinhood-custody crypto is Robinhood's, labelled as theirs. Status: API in build; the Directory page's panel states its live status and governs.

**TradeLayer MCP** (trading MCP): the trading surface for the information markets — launches with the Brokerage MCP door in front of it. Status: in build behind the brokerage door.

**SigLayer MCP** (trading MCP): the full production trading layer — treasury, signing, and settlement discipline — which follows once TradeLayer works. Status: design of record, sequenced after TradeLayer.

---

## 4. UZE Instant MCP — the platform MCP (catalog of record, built)

**Short description:**
UZE Instant MCP — one endpoint for UZE compute and markets. Provision a UZE Instance, meter it, terminate it — every call inside limits you set in advance, every call on the record.

**Long description:**
The UZE Instant MCP is the single MCP endpoint (mcp.uzemarkets.com) for the UZE Instant platform, in two tiers. **UZE Instance** is the generic tier: branded NEAR AI Cloud compute plus settlement, nine base tools, no vertical access. **UZE Markets Instance** is the premium tier: the base tools plus the vertical pathways — TradeLayer, SigLayer, Arcium, and the Talent tools of §2.

Access is gated in three layers: the **pre-authorization limits you set** (per-call and per-day ceilings, an optional tool allowlist), **MCP enforcement** of those limits before any call executes, and the **vertical gates** behind each tool. Sign-in is wallet-bound — your wallet signature is your credential. Every call, grant, and refusal is written to an append-only chronicle; revocation cascades at the call boundary — sessions die, later calls refuse, an in-flight call completes. Settlement follows the rail law: **USDC on Solana is the default for everything**, cascading to USDC on Base, then USDG on Robinhood Chain; Tempo/Stripe CASH only where a vertical requires it.

**Catalog of record (18 tools):** base — provision_instance, get_credentials, terminate_instance, get_status, list_tiers, query_balance, pay_via_x402 (live); create_escrow, release_milestone (arrive with the settlement phase). Vertical — the nine Markets-tier tools, including the three Talent tools of §2.

**Status:** built and proven (gating, limits, and revoke cascade demonstrated); the public endpoint opens with the January 2, 2027 launch. No spin-up time is claimed until provisioning is measured.

---

## 5. The directories this language is written for

Anthropic (Claude) · OpenAI · Microsoft Copilot · Google (Duet / Gemini) · Meta (Muse) · Perplexity · Venice AI · DeepSeek · Kimi — tracked, with listing routes and statuses, in the MCP Directory Listings to-do sheet. The order of work follows the filed two-tier structure: the Anthropic MCP registry first (conversion), the reach tier after; listings claim only compatibility that is verified when the claim is made.
