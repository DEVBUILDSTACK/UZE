import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Talent Placement | UZEmarkets",
  description:
    "UZEmarkets Talent Placement: the underwrite identifies the operational roles an asset already pays for — placement sources the people.",
};

const PAGE_JSON_LD = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebPage",
      name: "Talent Placement",
      url: "https://uzemarkets.com/talent/placement",
      description:
        "UZEmarkets Talent Placement: the underwrite identifies the operational roles an asset already pays for — placement sources the people.",
      isPartOf: {
        "@type": "WebSite",
        name: "UZEmarkets",
        url: "https://uzemarkets.com",
      },
    },
    {
      "@type": "Service",
      name: "UZEmarkets Talent Placement",
      serviceType:
        "Talent placement for hospitality and income commercial real estate",
      description:
        "The UZE Underwrite report reads an asset's payroll lines and identifies the operational roles the property already pays for; Talent Placement sources vetted people for flagged roles, matched against the payroll budget the underwriting calculated. Talent submits a TalentProfile as JSON through the underwriting gateway; matching in the current demonstration is run by the placement team.",
      url: "https://uzemarkets.com/talent/placement",
      provider: { "@type": "Organization", name: "UZEmarkets" },
    },
  ],
};

/** Talent Placement (owner tap, 2026-11-12): the B2C side of
 *  the underwrite bridge. The underwrite's talent_placement
 *  object names the roles an asset's payroll already funds;
 *  this desk sources them. Talent submits a TalentProfile as
 *  JSON (validated by the gateway); PDF/Word resume parsing
 *  is deferred to the January 2nd update and the page says so
 *  plainly. Demo scope: profiles are validated and recorded;
 *  matching is run by the placement team, not automated here. */
