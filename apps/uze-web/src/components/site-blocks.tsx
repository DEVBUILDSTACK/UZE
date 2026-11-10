import Wordmark from "@/components/wordmark";

/** Shared blocks for the client-facing /site track pages (James's
 *  Website Adaptation Directive, 2026-11-10): plain business language
 *  only. Technology partners are NEVER named on client-facing pages —
 *  NEAR, Arcium and Gensyn are reserved for the DevPartner portal and
 *  internal documentation. The roadmap's technology and grant lines use
 *  James's exact anonymized phrasing from the directive. */

export function RoadmapBlock({ track }: { track: "hicre" | "anrd" }) {
  return (
    <>
      <h2>The road ahead</h2>
      <p>
        <strong>Where we are (November 2026).</strong> The checking engine
        is built and proven: statements judged, challenged, settled on
        evidence, and recorded, end to end — including a live settled
        transaction. The Content Desk publishes live market intelligence
        for ten micro-regions across our two launch markets — South &amp;
        Central Florida, and the Mid-Atlantic (Baltimore and Washington,
        DC). The developer portal serves our land-track partners in four
        languages.
      </p>
      <p>
        <strong>Next (into 2027).</strong>{" "}
        {track === "hicre"
          ? "The first live HiCRE records for financing partners in our two launch markets; owner- and broker-issued statements at working scale; the first priced information markets formed on property statements; Costa Rica and the Dominican Republic are next to launch."
          : "Partner parcels and their evidence at working scale across Brazil, Uruguay, and the United States; the first proven land records standing behind live financings and acquisitions; Costa Rica and the Dominican Republic are next to launch."}
      </p>
      {track === "hicre" ? (
        <>
          <p>
            <strong>Technology:</strong> We build on high-performance
            settlement networks and privacy-preserving computing to ensure
            every transaction is secure and verifiable.
          </p>
          <p>
            <strong>Grant support:</strong> We are actively targeting
            leading AI research grants to fund the launch and initial
            liquidity of our first markets.
          </p>
        </>
      ) : (
        <>
          <p>
            <strong>Technology alliances:</strong> We are actively
            integrating specialized technology partners in agriculture and
            natural resources—specifically those focused on crop yield
            optimization, soil chemistry, and spatial resource mapping—to
            ensure every land asset is underwritten with the highest
            fidelity data available.
          </p>
          <p>
            <strong>Financing &amp; grant support:</strong> We are
            targeting strategic grant support and investment alliances
            specifically focused on land-use technology. Furthermore, we
            are actively building private debt syndicates and venture
            markets in the US and the Americas, while integrating with
            long-standing private debt venture networks in Brazil to
            unlock immediate liquidity for agricultural and development
            acquisitions.
          </p>
        </>
      )}
    </>
  );
}

/** The public house email, rendered per the wordmark rules: only the
 *  domain's UZE is tangerine; the local part, the @ and .com are ink. */
export function HouseEmail() {
  return (
    <p className="note">
      Questions or team access? Email:{" "}
      <a href="mailto:UZEmarket@uzemarkets.com">
        <span className="addr-ink">UZEmarket@</span>
        <Wordmark />
        <span className="addr-ink">.com</span>
      </a>
    </p>
  );
}
