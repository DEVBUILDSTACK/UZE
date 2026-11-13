import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Development Stack | UZEmarkets",
  description:
    "The UZEmarkets turnkey development stack: architecture and project execution, visualization, software, and time-based compute — assembled from one onboarding.",
};

/** The Development Stack (owner tap, 2026-11-13): the
 * turnkey offer for a development — Money (the underwrite) +
 * Talent (the project team and project side) + Visuals (the
 * Creative Intelligence Agency) + Software (the Institutional
 * Software Partner). Partner and affiliate names stay in the
 * background by the owner's standing positioning rule: the
 * page sells capabilities under generic titles only.
 * Compute rental is presented honestly: the tiers are the
 * program's shape; container provisioning is not live yet,
 * and the page routes the reader to onboarding instead of a
 * checkout. No prices appear on this page — participation
 * levels are market-bid (see UZEguidance). */
export default function DevelopmentStackPage() {
  return (
    <main className="mk">
      <p className="note" role="note">
        <strong>Demonstration Environment:</strong> this page is
        backed by synthetic fixtures. The live API is pending
        deployment.
      </p>
      <h1>The Development Stack</h1>
      <p className="lede">
        <strong>
          Bring the land and the capital. The stack assembles
          the rest.
        </strong>
      </p>
      <p>
        A development moves through one pipeline: the
        underwrite prices it, the project team designs it, the
        project side builds it, visualization pre-sells it, and
        software operates it. Every capability below is a
        talent or affiliate category inside the same
        marketplace — a developer hires the bundle, not five
        separate agencies.
      </p>

      <section>
        <h2>1. Architecture &amp; execution — hire the team</h2>
        <p>
          The project team: architect, interior designer,
          lighting technology integrator, wellness spa
          consultant, CAD drafter, pre-sales broker. The project
          side that executes: development manager, general
          contractor, construction project manager, entitlement
          consultant, development finance analyst. A project
          roster reads plainly — <em>we need: 1 architect, 1
          general contractor, 1 development finance analyst</em>{" "}
          — and the developer can engage it as a bundled team,
          staged by the project lifecycle: acquisition &amp;
          entitlement, design &amp; architecture, construction
          execution, operations stabilization.
        </p>
        <p>
          <a href="https://uzemarkets.com/talent/placement">
            See Talent Placement
          </a>
        </p>
      </section>

      <section>
        <h2>2. Visualization — the Creative Intelligence Agency</h2>
        <p>
          Drone footage, motion graphics, 3D renders, and
          explainer animation, produced by the marketplace&apos;s
          creative talent — animators, drone operators, fine
          artists, filmmakers — supervised by creative
          direction. A developer looking at raw land does not
          only want an underwriting report; they want to see
          what a world-class architect could do with that view.
          Visualization is how the project pre-sells.
        </p>
      </section>

      <section>
        <h2>3. Software — the Institutional Software Partner</h2>
        <p>
          The traditional stack, built by specialized software
          engineers: booking engines, tenant portals, property
          management dashboards. When a project requires
          traditional web development, the platform routes to
          the software categories in its taxonomy; when it
          requires visual assets, it routes to the creative
          ones. The capability is the platform&apos;s; the
          firms behind it stay in the background.
        </p>
      </section>

      <section>
        <h2>4. Compute rental — time-based, by the tier</h2>
        <p>
          Rendering and development environments are rented by
          time, in four tiers: <strong>Day · Week · Month ·
          Quarter</strong>. Container provisioning opens with
          the compute rental program; until then there is no
          checkout on this page — developers and affiliates
          reserve their place through onboarding, and rental
          billing runs on the platform&apos;s metered rails
          when the program opens.
        </p>
      </section>

      <section>
        <h2>Launch the full stack</h2>
        <p>
          Affiliates onboard once — declaring their services,
          their portfolio, and their team — and the stack can
          deploy them whenever a project requires their exact
          expertise.
        </p>
        <p>
          <a href="https://uzemarkets.com/alpha">
            Launch Your Full Project Stack
          </a>{" "}
          ·{" "}
          <a href="https://uzemarkets.com/affiliates">
            Browse the affiliate directory
          </a>
        </p>
      </section>
    </main>
  );
}
