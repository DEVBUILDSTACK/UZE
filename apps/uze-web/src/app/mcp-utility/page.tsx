import type { Metadata } from "next";
import BrokeragePanel from "@/components/brokerage-panel";

export const metadata: Metadata = {
  title: "Brokerage MCP | UZEmarkets",
  description:
    "Dynamic mock-up of the brokerage-model MCP — the TradeLayer door: connect your own LLM, read every account, trade TradFi only in a dedicated MCP account. UZE crypto stays permissionless self-custody.",
};

/** Brokerage MCP mock-up (2026-11-16, James's build order:
 *  the Robinhood-model MCP first, then TradeLayer and SigLayer).
 *  Spec: docs/MCP-UTILITY-SPEC-v0.1.md. The panel speaks JSON-RPC
 *  to the live MCP surface; demonstration scope is stated on the
 *  page — demo data, simulated orders, no real money. */
export default function McpUtilityPage() {
  return (
    <main className="mk">
      <h1>Brokerage MCP — the TradeLayer door</h1>
      <p className="lede">
        Connect your AI. It reads your accounts — and trades only
        where you fence it in.
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
        election — and that extension is for experienced DeFi
        traders only, more than 5 consecutive years trading
        permissionless, non-custodial DeFi markets.
      </p>
      <p className="note">
        Dynamic mock-up — demo data, simulated orders, no brokerage
        connected, no real money moves. The panel below talks to the
        real MCP surface (<code>POST /api/v1/mcp-brokerage</code>);
        if that API build is not deployed yet, the panel says so
        instead of faking the data.
      </p>
      <BrokeragePanel />
    </main>
  );
}
