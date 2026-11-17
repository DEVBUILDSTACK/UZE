# MCP Utility — Spec v0.1 (2026-11-16)

Status: FILED on James's tap (2026-11-16 20:50–20:55 ET). Docs + dynamic
mock-up build. No live brokerage, no real money, no live trading — the
mock-up runs on labelled demo data and simulated orders only.

Source brief: `~/workspace/research_notes/UZEMARKETS-MCP-UTILITY-BRIEF-2026-11-16.md`
(James's email 2026-11-16 10:06 ET pasting Robinhood's "Onboarding an
external agent" article; article verified live the same day).

## 1. What this is

A UZEmarkets MCP utility modelled on the Robinhood brokerage agent
model, for the TradeLayer and SigLayer surfaces:

- An external AI agent (the user's own LLM — Claude, ChatGPT/OpenAI,
  Codex, Cursor, Grok, Perplexity, and the rest of the cast) connects to
  the surface over one MCP link.
- The agent gets READ access to accounts, positions, balances, and
  transaction/order history.
- The agent can place TradFi orders ONLY inside a dedicated,
  separately funded MCP account. Every other account is read-only to
  the agent. This caps what the agent can touch and isolates its P&L.
- Review before action: an order is first returned as a REVIEW preview;
  it executes only on an explicit confirm step. There is no
  act-without-asking mode in this build — money stays behind the user's
  explicit confirmation (James's standing gate through Dec 2026).

## 2. The custody differentiation (James's ruling, 2026-11-16)

- TradFi through this door is the brokerage model — custodial, inside
  the brokerage account.
- Crypto is NOT the brokerage door's product. Any crypto visible through
  a brokerage surface is brokerage-custody crypto and is never presented
  as the UZE crypto solution.
- UZE crypto is purely permissionless self-custody (TradeLayer /
  SigLayer, Arbitrum Orbit L2 — Robinhood Chain — and UZE's own rails).
- UZE extends beyond the brokerage catalogue: users who want a greater,
  more extensive DeFi experience can acquire earlier-stage tokens the
  brokerage does not offer, in their own custody, on their own
  election — buyer beware. The disclosure states this plainly.
- **Eligibility (James, 2026-11-16 21:47 ET):** the UZE self-custody
  extension is offered **only to experienced DeFi traders — more than
  5 consecutive years trading permissionless, non-custodial DeFi
  markets.** The rule is carried in the spec, the API payloads, the
  disclosure, and the site copy wherever the extension is described.
- **Product name (James, spelled out 2026-11-16 22:01 ET):** the
  offering is **UZE TradFi Complex & Agentic DeFi** — UZE (U-Z-E),
  TradFi (capital T, capital F), Complex (capital C), ampersand,
  Agentic DeFi. It is not only a self-custody extension: it is the
  TradFi complex (the Robinhood brokerage door) and its agentic DeFi
  side (the self-custody extension) under one name. The directory
  entry on the site carries this name, with Robinhood Crypto kept
  separate.

## 3. Build order (James, 2026-11-16)

1. **The Robinhood-model MCP first** — this spec and its mock-up.
2. TradeLayer and SigLayer permissionless DeFi surfaces after.

## 4. Pairings board (James, 2026-11-16)

Priority three chains: **Robinhood, Solana, Ink**.

- Paired tokens across Robinhood ↔ Solana, including xStocks
  (tokenized equities on Solana).
- Robinhood Chain pairings.
- Equity pairings and yield pairings on Ink Chain.
- The other previously specified chains (NEAR, Base, LightLink, …)
  follow after the priority three.

The pairings board in the mock-up is a labelled roadmap surface: pairs
are displayed with their route and status; no pairing is live in this
build.

## 5. Tool surface (this build)

JSON-RPC 2.0 MCP endpoint, same protocol shape as the existing
`POST /api/v1/mcp` surface:

- `POST /api/v1/mcp-brokerage` — methods: initialize, ping, tools/list,
  tools/call.
- `GET /api/v1/mcp-brokerage/connect` — the connect-your-LLM payload:
  the MCP link, supported clients, the dedicated-account rule, and the
  disclosure text.

Tools:

| Tool | Kind | Rule |
|---|---|---|
| `Brokerage_List_Accounts` | read | all accounts; flags the dedicated MCP account |
| `Brokerage_Get_Positions` | read | positions + cash for one account |
| `Brokerage_Get_Transactions` | read | order/transaction history for one account |
| `Brokerage_Get_Quote` | read | TradFi symbols only; crypto symbols are refused with the differentiation payload |
| `Brokerage_Place_Order` | trade (simulated) | dedicated MCP account only; TradFi only; no-confirm call returns a REVIEW preview, confirm executes against the demo book |
| `UZE_Self_Custody_Route` | info | the differentiation: self-custody route, earlier-stage tokens, buyer beware |

Demo data is synthetic and labelled `demo: true` in every payload.
Demo state is in-memory and resets on restart; no database migration
is introduced by this build.

## 6. Disclosure (adapted substance, draft — not legal advice)

Modelled on Robinhood's published agentic-trading disclosure:
agentic trading can lose the entire investment; agents can err,
misinterpret, or act on incomplete or outdated information; the
provider does not guarantee agent output and is not responsible for
agent-generated losses; the user assumes all risk for agent trades and
for third-party AI providers' use of their data. UZE additions:
earlier-stage tokens acquired through the self-custody extension are
higher-risk and are the user's own election (buyer beware); UZE crypto
is self-custodial — the user holds their own keys and bears custody
risk.

## 7. Hard constraints carried from the brief

- Money stays gated by James through Dec 2026; the only autonomous
  trading authority on file is the $100 XSigLayer envelope expiring
  Jan 2, 2027 (granted, pending activation; not used by this build).
- Robinhood Chain (Arbitrum Orbit L2, chain 4663) is not Robinhood the
  brokerage; the two are never conflated in copy or code naming.
- Scope Tenet 01: this utility serves the TradeLayer and SigLayer
  surfaces on the one shared core; it is not filed twice.
- Public-copy rule: client-facing pages do not name technology
  partners; partner-named detail belongs on the DevPartner surface.
  (This spec is an internal document; the mock-up page is a demo
  surface and labels its model as a design reference, not a partner
  claim.)
- Verification rule (Exa lesson, Nov 13): no MCP surface is claimed to
  work until it is exercised end-to-end in the running system.

## 8. Separate MCPs, separate listings (James, 2026-11-16 20:56 ET, corrected 20:58 ET)

Two unrelated MCP groupings exist, and they are never blended —
James's correction is explicit: the TradeLayer / SigLayer trading
MCPs have **nothing to do at all** with UZE Underwrite, Assign, and
Auction.

- **Product MCPs** — segmented and listed as **UZE Underwrite |
  UZE Assign | UZE Auction** (§9). UZE Underwrite is live now as the
  `UZE_Underwrite` tool on `POST /api/v1/mcp` (with
  `UZE_Research_Query`); Assign and Auction are added as they come in.
- **Trading MCPs** — TradeLayer and SigLayer (§9). This build is the
  brokerage door TradeLayer launches with.

Discovery rule (James): MCPs are not found unless they are listed as
connectors in the directories of the LLM companies themselves. Each
MCP is therefore listed separately, as its own connector — prepared
submissions, each gated on James's own tap, none submitted by this
build — in:

- Anthropic (Claude connectors directory)
- OpenAI (ChatGPT)
- Perplexity
- Venice
- DeepSeek
- Kimi
- …and the other major LLM platforms, alongside the registry
  directories already in the 2026-11-13 listing packet (Official MCP
  Registry, Smithery, Glama, PulseMCP, mcp.so).

Each directory's current submission requirements and
ownership-verification method are checked at submission time; a
prepared packet is never represented as a live listing. The
2026-11-13 packet is extended per MCP when the listings run.

## 9. Segmentation and launch sequence (James, 2026-11-16 20:58 ET)

Two segmentations, kept apart in every surface and listing:

**Product MCPs** — listed as **UZE Underwrite | UZE Assign |
UZE Auction**:

- **UZE Underwrite** — live now (the `UZE_Underwrite` tool).
- **UZE Assign** — added as it comes in.
- **UZE Auction** — added as it comes in.

**Trading MCPs** — TradeLayer and SigLayer, in launch order:

1. **TradeLayer launches first, with the Robinhood brokerage MCP**
   (this build is its door).
2. **SigLayer launches as full production after TradeLayer is
   working.**

The brokerage connect payload carries only the trading
segmentation; the product segmentation lives on the product MCP
surface. Neither grouping borrows the other's names.

## 10. Asset coverage — all available assets (James, 2026-11-16 21:29 ET)

Per Robinhood's "Trading with your agent" article (read in full the
same evening; brief §6): the brokerage agent surface covers **long
equities, options, and crypto** — order types market (share- and
dollar-based), limit, stop limit, stop market; no multi-leg options
by agent; crypto trade-only (no transfer/stake/lend), gated on a
corresponding Robinhood Crypto account and state availability.

The live integration's allowlist plan follows the article's external
-agent catalogue (~90 tools): read tools and the review/preview
simulations across all asset classes are allowlisted after the live
schema review; place/cancel/exercise tools stay behind the user's
per-order confirmation. Robinhood's own trade-approvals control
defaults OFF for MCP accounts, so the review gate in §1 is the
operative fence (the user may also turn approvals on inside
Robinhood as a second fence). Crypto reached through this door is
brokerage-custody crypto under §2's differentiation — never the UZE
crypto solution.

**EVM wallet recovery (indicated + highlighted on the site, James
2026-11-16 22:13 ET; verified against Robinhood's own support pages
the same evening):** the Robinhood Wallet app — Robinhood's
self-custody crypto app, separate from the brokerage app — imports
and recovers EVM wallets (Ethereum, Arbitrum, Polygon, Optimism,
BNB Smart Chain, Base, Robinhood Chain) from a secret recovery
phrase, or from an iCloud / Google Drive backup. Recovery is
user-side: Robinhood never holds the phrase and cannot recover a
lost one.