export default function TalentPlacementPage() {
  return (
    <main className="mk">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(PAGE_JSON_LD) }}
      />
      <p className="note" role="note">
        <strong>Demonstration Environment:</strong> this page is
        backed by synthetic fixtures. The live API is pending
        deployment.
      </p>
      <h1>Talent Placement</h1>
      <p className="lede">
        <strong>
          The underwriting names the role. Placement fills it.
        </strong>
      </p>
      <p>
        Every UZE Underwrite report reads the asset&apos;s own
        payroll lines and identifies the operational roles the
        property already pays for — property manager,
        maintenance, leasing, security. When a report flags a
        role, this desk sources a vetted person for it, matched
        against the payroll budget the underwriting calculated.
      </p>

      <section>
        <h2>For property owners</h2>
        <p>
          Run the underwrite first. If the report flags a role
          your asset needs, the placement team sources candidates
          whose rate requirements fit the asset&apos;s payroll
          envelope — no separate brief, no re-keyed numbers: the
          underwrite is the brief.
        </p>
        <p>
          <a href="https://uzemarkets.com/underwrite">
            Go to UZE Underwrite
          </a>
        </p>
      </section>

      <section>
        <h2>For talent</h2>
        <p>
          Submit your profile as a TalentProfile JSON — name,
          role, years of experience, skills, your rate
          requirement, and any certifications — through the
          underwriting gateway. Profiles are validated on
          arrival; an incomplete profile comes back naming
          exactly which fields are missing.
        </p>
        <p>
          PDF and Word resumes are not parsed yet: resume parsing
          arrives with our January 2nd update. Until then, JSON
          is the format that gets you matched.
        </p>
      </section>

      <section>
        <h2>Two kinds of work, one marketplace</h2>
        <p>
          <strong>Operations</strong> — the people who run the
          asset: general managers, property managers,
          maintenance, leasing. Hospitality organizations hire
          them; residential syndicates and owners hire them.
          <strong> Knowledge work</strong> — the people who run
          the numbers: financial analysts who keep an
          asset&apos;s underwriting current, engaged as employees,
          as fractional contractors, or as autonomous agentic
          services.
        </p>
        <p>
          A profile states its focus — hospitality or
          residential — and its kind: employee, contractor, or
          agentic service. A need states the same two things.
          The match is arithmetic on those fields plus the role:
          nothing vaguer is allowed to call itself a match.
        </p>
        <p>
          <em>Example — operations:</em> a hospitality
          organization needs a general manager for a 340-room
          hotel. The match is an employee-profile general
          manager whose focus is hospitality.
        </p>
        <p>
          <em>Example — knowledge work:</em> a syndicate acquires
          a 240-unit residential community. It does not need a
          full-time analyst; it needs the monthly underwriting
          run. The match is a residential financial analyst
          working as a contractor — or an agentic analysis
          service that returns the same verified report.
        </p>
      </section>

      <section>
        <h2>The pre-assessment — skills prove the fit</h2>
        <p>
          Before a shortlist, a candidate can take a short,
          role-specific pre-assessment — about 250 seconds —
          that proves the skills the profile claims. The result
          rides on the profile as a score, and the score is one
          input to the match: a need can set a minimum score,
          and shortlists rank by it. A resume tells a story;
          the assessment is the evidence.
        </p>
      </section>

      <section>
        <h2>Two-way tracking — one state, both sides</h2>
        <p>
          An application moves through one state machine —
          <strong> Recommended → Applied → In Progress →
          Accepted / Rejected</strong> — and the candidate and
          the employer see the same state at the same time,
          with every transition recorded. No side works from a
          different version of the truth. On Accepted, the
          placement record hands off to payroll setup:
          employees to payroll, affiliates on their engagement
          terms, agentic services to x402.
        </p>
      </section>

      <section>
        <h2>Who placement serves — and who it doesn&apos;t</h2>
        <p>
          Hands-on placement concentrates on experienced
          professionals — roughly 27 and up, with five to seven
          years in the work. Early-career talent (roughly 19 to
          27, fresh out of university), particularly in
          white-collar roles exposed to AI replacement, is not
          this desk&apos;s environment: that segment is matched
          autonomously in the intents marketplace. One
          exception stands regardless of the band: AI/ML and
          highly experienced developers with five or more years
          at a major international firm are in placement scope.
        </p>
      </section>

      <section>
        <h2>How matching runs — intents and solvers</h2>
        <p>
          An employer&apos;s role requirement is expressed as an
          intent; candidate supply — human profiles and agentic
          services alike — responds as solvers; a settled match
          becomes the placement record. Today the solver behind
          that interface is the deterministic matcher described
          above, and the interface is the contract a smarter
          solver can be swapped behind. Stated plainly: NEAR AI
          attested inference is not yet live on this surface —
          it is credit-blocked (HTTP 402) — so nothing here
          claims an AI match. The match is arithmetic, labelled
          as such.
        </p>
      </section>

      <section>
        <h2>SURA — agentic guidance, both sides of the market</h2>
        <p>
          The best candidates rarely apply; their public work
          speaks first. <strong>SURA</strong> is the guidance
          layer over this marketplace, and it serves both
          sides. <strong>For employers</strong> — a person
          hiring, or an agent posting a skill listing — SURA
          reads a role requirement and answers with the state
          of the pool: how much supply exists, how it splits
          between people who applied and people who were
          sourced, and a recommendation that follows from
          that state. <strong>For candidates</strong>, SURA
          reads a profile against the open roles — roles
          defined by skill and by geo-requirement: remote,
          hybrid, or onsite — and answers with the roles the
          candidate qualifies for and the reason why, skill
          by skill.
        </p>
        <p>
          Two scores carry the guidance, and both show their
          arithmetic. A <strong>fit score</strong> (0–100)
          weighs skill coverage, role match, geo fit,
          experience, and assessment evidence for one role
          and one candidate. A{" "}
          <strong>switch-likelihood</strong> (0–100), carried
          by sourced candidates, weighs the public-activity
          signals a feed supplies — tenure, mobility,
          activity, recency — and names any signal it did
          not have. Both are published, deterministic
          heuristics (version 1): the same inputs always
          produce the same score, and neither is described
          as an AI judgement.
        </p>
        <p>
          Sourced candidates arrive through an explicit feed,
          never anonymously: every sourced profile carries
          its provenance — where it was observed, which feed
          supplied it, and the public signal that justified
          including it — and that provenance stays visible in
          every shortlist and solver answer where the
          candidate appears. Stated plainly: in this first
          version SURA does <em>not</em> crawl GitHub,
          LinkedIn, X, or any other source; feeds supply the
          profiles and the signals, and SURA computes over
          what they assert.
        </p>
        <p>
          <strong>The guidance learns.</strong> SURA&apos;s
          guidance incorporates a reinforcement-learning
          plane — the talent environment of our RL framework —
          that learns from interacting with this marketplace:
          every match, every placement, and every settled
          outcome is recorded and makes the guidance better
          for the next employer and the next candidate. For
          employers, matching and guidance improve with use.
          For candidates and contractors, guidance and fit
          improve with use. Engaging with the platform is
          what trains it. The learning is disciplined: a new
          guidance policy replaces the current one only when
          it beats it on held-out outcomes, through a gated
          promotion — the system never silently rewrites
          itself. And the current state, stated as plainly
          as the mechanism: today&apos;s guidance is the
          published heuristic above, the learning feed is
          recording outcomes now, and no trained policy has
          been promoted yet.
        </p>
      </section>

      <section>
        <h2>Categories beyond the desk</h2>
        <p>
          Hospitality and income commercial real estate are the
          focus categories, and software stack and blockchain
          technical development are staffed natively from the
          standing bench (India, Brazil, the United States,
          Spain, Costa Rica). Other fields — healthcare,
          scientific and pharmaceutical work among them — are
          not built natively: the need is routed, openly,
          through a placement agreement to an expert
          contractor-affiliate, and the fee is usually paid on
          placement.
        </p>
      </section>

      <section>
        <h2>Development &amp; Design — the project team</h2>
        <p>
          A third kind of work builds the asset in the first
          place. A developer who has secured the land needs a
          project team to turn a development into a hospitality
          asset: an <strong>architect</strong>, an{" "}
          <strong>interior designer</strong> (furnishings,
          appointments, wallcoverings, flooring), a{" "}
          <strong>lighting technology integrator</strong>, a{" "}
          <strong>wellness spa consultant</strong>, a{" "}
          <strong>CAD drafter</strong>, and a{" "}
          <strong>pre-sales broker</strong>.
        </p>
        <p>
          These profiles declare their category and their design
          domain — commercial architecture, luxury residential,
          hospitality resort design, wellness infrastructure —
          alongside the same focus as every other profile:
          hospitality or residential. A development need filters
          on that focus, and the team assembles category by
          category from independent contractors and agentic
          services alike. Project members refer each other: the
          architect refers the interior designer, who refers the
          spa consultant, and the referral chain is recorded.
        </p>
        <p>
          <em>Example — development:</em> a developer holds raw
          coastal land and a resort plan. The need is hospitality
          focus, resort design domain. The assembled team is a
          resort architect, an interior designer whose skills are
          flooring and wallcoverings, and a wellness spa
          consultant — staffed before the first operating role
          exists.
        </p>
      </section>

      <section>
        <h2>Software &amp; creative services</h2>
        <p>
          The same taxonomy carries two more kinds of expertise,
          embedded invisibly — the platform provides the
          capability; no firm&apos;s name is attached to it.
          When a project team adds{" "}
          <strong>graphic design &amp; web development</strong>,
          the matcher routes to the traditional software stack:
          graphic designers, web developers, software
          engineers. When it adds{" "}
          <strong>project visualization</strong>, it routes to
          visual assets: animators, drone operators, fine
          artists, filmmakers, creative intelligence advisors.
        </p>
        <p>
          <a href="https://uzemarkets.com/development-stack">
            See the full Development Stack
          </a>
        </p>
      </section>
    </main>
  );
}
