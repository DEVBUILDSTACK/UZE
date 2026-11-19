# Scope 3 — UZE Instant MCP: Scope and Phased Specification v0.1

**Status: FOR JAMES'S TAP.** Filed 2026-11-18 by SoSem.
**Source:** DeepSeek, "Productization — UZE Instant MCP and the tier split" (2026-11-18), relayed by James and filed as received at `docs/instant-mcp/DEEPSEEK-PRODUCTIZATION-UZE-INSTANT-MCP-2026-11-18.md`.
**Addressee:** James. This document is the scope + phased specification for the third scope line (after Scope 1 — Talent/Dev Library, Scope 2 — P2 Assessment). Nothing in it builds until James taps it. DeepSeek's text is design input; where it conflicts with James's standing rulings of record, the rulings govern and the conflict is flagged in §9 rather than silently adopted.

---

## 0. The product, in one paragraph

The MCP is the product; the VPS is the resource it provisions; the AI directories are the distribution channel. One endpoint — **UZE Instant MCP** (`mcp.uzemarkets.com`) — sells two tiers of provisioned instance. The tier determines which tools a caller's agent may invoke. Margin sits on the tool call and on vertical access, not on the CPU-hour. The MCP is an **interface layer over the existing cores** (NEAR AI Cloud, TradeLayer, SigLayer, the Talent marketplace) — it is not a fourth core, per Scope Tenet 01.

## 1. Naming (subject to Open Item 1)

| Name | Job |
|---|---|
| **UZE Instant** | The platform brand. Provisioning claim + discovery posture. |
| **UZE Instance** | The generic SKU: branded NEAR AI Cloud compute + settlement, no vertical access. |
| **UZE Markets Instance** | The premium SKU: everything in UZE Instance + TradeLayer, SigLayer, and Arcium pathways. |
| **UZE Instant MCP** | The single MCP server endpoint both tiers connect through. |

## 2. The tiers

**UZE Instance — compute + settlement, generic.** Branded NEAR AI Cloud KVM (KVM1/2/3). Settlement via NEAR Intents and x402 agentic payment. No vertical access. Margin profile: infrastructure margin (NEAR cost + branded markup), predictable and capped.

**UZE Markets Instance — compute + settlement + vertical integration.** Everything above, plus: TradeLayer open/close positions across the prediction-market / ticket / talent marketplace stack (AEInfo, P2 auction, sealed-bid secondary); SigLayer attestation signing, dispute resolutions, credential operations; the Arcium MPC pathway for sealed-bid operations. Margin profile: infrastructure margin + vertical access premium, the premium being a share of transaction value on surfaces where UZE is operator of record.

## 3. Tool catalog (15 named tools; tier-gated)

**Core — both tiers (5):** `provision_instance(tier, spec)` · `get_credentials(instance_id)` · `terminate_instance(instance_id)` · `get_status(instance_id)` · `list_tiers()`

**Settlement — both tiers (4):** `create_escrow(engagement, amount, rail)` · `release_milestone(escrow, milestone)` · `query_balance(wallet)` · `pay_via_x402(amount, currency)`

**Vertical — Markets tier only (6):** `sealed_bid_assignment(role, bid)` via Arcium MPC · `open_position(market, side, amount)` via TradeLayer · `close_position(position_id)` via TradeLayer · `sign_attestation(claim, tier)` via SigLayer · `open_dispute(engagement, reason)` via SigLayer · `publish_redacted(engagement_id)` via the IPFS publication layer (§9, D6)

