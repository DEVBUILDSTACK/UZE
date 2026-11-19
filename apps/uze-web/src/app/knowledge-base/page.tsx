import type { Metadata } from "next";
import { HouseEmail } from "@/components/site-blocks";

export const metadata: Metadata = {
  title: "Knowledge Base — AI Economics | UZEmarkets",
  description:
    "For CFOs, analysts, and business clients: how UZEmarkets' AI underwriting is produced, metered, and secured — pay-as-you-go inference, cryptographic agent identity, and the token utility roadmap.",
};

/** B2B Knowledge Base (James's directive, 2026-11-10; Honest
 *  Register ruling): how the marketplace's AI economics work, in
 *  standard enterprise-finance vocabulary. No internal protocol
 *  names, no unbuilt features claimed — token utility is stated
 *  as roadmap, as it is. Separate from the DevPartner API portal,
 *  which is the technical surface. */
export default function KnowledgeBasePage() {
  return (
    <main className="mk">
      <h1>Knowledge Base</h1>
      <p className="lede">
        For CFOs, investment analysts, and business clients: how our
        AI analysis is produced, what it costs, and how access to it
        is secured — in plain financial terms.
      </p>

      <section>
        <h2>The Agentic Economy</h2>
        <p>
          Our underwriting agents (GIRA and SURA) use advanced AI
          models to perform deep financial analysis. Deep analysis
          requires compute, and compute has a real cost.
        </p>
      </section>

      <section>
        <h2>Pay-As-You-Go Inference</h2>
        <p>
          We do not charge opaque SaaS subscription fees. We use
          metered, pay-per-query billing. When your AI agent
          requests an analysis, it pays a micro-fee in stablecoin
          (USDC) based strictly on the compute used. You pay for
          what you use, nothing more.
        </p>
      </section>

      <section>
        <h2>Agent Identity &amp; Security</h2>
        <p>
          For a lender to trust an AI&rsquo;s analysis, they must
          know who the agent is acting for. We require cryptographic
          agent identity verification. This ensures that every query
          is tied to an authorized entity, preventing unauthorized
          scraping and ensuring compliance.
        </p>
      </section>

      <section>
        <h2>Token Utility</h2>
        <p>
          While pay-as-you-go is the standard, we are building
          native token integration. In future phases, holding the
          required amount of our network&rsquo;s native token in a
          verified wallet will grant a baseline allocation of free
          inference, offsetting compute costs for high-volume
          partners. This token utility is on our roadmap.
        </p>
      </section>

      <section id="mcp">
        <h2>The UZE MCPs — How Agents Connect</h2>
        <p>
          An MCP (Model Context Protocol) server is the door an AI
          assistant walks through to work inside UZEmarkets on your
          behalf: instead of a person clicking through screens,
          your own AI connects over one link and calls defined
          tools, inside limits you set in advance. UZEmarkets is
          building its MCPs as separate families, and the families
          are never blended: the <strong>Brokerage MCP</strong> is
          the TradeLayer door on the brokerage model — your AI
          reads your accounts and trades only inside a fenced,
          separately funded account, with every order reviewed
          before it executes. The <strong>UZE Instant MCP</strong>{" "}
          is our own endpoint for compute and settlement, in two
          tiers: UZE Instance (compute and settlement, nine base
          tools) and UZE Markets Instance (adding the TradeLayer,
          SigLayer and Arcium pathways and the vertical tools —
          eighteen tools in all, the Talent assessment tools among
          them). The <strong>product MCPs</strong> — UZE Underwrite,
          UZE Assign and UZE Auction — carry product work; the{" "}
          <strong>trading MCPs</strong> — TradeLayer and SigLayer —
          carry trading. Product and trading MCPs have nothing to
          do with each other, by design.
        </p>
      </section>

      <section>
        <h2>How Access Is Fenced</h2>
        <p>
          Three layers fence every call. First, your
          pre-authorization: the per-call and per-day limits you set
          before your agent connects. Second, the MCP&apos;s own
          enforcement: a call outside those limits is refused
          before anything executes — the refusal itself is
          recorded. Third, each vertical&apos;s own gates, which a
          call must also pass. Sign-in is bound to your wallet:
          your signature over a one-time challenge is your
          credential, and no password is stored. Every call —
          executed or refused — is written to a permanent record,
          the chronicle, so the history of what your agent did is
          auditable line by line. And revocation is immediate: end
          access and the sessions die at the next call, while a
          call already in flight completes.
        </p>
      </section>

      <section>
        <h2>Settlement</h2>
        <p>
          Where an MCP settles value, the default rail is USDC on
          Solana. That default is a rule of the platform, not a
          per-transaction choice an agent can improvise around.
        </p>
      </section>

      <section>
        <h2>MCP Status — What Is Live, What Is in Build</h2>
        <p>
          Stated plainly, as of this writing: the Brokerage MCP
          demonstration panel is live on the{" "}
          <a href="https://uzemarkets.com/mcp-utility">
            UZE MCP Directory
          </a>{" "}
          page; the brokerage API behind it is in build, and the
          panel says so until it deploys — nothing on that page is
          faked in the meantime. The UZE Instant MCP server is
          built and proven end to end; its public endpoint opens
          with the January 2, 2027 launch, and its directory
          listings are prepared in order — Anthropic (Claude),
          Smithery, Cursor and Windsurf first — and are claimed
          only when they are live. The product and trading MCPs
          are in build as their own families; each will be
          announced here when it opens. A short version of this
          entry — the MCP Tooling &amp; Directories strip — sits
          immediately above the footer of every page on this site,
          and the full directory of MCPs, tools and statuses is
          the{" "}
          <a href="https://uzemarkets.com/mcp-utility">
            UZE MCP Directory
          </a>
          .
        </p>
      </section>

      <HouseEmail />
    </main>
  );
}
