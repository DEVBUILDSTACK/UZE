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
        </div>
      </div>
      <BrokeragePanel />
    </main>
  );
}
