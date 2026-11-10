import Link from "next/link";
import Hero from "@/components/hero";

/** Public front door (James, 2026-11-10): clean landing page in the
 *  POD/blog coloration, Altitude-pattern hero - rotating HIADR focus,
 *  constant USP support line, one primary CTA (Create your profile,
 *  the entity on-ramp). Evaluation-first: anyone can look around;
 *  profile creation is an invitation, not a gate. */
export default function Home() {
  return (
    <main>
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
            <a href="https://blog.uzemarkets.com">
              The Content Desk — micro-regions, pulses and specs
            </a>
          </li>
        </ul>
      </nav>
    </main>
  );
}
