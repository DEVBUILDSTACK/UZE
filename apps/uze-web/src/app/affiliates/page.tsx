import type { Metadata } from "next";
import { orderedAffiliates } from "@/lib/affiliates";

export const metadata: Metadata = {
  title: "Affiliate Directory | UZEmarkets",
  description:
    "UZEmarkets affiliate directory: the agencies and studios whose capabilities power the Development Stack, onboarded with their portfolios.",
};

/** Affiliate directory (owner tap, 2026-11-13). Sponsored
 * affiliates order first — the one effect sponsorship has.
 * Demonstration fixtures: the firms shown are invented
 * examples pinning the page shape until real onboarding
 * records render here, and the page says so. */
export default function AffiliatesPage() {
  const firms = orderedAffiliates();
  return (
    <main className="mk">
      <h1>Affiliate Directory</h1>
      <p className="lede">
        <strong>
          The firms behind the capabilities — onboarded once,
          deployed when a project requires them.
        </strong>
      </p>
      <p className="note">
        Demonstration directory: the firms below are sample
        affiliate pages showing the shape of an onboarded
        portfolio. Real listings replace them as affiliates
        complete onboarding.
      </p>
      {firms.map((f) => (
        <section key={f.slug}>
          <h2>
            <a href={`https://uzemarkets.com/affiliates/${f.slug}`}>
              {f.name}
            </a>
          </h2>
          <p>
            <em>{f.kind}</em>
            {f.sponsorshipStatus ? " · Sponsored listing" : ""}
          </p>
          <p>{f.summary}</p>
          <p>Specialties: {f.specialties.join(" · ")}</p>
        </section>
      ))}
      <section>
        <h2>Onboard your firm</h2>
        <p>
          Declare your services and portfolio once, and the
          Development Stack can route projects to your exact
          expertise.
        </p>
        <p>
          <a href="https://uzemarkets.com/alpha">
            Start affiliate onboarding
          </a>
        </p>
      </section>
    </main>
  );
}
