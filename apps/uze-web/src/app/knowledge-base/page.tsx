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
          tools, inside limits you set in advance. Two lead MCPs
          carry the desks: <strong>UZE Underwrite</strong>, the
          Autonomous Underwriting desk, and{" "}
          <strong>Talent matching</strong>, the Talent desk. The{" "}
          <strong>UZE Instant MCP</strong> is the platform endpoint
          they ride on. Around them stand two families that are
          never blended: the <strong>product MCPs</strong> (UZE
          Underwrite · UZE Assign · UZE Auction) and the{" "}
          <strong>trading MCPs</strong> (TradeLayer · SigLayer),
          with the Brokerage MCP as the TradeLayer door. Product
          MCPs and trading MCPs have nothing to do with each other,
          by design.
        </p>
      </section>

      <section>
        <h2>UZE Underwrite — the Lead Product MCP</h2>
        <p>
          UZE Underwrite is the MCP face of the UZEmarkets
          Autonomous Underwriting desk — one of the three matching
          desks that make up UZEmarkets superIntelligence. Submit
          a Hospitality or Income property with its operating
          financials and receive an underwriting read benchmarked
          against its own micro-region: every claim checked, every
          number in its proper bucket, nothing taken on faith. It
          underwrites Hospitality and Income real estate (the H
          and I of the HIADR asset taxonomy) inside defined
          micro-regions.
        </p>
        <p>
          Financial claims arrive as <strong>Assuraties</strong> —
          claims a seller or advisor stands behind — and are
          tested before they are relied on. Performance is read in
          exactly seven buckets, never blended:{" "}
          <strong>
            Revenue; Operating Expenses; Taxes; Insurance(s);
            Interest Expense/Income; Miscellaneous Net
            Expenses/Income; Profit (Net Income)
          </strong>
          . Operating Expenses never absorb Taxes, Insurance, or
          Interest. Judgement is made only against benchmarks from
          the <strong>same micro-region</strong>, because taxes —
          the largest driver of micro-market variability — make
          cross-region comparison meaningless. Claims that survive
          the process are <strong>Assuratized</strong>:
          reliance-grade, with the evidence trail attached. It
          serves lenders, buyers, and financing partners who need
          an underwriting read they can rely on, and sellers whose
          financials are strong enough to be proven rather than
          pitched. Its tool set — underwriting submission,
          benchmark read, claim check, reliance report — is design
          at this stage, labelled as such; the built catalog of
          record today is the UZE Instant MCP&apos;s.
        </p>
      </section>

      <section>
        <h2>Talent Matching — Fit Proven, Not Asserted</h2>
        <p>
          Talent matching is the MCP face of the UZE Talent desk:
          Role × Realm matching with assessment proof. Configure
          the role you need; the desk matches on role and realm,
          proves fit through a two-gate assessment, and keeps
          every candidate blind until engagement and deposit. A
          role is configured once, as a keyed record in the{" "}
          <strong>Role × Realm taxonomy</strong> — 11 roles across
          6 realms of expertise, up to five Role×Realm pairs per
          professional, ranked primary to quinary. The desk
          matches against that taxonomy; it does not
          keyword-search résumés.
        </p>
        <p>
          From the role, the system generates a skills assessment
          from a curated template library — generation is
          slot-filling against calibrated templates, never free
          invention. Two human gates stand before anything runs:{" "}
          <strong>Gate 1</strong>, the engaging employer&apos;s
          confirmation of intent, and <strong>Gate 2</strong>, an
          approver of record&apos;s confirmation that the
          assessment is valid for the vertical. An agent identity
          can satisfy neither gate. Runs are scored at a scoring
          center — an AI grade with a human-review flag against a
          stated threshold — and results are published{" "}
          <strong>redacted and pseudonymous</strong>: no talent
          names, no emails, no company names, ever, until the
          moment identity is earned. Engagement runs on two money
          models: <strong>outstaffing</strong> — UZE Markets pays
          the talent and bills the client — and{" "}
          <strong>placement</strong> — UZE places for a fee of at
          least one month (30 days) of salary, and the client pays
          the individual directly. A talent target is never
          exposed until both a signed engagement and a deposit are
          in hand; until then, talent is presented blind, through
          the desk alone. The three tools are built and live in
          the UZE Instant MCP: <code>submit_assessment</code>,{" "}
          <code>score_assessment</code> and{" "}
          <code>publish_assessment_outcome</code>.
        </p>
      </section>

      <section>
        <h2>The Rest of the Family</h2>
        <p>
          <strong>UZE Assign</strong>, the DealFi matching desk as
          an MCP: a deal or position is described once, and the
          desk assigns it to the matched counterparty on the other
          side of the market. <strong>UZE Auction</strong>:
          sealed-bid auctions for the secondary market — bids
          sealed under Arcium MPC on Solana, matched by solvers,
          cleared at a uniform price; primary sales are never
          auctioned, because primary is fixed price plus
          allocation. The <strong>Brokerage MCP</strong> is the
          TradeLayer door on the Robinhood model, detailed on the
          Directory page. <strong>TradeLayer</strong> is the
          trading surface for the information markets, launching
          with the brokerage door in front of it;{" "}
          <strong>SigLayer</strong> is the full production trading
          layer — treasury, signing, and settlement discipline —
          which follows once TradeLayer works.
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
          Settlement follows the rail law:{" "}
          <strong>USDC on Solana is the default for everything</strong>,
          cascading to USDC on Base, then USDG on Robinhood Chain;
          Tempo/Stripe CASH only where a vertical requires it.
          That default is a rule of the platform, not a
          per-transaction choice an agent can improvise around.
        </p>
      </section>

      <section>
        <h2>MCP Status — What Is Live, What Is in Build</h2>
        <p>
          Stated plainly, as of this writing.{" "}
          <strong>UZE Underwrite:</strong> the underwriting desk
          is in build on the AssurativeV2 core; the MCP ships as a
          product MCP with the Markets tier.{" "}
          <strong>Talent matching:</strong> the Talent system of
          record is built and live (the UZE Dev Library is its
          developer instance), and the three tools activated on
          the first assessment outcome published under the two
          gates; production Gate 2 opens per vertical as approvers
          of record are named. <strong>UZE Instant MCP:</strong>{" "}
          built and proven — gating, limits, and the revoke
          cascade demonstrated — and its public endpoint opens
          with the January 2, 2027 launch; no spin-up time is
          claimed until provisioning is measured.{" "}
          <strong>Brokerage MCP:</strong> API in build; the panel
          on the{" "}
          <a href="https://uzemarkets.com/mcp-utility">
            UZE MCP Directory
          </a>{" "}
          page states its live status and governs — nothing on
          that page is faked in the meantime.{" "}
          <strong>UZE Assign:</strong> the DealFi desk is in
          build and brings online first among the desks.{" "}
          <strong>UZE Auction, TradeLayer, SigLayer:</strong>{" "}
          design of record and in build in their sequence.
          Directory listings are prepared in the filed order —
          the Anthropic (Claude) MCP Registry first, the reach
          tier (OpenAI, Microsoft Copilot, Google, Meta,
          Perplexity, Venice AI, DeepSeek, Kimi) after — and claim
          only compatibility that is verified when the claim is
          made; no listing is claimed live. A short version of
          this entry — the MCP Tooling &amp; Directories strip —
          sits immediately above the footer of every page on this
          site, and the full directory of MCPs, tools and statuses
          is the{" "}
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
