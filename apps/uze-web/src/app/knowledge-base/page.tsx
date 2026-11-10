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

      <HouseEmail />
    </main>
  );
}
