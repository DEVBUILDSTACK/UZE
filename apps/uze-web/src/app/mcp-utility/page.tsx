import type { Metadata } from "next";
import BrokeragePanel from "@/components/brokerage-panel";

export const metadata: Metadata = {
  title: "UZE MCP Directory | UZEmarkets",
  description:
    "The UZE MCP Directory — the brokerage-model MCP, the TradeLayer door: connect your own LLM, read every account, trade only in a dedicated MCP account. UZE crypto stays permissionless self-custody.",
};

/** Brokerage MCP mock-up (2026-11-16, James's build order:
 *  the Robinhood-model MCP first, then TradeLayer and SigLayer).
 *  Spec: docs/MCP-UTILITY-SPEC-v0.1.md. The panel speaks JSON-RPC
 *  to the live MCP surface; demonstration scope is stated on the
 *  page — demo data, simulated orders, no real money. */
export default function McpUtilityPage() {
  return (
    <main className="mk">
      <h1>UZE MCP Directory</h1>
      <p className="lede">
        Brokerage MCP — the TradeLayer door. Connect your AI. It
        reads your accounts — and trades only where you fence it in.
      </p>
      <p>
        This is the brokerage model as an MCP utility, built first
        ahead of the TradeLayer and SigLayer trading surfaces: your
        own LLM connects over one link, sees every account, and can
        place orders only inside a dedicated, separately funded MCP
        account — every order reviewed before it executes. The live
        model covers all available assets — long equities, options,
        and crypto (order types: market, limit, stop limit, stop
        market; this demo simulates equities). Crypto placed here is
        brokerage-custody crypto, and it is not the UZE crypto
        solution: UZE crypto is permissionless self-custody, with
        earlier-stage tokens the brokerage never lists, at your own
        election — and UZE TradFi Complex &amp; Agentic DeFi, the
        self-custody side of this directory, is for experienced
        DeFi traders only, more than 5 consecutive years trading
        permissionless, non-custodial DeFi markets.
      </p>
      <p className="note">
        Dynamic mock-up — demo data, simulated orders, no brokerage
        connected, no real money moves. The panel below talks to the
        real MCP surface (<code>POST /api/v1/mcp-brokerage</code>);
        if that API build is not deployed yet, the panel says so
        instead of faking the data.
      </p>
      <h2>Directory</h2>
      <div className="cards">
        <div
          className="card"
          style={{ borderLeft: "4px solid var(--accent)" }}
        >
          <h3>Robinhood Brokerage — UZE TradFi Complex &amp; Agentic DeFi</h3>
          <p className="meta">
            Traditional finance — the prominent door across the US
            and Europe
          </p>
          <p>
            The TradFi complex: long equities and options in a
            brokerage account, held in brokerage custody. Your agent
            reads every account and trades only in the dedicated MCP
            account, behind a review step. Its agentic DeFi side is
            the UZE self-custody extension in the two-doors panel
            below. The live demo of this entry is the panel below.
          </p>
        </div>
        <div className="card">
          <h3>Robinhood Crypto</h3>
          <p className="meta">Kept separate — brokerage custody</p>
          <p>
            Crypto placed through Robinhood sits in Robinhood&apos;s
            custody and is not the UZE crypto solution. UZE crypto is
            permissionless self-custody — TradeLayer and SigLayer,
            the two-doors panel below.
          </p>
          <p className="highlight-callout">
            <strong>Highlight — EVM wallet recovery supported:</strong>{" "}
            the Robinhood Wallet app (Robinhood&apos;s self-custody
            crypto app) imports and recovers EVM wallets — Ethereum,
            Arbitrum, Polygon, Optimism, Base, and Robinhood Chain —
            from a secret recovery phrase or an iCloud / Google Drive
            backup.
          </p>
        </div>
      </div>
      <BrokeragePanel />

      <h2>UZE Instant MCP</h2>
      <p>
        The second door in this directory is our own: one MCP
        endpoint for UZE compute and settlement, in two tiers. The
        server is built and proven — gating, metering and the
        revoke cascade all demonstrated end to end. The public
        endpoint opens with the January 2, 2027 launch; until then
        there is no public endpoint to connect to, and this page
        will say so until there is.
      </p>
      <div className="cards">
        <div className="card">
          <h3>UZE Instance</h3>
          <p className="meta">The base tier — compute + settlement</p>
          <p>
            Branded compute with settlement built in, and the nine
            base tools below. No vertical access: this tier is the
            general-purpose door.
          </p>
        </div>
        <div className="card">
          <h3>UZE Markets Instance</h3>
          <p className="meta">The premium tier — the verticals</p>
          <p>
            Everything in UZE Instance, plus the TradeLayer,
            SigLayer and Arcium pathways and the nine vertical
            tools — the Talent assessment tools among them.
          </p>
        </div>
      </div>
      <h3>The 18 tools</h3>
      <p>
        <strong>Nine base tools.</strong> Seven are live in the
        build: <code>provision_instance</code>,{" "}
        <code>get_credentials</code>, <code>terminate_instance</code>,{" "}
        <code>get_status</code>, <code>list_tiers</code>,{" "}
        <code>query_balance</code> and <code>pay_via_x402</code>. Two
        arrive with the settlement phase: <code>create_escrow</code>{" "}
        and <code>release_milestone</code>.
      </p>
      <p>
        <strong>Nine vertical tools</strong> ride the Markets tier —
        the TradeLayer, SigLayer and Arcium pathways, and the
        Talent assessment tools: <code>submit_assessment</code>,{" "}
        <code>score_assessment</code> and{" "}
        <code>publish_assessment_outcome</code>. A tool your tier
        does not carry is refused before it runs, and the refusal
        is recorded like every other call.
      </p>
      <p className="note">
        Every call is fenced three ways — the limits you
        pre-authorize, the MCP&apos;s own enforcement of those
        limits before anything executes, and each vertical&apos;s
        own gates — and every call is written to the chronicle.
        The full mechanics are detailed in the{" "}
        <a href="https://uzemarkets.com/knowledge-base#mcp">
          Knowledge Base
        </a>
        .
      </p>

      <h2>Directories</h2>
      <p>
        An MCP is only as useful as the assistants that can find
        it, so the UZE MCPs are listed as connectors in the major
        AI directories. Listings are prepared in this order:
      </p>
      <p>
        <strong>Tier 1:</strong> Anthropic (Claude) MCP Registry ·
        Smithery · Cursor · Windsurf.
        <br />
        <strong>Tier 2:</strong> OpenAI · Perplexity · Venice ·
        DeepSeek · Kimi · Hostinger · mcp.so · mcpmarket.
      </p>
      <p className="note">
        No listing is claimed until it is live — when one goes
        live, it will be named here as live, with its link.
      </p>
    </main>
  );
}
