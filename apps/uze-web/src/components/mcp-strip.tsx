/** MCP Tooling & Directories strip — rendered in the root layout
 *  immediately above the site footer, on every page (James,
 *  2026-11-18). A directory, not an essay: the MCP families, each
 *  with its true status, and the directory listing program in its
 *  preparation order. Nothing here claims a live endpoint, a live
 *  listing, or a measured time that does not exist — the public
 *  endpoint opens with the January 2, 2027 launch. Cross-links to
 *  the full Directory page and to the Knowledge Base MCP entry,
 *  which links back here. */

const TOOLING = [
  {
    name: "Brokerage MCP",
    body: "The TradeLayer door (Robinhood model). Your AI reads your accounts and trades only inside a fenced, separately funded account — every order reviewed before it executes.",
    status: "Status: API in build — the panel on the Directory page says so plainly until it deploys.",
  },
  {
    name: "UZE Instant MCP",
    body: "One endpoint, two tiers. UZE Instance: compute and settlement, 9 base tools. UZE Markets Instance: adds the TradeLayer, SigLayer and Arcium pathways and the vertical tools — 18 tools in all, the Talent assessment tools included.",
    status: "Status: built and proven — the public endpoint opens with the January 2, 2027 launch.",
  },
  {
    name: "Product MCPs",
    body: "UZE Underwrite · UZE Assign · UZE Auction — the product side: underwriting, assignment and auction work, done by your agent inside limits you set.",
    status: "Status: in build as their own family.",
  },
  {
    name: "Trading MCPs",
    body: "TradeLayer · SigLayer — the trading side: permissionless self-custody markets, reached by your agent inside limits you set.",
    status: "Status: in build as their own family.",
  },
];

const TIER1 = ["Anthropic (Claude) MCP Registry", "Smithery", "Cursor", "Windsurf"];
const TIER2 = [
  "OpenAI",
  "Perplexity",
  "Venice",
  "DeepSeek",
  "Kimi",
  "Hostinger",
  "mcp.so",
  "mcpmarket",
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
          <strong>Directory listings, in preparation order — Tier 1:</strong>{" "}
          {TIER1.join(" · ")}
        </p>
        <p>
          <strong>Tier 2:</strong> {TIER2.join(" · ")}
        </p>
        <p>
          Listings are prepared in that order. A listing is claimed
          only when it is live — none is claimed yet.
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
