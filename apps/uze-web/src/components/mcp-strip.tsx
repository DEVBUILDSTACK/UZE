/** MCP Tooling & Directories strip — rendered in the root layout
 *  immediately above the site footer, on every page (James,
 *  2026-11-18). A directory, not an essay: the MCP families, each
 *  with its true status, and the directory listing program in its
 *  preparation order. The wording is the filed descriptive
 *  language (docs/instant-mcp/MCP-DESCRIPTIVE-LANGUAGE-v0.1.md) —
 *  one language for the listings, this section, and the Knowledge
 *  Base; condensed only where the strip format forces it, status
 *  lines verbatim in substance. Nothing here claims a live public
 *  endpoint or a live listing — the public endpoint opens with
 *  the January 2, 2027 launch. Cross-links to the full Directory
 *  page and to the Knowledge Base MCP entry, which links back. */

const TOOLING = [
  {
    name: "UZE Underwrite",
    body: "The Autonomous Underwriting desk as an MCP. Submit a Hospitality or Income property with its operating financials and receive an underwriting read benchmarked against its own micro-region: every claim checked, every number in its proper bucket, nothing taken on faith.",
    status:
      "Status: the underwriting desk is in build on the AssurativeV2 core; the MCP ships as a product MCP with the Markets tier.",
  },
  {
    name: "Talent matching",
    body: "Role × Realm matching with assessment proof. Configure the role you need; the desk matches on role and realm, proves fit through a two-gate assessment, and keeps every candidate blind until engagement and deposit.",
    status:
      "Status: built and live in the UZE Instant MCP — the three Talent tools are on; production Gate 2 opens per vertical as approvers of record are named.",
  },
  {
    name: "UZE Instant MCP",
    body: "One endpoint for UZE compute and markets. Provision a UZE Instance, meter it, terminate it — every call inside limits you set in advance, every call on the record. UZE Markets Instance adds the TradeLayer, SigLayer and Arcium pathways and the vertical tools: 18 tools in all.",
    status:
      "Status: built and proven; the public endpoint opens with the January 2, 2027 launch.",
  },
  {
    name: "Brokerage MCP",
    body: "The TradeLayer door: connect your AI to your brokerage accounts — it reads every account and trades only where you fence it in: a dedicated, separately funded MCP account, every order reviewed before it executes.",
    status:
      "Status: API in build — the Directory page's panel states its live status and governs.",
  },
  {
    name: "Product MCPs",
    body: "UZE Assign — DealFi matching as an MCP: a deal or position is described once, and the desk assigns it to the matched counterparty. UZE Auction — sealed-bid auctions for the secondary market; primary sales are never auctioned.",
    status:
      "Status: the DealFi desk is in build and comes online first among the desks; the Auction surface is design of record.",
  },
  {
    name: "Trading MCPs",
    body: "TradeLayer — the trading surface for the information markets, launching with the Brokerage MCP door in front of it. SigLayer — the full production trading layer: treasury, signing, and settlement discipline.",
    status:
      "Status: TradeLayer in build behind the brokerage door; SigLayer is design of record, sequenced after TradeLayer.",
  },
];

export default function McpStrip() {
  return (
    <section className="mcp-strip" aria-label="MCP tooling and directories">
      <h2>MCP Tooling &amp; Directories</h2>
      <p className="mcp-strip-lede">
        Every UZE MCP, in one strip — what each one does, and where
        it honestly stands.
      </p>
      <div className="mcp-strip-grid">
        {TOOLING.map((t) => (
          <article className="mcp-strip-item" key={t.name}>
            <h3>{t.name}</h3>
            <p>{t.body}</p>
            <p className="mcp-strip-status">{t.status}</p>
          </article>
        ))}
      </div>
      <p className="mcp-strip-rule">
        Product MCPs and trading MCPs are separate families — never
        blended.
      </p>
      <div className="mcp-strip-dirs">
        <p>
          <strong>Directory listings, in preparation order — first:</strong>{" "}
          Anthropic (Claude) MCP Registry, the conversion tier.
        </p>
        <p>
          <strong>Reach tier:</strong> OpenAI · Microsoft Copilot ·
          Google (Duet / Gemini) · Meta (Muse) · Perplexity ·
          Venice AI · DeepSeek · Kimi
        </p>
        <p>
          Listings claim only compatibility that is verified when
          the claim is made — no listing is claimed live yet.
        </p>
      </div>
      <nav className="mcp-strip-links" aria-label="MCP directory links">
        <a href="https://uzemarkets.com/mcp-utility">
          <span className="link-glyph" aria-hidden="true">
            🔗
          </span>{" "}
          Full directory
        </a>
        <a href="https://uzemarkets.com/knowledge-base#mcp">
          <span className="link-glyph" aria-hidden="true">
            🔗
          </span>{" "}
          MCP details in the Knowledge Base
        </a>
      </nav>
    </section>
  );
}
