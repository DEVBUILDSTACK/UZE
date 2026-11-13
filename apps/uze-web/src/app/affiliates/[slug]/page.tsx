import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { findAffiliate } from "@/lib/affiliates";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const firm = findAffiliate(slug);
  return {
    title: firm
      ? `${firm.name} | UZEmarkets Affiliates`
      : "Affiliate | UZEmarkets",
    description: firm?.summary,
  };
}

/** The white-label affiliate page (owner tap, 2026-11-13):
 * an onboarded firm's agency page inside UZEmarkets — its
 * portfolio, its services, its team categories, and the hire
 * CTA. It lives under /affiliates/[slug], never a root-level
 * slug: root routes belong to the platform's own surfaces,
 * and tenant instances are a separate topology. The JSON-LD
 * carries Schema.org ProfessionalService + Person so agent
 * crawlers can cite the portfolio. Demonstration fixture —
 * the firm is invented and the page says so. */
export default async function AffiliatePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const firm = findAffiliate(decodeURIComponent(slug));
  if (!firm) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ProfessionalService",
    name: firm.name,
    description: firm.summary,
    url: `https://uzemarkets.com/affiliates/${firm.slug}`,
    makesOffer: firm.services.map((s) => ({
      "@type": "Offer",
      itemOffered: { "@type": "Service", name: s },
    })),
    founder: { "@type": "Person", name: firm.name, jobTitle: firm.kind },
  };

  return (
    <main className="mk">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <p className="note">
        UZEmarkets affiliate page — demonstration firm; real
        listings render from onboarding records.
      </p>
      <h1>{firm.name}</h1>
      <p className="lede">
        <strong>{firm.kind}</strong>
      </p>
      <p>{firm.summary}</p>

      <section>
        <h2>Portfolio</h2>
        <p>{firm.mediaNote}</p>
        {firm.projects.map((p) => (
          <p key={p.name}>
            <strong>{p.name}</strong> — {p.location}, {p.year} ·{" "}
            {p.type}
          </p>
        ))}
        {firm.awards.map((a) => (
          <p key={a.name}>
            🏆 {a.name} ({a.year}) — {a.organization}
          </p>
        ))}
        <p>Specialties: {firm.specialties.join(" · ")}</p>
      </section>

      <section>
        <h2>Services</h2>
        <p>{firm.services.join(" · ")}</p>
      </section>

      <section>
        <h2>Hire this firm</h2>
        <p>
          Route your next development to {firm.name} through
          the Development Stack — one onboarding, the whole
          team.
        </p>
        <p>
          <a href="https://uzemarkets.com/development-stack">
            Hire this Firm for your next Development
          </a>{" "}
          ·{" "}
          <a href="https://uzemarkets.com/alpha">
            Request a Consultation
          </a>
        </p>
      </section>
    </main>
  );
}
