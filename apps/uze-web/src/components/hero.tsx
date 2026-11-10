"use client";

/** Landing hero. Original form (2026-11-10): the Altitude grammar
 *  with a rotating HIADR focus word. Replaced the same evening by
 *  the Hero Correction directive: the rotating "Test and use ___"
 *  frame and the USP support line were killed as vague and
 *  jargon-bearing ("AssurativeV2" never appears in client-facing
 *  copy). The hero now states the pain and the solution directly:
 *  prove the P&L, get financed faster. */
import Link from "next/link";
import Wordmark from "@/components/wordmark";

export default function Hero() {
  return (
    <section className="hero">
      <span className="hero-pill">
        <Wordmark tone="white" />
      </span>
      <h1>Prove your property&apos;s P&amp;L. Get financed faster.</h1>
      <p className="hero-support">
        UZEmarkets is the information market where revenue, operating
        expenses, and net income are verified by AI, challenged on
        evidence, and trusted by lenders.
      </p>
      <div className="hero-ctas">
        <Link className="cta-primary" href="/onboard">
          Verify Your Property
        </Link>
        <a className="cta-quiet" href="https://podcast.uzemarkets.com">
          See our podcast
        </a>
      </div>
    </section>
  );
}
