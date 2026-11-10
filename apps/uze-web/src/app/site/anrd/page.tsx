import type { Metadata } from "next";
import Link from "next/link";
import {
  HouseEmail,
  InnovationBlock,
  RoadmapBlock,
} from "@/components/site-blocks";

export const metadata: Metadata = {
  title: "Land & Development — Agriculture, Natural Resources | UZEmarkets",
  description:
    "For landowners, developers and syndicates: UZEmarkets proves the facts about what a parcel holds and what it can become, for the financings and acquisitions that monetize it.",
};

/** Track 2 landing page (James's Website Adaptation Directive,
 *  2026-11-10): A|NR|D for landowners, developers and syndicates.
 *  Copy is the v0.3/v0.5 site draft's land material — the "single
 *  large events" narrative — plain English, no technical jargon, and
 *  no technology partner names (reserved for the DevPartner portal,
 *  which is this track's CTA: developers submit parcels there). */
export default function AnrdPage() {
  return (
    <main className="mk">
      <h1>Prove your land&apos;s value. Unlock capital.</h1>
      <p className="lede">
        For landowners, developers, and syndicates. Land does not produce
        a monthly income story. It is valued on what it holds and what it
        can become — and UZEmarkets proves those facts before the money
        moves.
      </p>

      <InnovationBlock track="anrd" />

      <h2>The Paraguay Example</h2>
      <p>
        <strong>When Liquidity Becomes the Only Metric.</strong>{" "}
        Sovereign risk and economic instability do not just affect
        currency; they freeze the banking system. When a nation faces
        sudden economic distress or governmental fraud, the traditional
        routes to liquidity close overnight.
      </p>
      <p>
        In these moments, a landowner&apos;s perspective shifts
        instantly. Land held for long-term agricultural yield or future
        development must suddenly be reallocated for immediate
        monetization. The question changes from &ldquo;What will this
        land produce next year?&rdquo; to &ldquo;How fast can this land
        be converted to capital?&rdquo;
      </p>
      <p>
        UZEmarkets is built for this reality. We don&apos;t just price
        the original plan; we price the highest and best use of the land
        right now, based on the current economic environment. When the
        traditional banking system freezes, UZEmarkets provides the
        verified, rapid underwriting required to unlock immediate
        liquidity from raw land and agricultural assets.
      </p>

      <h2>A completely different animal</h2>
      <p>
        Farms, raw land, and resources — above ground and below — rest
        their value on what they could become: a crop, a development, a
        discovery. There is no rent roll to check and no next month to
        correct a mistake. What a parcel is worth depends on evidence:
        its boundaries, its soil, its water, the rights below its
        surface, and what the land can realistically be turned into.
      </p>
      <p>
        Today that evidence is assembled deal by deal, from documents
        nobody stands behind in any way you can check — and every new
        party starts the checking from zero. The buyers and backers are
        different, too: investors, investment groups, private capital
        syndicates, niche funds, venture capital, municipalities, and
        governments, each asking different questions, on a different
        clock.
      </p>
      <p>
        Land carries the same trap in its own form: property taxes
        follow the local jurisdiction, and crop insurance follows
        the local crop and climate — both swing sharply from one
        place to the next. A figure means nothing outside its own
        micro-region, so that is where UZEmarkets judges it.
      </p>

      <h2>Single, large events</h2>
      <p>
        Land is monetized in single, large events: a financing, an
        acquisition. One event, priced once, on facts that must be right
        the first time.
      </p>
      <p>
        That is exactly what our process is for. A parcel&apos;s facts —
        boundaries, soil, water, subsurface rights, development
        potential — are stated, tested against surveys, records, and
        field evidence, open to challenge, and settled by independent
        judgment. What survives becomes a proven record that travels with
        the parcel from event to event, so the next financing or
        acquisition starts from facts, not from a fresh round of doubt.
      </p>
      <p>
        And because the risk of being wrong is smaller, the money gets
        cheaper: better terms for the landowner, fairer prices for the
        acquirer, fewer good parcels stalled by uncertainty.
      </p>

      <h2>The process, in plain words</h2>
      <ol>
        <li>
          <strong>Someone states the facts.</strong> A landowner states
          what their parcel holds — its boundaries, soil, and water. A
          developer states what they represent about a parcel&apos;s
          potential. A specialist states what they believe the land can
          become.
        </li>
        <li>
          <strong>The facts are tested.</strong> Each statement is
          compared against surveys, records, field evidence, and the
          proven results of comparable parcels.
        </li>
        <li>
          <strong>Anyone may challenge.</strong> Standing behind a
          statement, or challenging one, means putting something real
          behind your position. Views nobody will back carry no weight.
        </li>
        <li>
          <strong>Independent judgment settles it.</strong> Reviewers who
          work for neither side weigh the evidence and decide. The
          decision, and the reasons for it, are kept in a permanent record
          that anyone relying on it can inspect.
        </li>
        <li>
          <strong>Proven facts become the foundation.</strong> A statement
          that survives this process can be relied on — by a financing
          party or an acquirer — without repeating the checking, and it
          joins the growing library of proven results for the region.
        </li>
      </ol>

      <h2>How an information market forms</h2>
      <p>
        An information market forms wherever a question matters enough
        that people will back their answers. For land, the questions are
        the ones every financing and acquisition turns on: <em>is the
        water really there? will this parcel carry the development its
        owner describes?</em>
      </p>
      <p>
        People who believe a statement, and people who doubt it, each back
        their view; the balance forms a <strong>price</strong> — a living
        measure of how much confidence the statement deserves. When the
        facts come due, the statement is settled on evidence, and the
        settled result becomes proven information, permanently on record.
        Across a region, those settled results become the shared factual
        ground every future event stands on.
      </p>

      <RoadmapBlock track="anrd" />

      <h2>Put your land&apos;s potential to work</h2>
      <p>
        Developers and landowners submit parcels, boundaries, and
        evidence through our developer portal — the technical door into
        the same process described above.
      </p>
      <p>
        <Link className="cta-primary" href="/devpartner">
          Put your land&apos;s potential to work
        </Link>
      </p>
      <HouseEmail />
    </main>
  );
}
