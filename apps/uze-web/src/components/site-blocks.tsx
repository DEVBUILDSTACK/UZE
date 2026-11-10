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

/** §0 — The Innovation (James's positioning directive, 2026-11-10).
 *  Universal opening, identical on both tracks; track-specific closing.
 *  The phrase "autonomous innovation replaces human pricing" is the
 *  position statement, used exactly; no other AI/autonomy language, no
 *  technology partner names, launch framing only. */
export function InnovationBlock({ track }: { track: "hicre" | "anrd" }) {
  return (
    <>
      <h2>The Innovation</h2>
      <p>
        UZEmarkets is building information markets — markets that price
        the value of a property&apos;s facts, not just the property
        itself.
      </p>
      <p>
        When autonomous innovation replaces human pricing, two things
        change at once: the risk of being wrong falls, and the speed of
        financing decisions rises. The lender no longer waits weeks for a
        stranger&apos;s opinion. The owner no longer accepts a discount
        for someone else&apos;s uncertainty. The market prices the truth,
        and the truth moves the money.
      </p>
      <p>
        UZEmarkets stands as an innovator in the Americas market across
        two very different asset classes, judged by two very different
        rules.
      </p>
      {track === "hicre" ? (
        <p>
          Income-producing commercial real estate — hotels, resorts,
          apartment buildings, any property that earns money from rents
          and guests — is judged on the income it proves, period after
          period. Every month produces a fresh set of facts. The engine
          prices those facts continuously, so a good property is financed
          on what it has proven, not on what someone hopes it might do.
        </p>
      ) : (
        <>
          <p>
            Land is judged on evidence about what it holds and what it
            can become — whether that is agricultural production,
            subterranean natural resources, or the development
            opportunity the land itself makes possible.
          </p>
          <p>
            And critically: when a parcel&apos;s intended use is
            reallocated — agricultural land steered toward development,
            or a resource-bearing tract redirected because liquidity or
            monetization demands it — the engine follows the land&apos;s
            highest and best use, not the original plan. A shift in use
            is not a break in the record. It is a new question the market
            prices.
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
