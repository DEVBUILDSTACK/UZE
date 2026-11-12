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
    </main>
  );
}