Instance tier = 9 tools (Core + Settlement). Markets tier = 15 tools. (DeepSeek's gating diagram states 8 and 14 — an arithmetic discrepancy in the source, flagged as D7 in §9; the enumerated catalog governs.) Sealed-bid tools operate on **secondary / assignment markets only**, per the standing AEInfo doctrine (primary = fixed price + allocation).

## 4. Gating and security — non-negotiable

1. **User pre-authorization.** At provisioning, the user authorizes their agent with explicit limits: per-call max, per-day cumulative max, and an allowed tool set (e.g., `open_position` disabled, `sign_attestation` enabled). Limit changes require re-authentication.
2. **MCP-side enforcement.** Calls exceeding limits are refused **before** execution. Every refusal is logged as a chronicle Event.
3. **Vertical-side safety.** The MCP never bypasses a vertical's own gates — TradeLayer position caps, market availability, jurisdiction checks; SigLayer record-state checks; Arcium sealed-bid conditions.

The user is the customer, not the agent. The agent is the caller; the user's wallet pays and is what the MCP meters against. An agent can never draw beyond the wallet's authorized limits.

**Isolation.** Cross-user isolation is absolute, enforced at the routing layer before any tool runs. Two agents of the same user share no state unless the user explicitly enables it.

**Revocation cascade.** Disable agent / terminate instance / revoke tool → effective at the next MCP call boundary; the in-flight call completes, subsequent calls are refused. Same pattern as the Talent revoke cascade.

## 5. Settlement and rails — conformed to the rail law of record

Settlement follows James's rail law (2026-11-18): **USDC on Solana is the default for everything**; cascade USDC Base → USDG Robinhood Chain → Tempo/Stripe CASH only where none of the first three is available (and never inside SigLayer/TradeLayer). NEAR Intents and x402 are the agentic payment mechanics; the NEAR staking discount from the P2 access model applies to both tiers. See Deviation D1 in §9: DeepSeek's architecture diagram frames the user wallet as "Base USDC wallet + NEAR Intents as base" — this specification conforms the default to Solana per the law of record and flags the difference for James's ruling rather than adopting Base-first silently.

## 6. Directory and discovery strategy

One endpoint, listed across the AI directories; uniform listing content (tool catalog, 30-second demo, both tiers' pricing posture, the one-page "what this is"). No underlying-infrastructure brands named beyond compliance requirements. DeepSeek's proposed priority: Anthropic registry → Smithery → OpenAI → Hostinger → mcp.so / mcpmarket → Cursor / Windsurf, with own-docs/direct-config in parallel from day one. See Deviation D2 in §9: James's standing record names the major LLM directories as Anthropic/Claude, OpenAI, Perplexity, Venice, DeepSeek, and Kimi — the listing plan must reconcile both lists under James's ruling (Open Item 2).

## 7. Pricing posture (parameters, not public prices)

| Component | UZE Instance | UZE Markets Instance |
|---|---|---|
| Provisioning | Free | Free |
| Compute | Per vCPU-hour, NEAR underlying + ~20–30% branded margin | Same base |
| Metering | Per tool call, x402, standard rate | Per tool call, x402, standard rate |
| Vertical access | — | Premium rate per call; TradeLayer trades as a share of notional (Open Item 4) |
| NEAR staking discount | Available (per P2 access model) | Available (per P2 access model) |

The premium is per-call / per-transaction, never a subscription. Consistent with house practice, no static prices are published in public copy; the figures above are internal parameters for James's ruling.

## 8. Phased plan

**P0 — Verification and foundations (no product claims leave this phase).**
Verify NEAR AI Cloud provisioning reality end-to-end (API surface, KVM tiers, actual spin-up time — the "under 30 seconds" claim is a **target to be measured**, not a filed fact); resolve the NEAR AI Cloud credits blocker (live inference currently blocked at a $0 org balance — provisioning economics cannot be stated until credits and pricing are confirmed); MCP protocol conformance spike against the Claude reference implementation; tenet-conformance note (interface layer over existing cores).

**P1 — Core MCP + Instance tier.** The endpoint at `mcp.uzemarkets.com`; wallet-bound auth; the 9 Core + Settlement tools; x402 metering; every call a chronicle Event; pre-authorization limits and MCP-side enforcement; revoke cascade.

**P2 — Markets tier vertical tools.** The 6 vertical tools behind the three-layer gating; Arcium sealed-bid pathway; TradeLayer/SigLayer execution strictly inside the verticals' own gates. `publish_redacted` rides on the P2 Assessment publication layer (IPFS) and its pinning-home ruling. Depends on: P2 Assessment tap, TradeLayer/SigLayer surfaces as built.

**P3 — Directory listings.** In the priority order James rules under Open Item 2; uniform listing content; own-docs route live from P1.

**P4 — Compatibility matrix + hardening.** Per-client testing (Claude reference; OpenAI function-call parity; Gemini parameter encoding; popular open-source MCP clients). A compatibility claim is made only for a green cell — no claims without evidence. Tenant-isolation and limit-enforcement adversarial pass.

Each phase starts on its own tap, per the standing cadence.

## 9. Verification notes and deviations (SoSem's pass on the source document)

- **D1 — Rail default.** DeepSeek's diagram and §2 frame provisioning "against their Base wallet," with NEAR Intents "as base." James's rail law of record (2026-11-18) makes **USDC on Solana the default for everything**, Base second. §5 conforms to the law. If James wants this product Base-first as a deliberate exception, that is his ruling to make — flagged, not adopted.
- **D2 — Directory list.** DeepSeek's list (Anthropic, OpenAI, Smithery, mcp.so/mcpmarket, Hostinger, Cursor/Windsurf) and James's standing list (Anthropic/Claude, OpenAI, Perplexity, Venice, DeepSeek, Kimi) overlap only at Anthropic + OpenAI. The union is plausible — registries vs LLM directories are different shelves — but priority and completeness need James's ruling (Open Item 2).
- **D3 — NEAR AI Cloud credits blocker.** The Instance tier's underlying compute is NEAR AI Cloud; live NEAR AI inference is currently blocked on org credits ($0.00 balance, HTTP 402 on use). P0 carries the resolution; no provisioning or pricing claim is made before it clears.
- **D4 — "Under 30 seconds."** DeepSeek's provisioning claim is unverified. It is carried in this specification as a P0 measurement target. It appears in no listing copy until measured.
- **D5 — Access regime boundary.** The standing NoGate rule (identity = agent's email; credential = wallet payment signature; no KYC/KYB for base builders) governs the base tier naturally. The P2 Assessment access model adds KYC/KYB for configuring employers. Which regime governs Markets-tier provisioning — where the caller can move money on the verticals — is stated here as: NoGate for provisioning + the §4 pre-authorization limits for tool access, with vertical-side gates unchanged. Flagged for James's confirmation (Open Item 5).
- **D6 — "[BRAND] IPFS."** DeepSeek's placeholder for the publication layer is the same IPFS-based publication the P2 Assessment specification already carries (NEAR AI Cloud the named reference home; hard redaction — no names, emails, or company names). The brand name and the pinning home ride on the P2 open item; Scope 3 does not fork that decision.
- **D7 — Tool-count arithmetic.** DeepSeek's catalog enumerates 5 Core + 4 Settlement + 6 Vertical = 15 tools, but its gating diagram labels the tiers "(8 tools)" and "(14 tools)". The enumerated catalog is taken as governing in §3; the counts in the diagram are the source's error, noted here rather than propagated.

## 10. Open items for James's ruling (unbundled; each stands alone)

1. **Tier naming** — "UZE Instance" / "UZE Markets Instance" as SKUs, "UZE Instant" as umbrella, "UZE Instant MCP" as endpoint. (DeepSeek item 1.)
2. **Directory priority + list reconciliation** — DeepSeek recommends Anthropic → Smithery → OpenAI; James's standing list adds Perplexity, Venice, DeepSeek, Kimi. (DeepSeek item 2 + Deviation D2.)
3. **publish_redacted tier scope** — Markets-tier only (DeepSeek's read), or also Instance tier? (DeepSeek item 3.)
4. **Premium rate structure** — DeepSeek recommends percentage-of-notional for `open_position`/`close_position`, per-call for `sign_attestation` / `open_dispute` / `sealed_bid_assignment`. (DeepSeek item 4.)
5. **Access regime for the Markets tier** — NoGate provisioning + §4 limits, as drafted in D5, or the P2 KYC/KYB regime extended to Markets-tier provisioning?

## 11. Invariants carried

Every tool call — executed, refused, or revoked — is a chronicle Event. Status is derived, never written. The revoke cascade is atomic at the call boundary. Redaction is by construction on anything published. The DeepSeek information boundary holds (accounts by label only in any external material). James's gates bind all money movement: the §4 limits are user-set, and nothing in this scope authorizes any spend, listing, or publication without the applicable tap. Filed records govern over summaries of them.

---

*Prepared by SoSem, 2026-11-18. On James's tap, the build decomposes per §8, one phase at a time.*

---

## Amendment — Composite ingestion, 2026-11-18 (DeepSeek feedback #1; by addition, v0.1 above unchanged)

DeepSeek's composite feedback (`docs/talent/DEEPSEEK-COMPOSITE-FEEDBACK-2026-11-18.md`, filed on the Talent line per James's direction — the scopes stand separated; this amendment carries only what touches Scope 3) was diagnosed the same day; the diagnosis of record is `docs/talent/DIAGNOSIS-COMPOSITE-FEEDBACK-2026-11-18.md`. On James's tap, this specification is read **as amended by the following**:

1. **The Talent/P2 vertical joins the Markets tier.** The Markets tier serves three vertical families: TradeLayer, SigLayer, and the **Talent layer (P2 Assessment)**. The vertical catalog grows by three tools: `submit_assessment(role_config)`, `score_assessment(talent_did, assessment_id)`, and `publish_assessment_outcome(assessment_id)` — the last being `publish_redacted` wired to the assessment engagement. Enumerated catalog: 9 base + 9 vertical = **18 tools** (the composite's "8 / 17" labels repeat the standalone's undercount; flag D7 stands, diagnosis X1).
2. **D1 RESOLVED.** The composite's rails layer names **USDC Solana as the default rail**, conforming to the rail law of record. §5's conformance is now the source's own position; no exception is needed.
3. **Publication layer named.** `publish_redacted` publishes to **UZE-IPFS** (real IPFS on NEAR Cloud) as the recommended home — shared with the P2 package, ruling 7; the capability claim is unverified and is a P0 verification item (diagnosis X2). A NEAR Cloud bucket is never to be labeled IPFS.
4. **Gating extended.** §4's layer 3 (vertical safety) explicitly includes P2's **two-gate human approval**; both gates are console-only and human-signed on every surface.
5. **Dual-surface contract adopted.** The console is a view over the API, never a parallel path; autonomous-first for money/execution, human-first for judgment.
6. **Open items consolidated.** §10's five items are superseded by the composite's **seven rulings** (diagnosis §7): rulings 1–4 are this scope's; rulings 5–7 ride with the P2 package. Flags **D2** (directory list reconciliation) and **D4** ("<30 seconds" unverified) stand unchanged.

**Outcome note (2026-11-18, by addition).** DeepSeek's response to the diagnosis (`docs/talent/DEEPSEEK-RESPONSE-DIAGNOSIS-FIXES-2026-11-18.md`) closes or settles the flags as follows. **Tool count (D7/X1): CLOSED** — no tool struck; the catalog is **9 base + 9 vertical = 18** (Instance 9, Markets 18), labels corrected. **Directory list (D2/X4):** the recommendation of record is now a **two-tier structure** — Tier 1 (conversion): Anthropic MCP registry → Smithery → Cursor/Windsurf; Tier 2 (reach): OpenAI → Perplexity → DeepSeek → Venice → Kimi → Hostinger → mcp.so/mcpmarket — James's standing list fully included; ruling 2 remains James's. **"<30 seconds" (D4/X5):** withheld from every surface until P0 measures actual provisioning time; "Instant" remains a brand word only. **P0 gains** the four-point IPFS verification checklist and the NEAR AI Cloud credits condition (diagnosis outcome, X2): Filebase/Pinata is the operating pinning home; UZE-IPFS is the conditional target state.
