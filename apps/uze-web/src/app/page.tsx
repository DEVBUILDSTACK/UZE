import Link from "next/link";
import Hero from "@/components/hero";

/** Site identity JSON-LD. layout.tsx carries metadata (title,
 *  OpenGraph, Twitter) but no structured data, so the Organization
 *  and WebSite entities are declared here, on the home page only. */
const SITE_JSON_LD = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://uzemarkets.com/#organization",
      name: "UZEmarkets",
      url: "https://uzemarkets.com",
      email: "desk@uzemarkets.com",
      description:
        "UZEmarkets — the information market where offerings are tested and used. An autonomous financial intelligence desk for income commercial real estate: UZE Underwrite, UZE Assign, UZE Auction, UZE Research, and the Talent marketplace.",
      logo: "https://uzemarkets.com/og-uzemarkets.png",
    },
    {
      "@type": "WebSite",
      "@id": "https://uzemarkets.com/#website",
      name: "UZEmarkets",
      url: "https://uzemarkets.com",
      publisher: { "@id": "https://uzemarkets.com/#organization" },
    },
  ],
};

/** Public front door (James, 2026-11-10): clean landing page in the
 *  POD/blog coloration, Altitude-pattern hero - rotating HIADR focus,
 *  constant USP support line, one primary CTA (Create your profile,
 *  the entity on-ramp). Evaluation-first: anyone can look around;
 *  profile creation is an invitation, not a gate. */
export default function Home() {
  return (
    <main>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(SITE_JSON_LD) }}
      />
      <Hero />
      <p className="hero-gira">
        Meet GIRA, your concierge for what&apos;s on, where it&apos;s
        happening, and how to be there.
      </p>
      <nav>
        <ul className="home-links">
          <li>
            <Link href="/site/hicre">
              For owners, brokers and lenders — HiCRE
            </Link>
          </li>
          <li>
            <Link href="/site/anrd">
              For landowners, developers and syndicates — Agriculture,
              Natural Resources &amp; Development
            </Link>
          </li>
          <li>
            <Link href="/guidance">See how GIRA guidance works</Link>
          </li>
          <li>
            <a href="https://uzemarkets.com/micro-regions">
              The Content Desk — micro-regions, pulses and specs
            </a>
          </li>
        </ul>
      </nav>
    </main>
  );
}
