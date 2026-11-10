import type { Metadata } from "next";
import Link from "next/link";
import {
  HouseEmail,
  InnovationBlock,
  RoadmapBlock,
} from "@/components/site-blocks";

export const metadata: Metadata = {
  title: "HiCRE — Hospitality & Income Properties | UZEmarkets",
  description:
    "For owners, brokers and lenders: UZEmarkets proves the numbers an income property's financing depends on, so decisions take days, not months.",
};

/** Track 1 landing page (James's Website Adaptation Directive,
 *  2026-11-10): HiCRE for owners, brokers and lenders. Copy is the
 *  v0.3/v0.5 site draft — Specification 07 digested into a business
 *  USP, plain English, no technical jargon, and no technology partner
 *  names (those are reserved for the DevPartner portal). */
export default function HicrePage() {
  return (
    <main className="mk">
      <h1>Prove your property&apos;s P&amp;L. Get financed faster.</h1>
      <p className="lede">
        UZEmarkets is the information market where revenue, operating
        expenses, and net income are verified by AI, challenged on
        evidence, and trusted by lenders.
      </p>

      <InnovationBlock track="hicre" />

      <h2>The problem UZEmarkets solves</h2>
      <p>
        An income property — a hotel, a resort, an apartment building, any
        commercial property that earns money from rents and guests — is
        worth what its income proves it to be worth.
      </p>
      <p>
        The financial packages behind these properties are documents full
        of numbers nobody stands behind in any way you can check. When a
        property needs financing, or a buyer, or an investor, the decision
        rests on those numbers: what the property earned, what it cost to
        run, what it is likely to earn next. The lender or buyer has no
        independent way to know they are true.
      </p>
      <p>
        Two lines in that statement swing more than all the others:
        taxes and insurance. A property tax bill follows the city,
        county, and state the property sits in; an insurance premium
        follows its geography and climate — Miami&rsquo;s hurricane
        exposure has nothing in common with Baltimore&rsquo;s. A cost
        judged against the wrong market&rsquo;s benchmarks is a cost
        misjudged. That is why UZEmarkets works in micro-regions:
        every number is weighed against its own local market, and no
        other.
      </p>
      <p>
        So every decision carries a hidden charge: the cost of not being
        sure. The decision-maker either spends weeks or months checking
        everything themselves — slow, expensive, and repeated from zero on
        every deal — or they protect themselves the only other way they
        can: they offer less, and charge more, to cover the risk that the
        numbers are wrong.
      </p>
      <p>
        Good properties are delayed, underpriced, or turned away. Not
        because the property is weak — because nobody could be sure of its
        facts.
      </p>

      <h2>Why certainty changes the price</h2>
      <p>
        The price of risk is, in large part, the price of uncertainty.
        When the facts about a property&apos;s income and costs have
        already been checked — by a process that works for neither side,
        and whose work anyone can inspect — the person deciding no longer
        has to guess, and no longer has to charge for guessing.
      </p>
      <p>
        That is what UZEmarkets&apos; engine does. It is a proprietary
        system that works continuously, the way a tireless team of
        analysts would: gathering the numbers, testing them against
        records and against what similar properties actually did, hearing
        challenges, and settling disagreements on evidence. It never
        forgets a result: every fact it proves becomes a reference that
        makes the next property faster and sharper to judge.
      </p>
      <p>
        The result is simple. Decisions that took months take days. And
        because the risk of being wrong is smaller, the money itself gets
        cheaper — better terms for owners, fairer prices for buyers, fewer
        good deals lost.
      </p>

      <h2>The process, in plain words</h2>
      <ol>
        <li>
          <strong>Someone states the facts.</strong> An owner states what
          their property earned and spent. A broker states what they
          represent about a property they are selling. A specialist states
          what they believe a property will do.
        </li>
        <li>
          <strong>The facts are tested.</strong> Each statement is compared
          against records, history, and the proven results of comparable
          properties.
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
          that survives this process can be relied on — by a lender, a
          buyer, an investor — without repeating the checking. And it
          joins the growing library of proven results that every future
          decision stands on.
        </li>
      </ol>

      <h2>How an information market forms</h2>
      <p>
        An information market forms wherever a question matters enough
        that people will back their answers.
      </p>
      <p>
        It begins with a statement that someone needs answered before they
        will act: <em>will this property&apos;s costs come in where its
        owner says they will?</em> People who believe the statement, and
        people who doubt it, each back their view. The balance of those
        backed views forms a <strong>price</strong> — a living measure of
        how much confidence the statement deserves.
      </p>
      <p>
        When the facts come due, the statement is settled on evidence.
        Those who judged rightly are rewarded; the settled result becomes
        proven information, permanently on record.
      </p>
      <p>
        Repeat that across a property, then a street, then a neighborhood,
        and something new exists: a market not in the property itself, but
        in the truth about it — where belief is priced, tested, and
        replaced by fact. That is an information market, and it is what
        UZEmarkets builds: every financing question, every owner&apos;s
        statement, every specialist&apos;s judgment is a door into the
        same market.
      </p>

      <h2>Our vision for HiCRE</h2>
      <p>
        <strong>HiCRE</strong> is our name for income-producing commercial
        real estate: hospitality and income properties whose value is the
        money they earn, period after period.
      </p>
      <p>
        A HiCRE property is not a static asset. It is a living business.
        Every month it produces a fresh set of facts — income, occupancy,
        costs — so its truth renews itself constantly. That rhythm is what
        makes HiCRE unique: it can be checked continuously, priced
        continuously, and financed on current facts instead of old
        paperwork.
      </p>
      <p>
        Our vision is that every income property carries a living,
        verified record of its own performance — so that financing a good
        property becomes fast and fairly priced, anywhere in the Americas,
        and a property&apos;s proven record becomes as much a part of its
        value as its walls and its land.
      </p>

      <h2>The team behind it</h2>
      <p>
        UZEmarkets is built by Learn2Launch, the launchpad and accelerator
        of 456iP.
      </p>
      <ul>
        <li>
          <strong>James (Hammond) Dugan</strong> — Founder and Project
          Lead, 456iP. Miami. Leads the UZEmarkets build and its partner
          network across the Americas.
        </li>
        <li>
          <strong>William Dugan</strong> — Launch principal. Commercial
          artist and business owner in fashion and commercial art; leads
          the brand and creative surface. Washington DC–Baltimore.
        </li>
        <li>
          <strong>James Dugan</strong> — Launch principal. Financial
          analyst in real estate; leads the income-property analysis
          discipline behind the HiCRE track.
        </li>
        <li>
          <strong>Jonathan Schmidt</strong> — Launch principal, creative
          interface. Animator and creative lead based in Santo Domingo,
          Dominican Republic.
        </li>
        <li>
          <strong>Joey Hunter</strong> — Creator collaborator and advisor,
          Fort Lauderdale.
        </li>
        <li>
          <strong>The 456iP build team</strong> — engineers across
          Melbourne, Surat, and the United States, who built and operate
          the engine, the Content Desk, and the partner portal.
        </li>
      </ul>

      <RoadmapBlock track="hicre" />

      <h2>Put your property&apos;s facts to work</h2>
      <p>
        It works because it removes the one cost every party pays today:
        the cost of not being sure. Owners get decisions in days instead
        of months, and terms that price their property&apos;s proven
        record instead of a stranger&apos;s doubt. Financing partners get
        facts they can rely on without repeating months of checking.
        Brokers stand behind their numbers — and are seen to.
      </p>
      <p>
        If you own, represent, or finance income property: create your
        profile and bring us the first property. The checking is on us.
      </p>
      <p>
        <Link className="cta-primary" href="/onboard">
          Create your profile
        </Link>
      </p>
      <HouseEmail />
    </main>
  );
}
