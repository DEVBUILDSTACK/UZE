import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Talent Placement | UZEmarkets",
  description:
    "UZEmarkets Talent Placement: the underwrite identifies the operational roles an asset already pays for — placement sources the people.",
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
      <p className="note" role="note">
        <strong>Demonstration Environment:</strong> this page is
        backed by synthetic fixtures. The live API is pending
        deployment.
      </p>
      <h1>Talent Placement</h1>
      <p className="lede">
        <strong>
          The underwrite names the role. Placement fills it.
        </strong>
      </p>
      <p>
        Every UZE Underwrite report reads the asset&apos;s own
        payroll lines and identifies the operational roles the
        property already pays for — property manager,
        maintenance, leasing, security. When a report flags a
        role, this desk sources a vetted person for it, matched
        against the payroll budget the underwrite calculated.
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
