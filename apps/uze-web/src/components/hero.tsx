"use client";

/** Landing hero — the unified rotating block (James's tap,
 *  2026-11-11 late). Three states rotate as ONE block each:
 *  badge, headline, support, circular bullets and CTAs are wrapped
 *  in a single container and move together — nothing animates
 *  independently. Motion spec (Altitude grammar): exit fades and
 *  slides up (y −20px, scale .98), enter fades in from below
 *  (y +20px, scale .98), 0.8s on cubic-bezier(0.4, 0, 0.2, 1),
 *  6s dwell per state. The 01 · 02 · 03 indicator under the CTAs
 *  jumps to a state on click and resets the dwell. The ambient
 *  pulse lives on the background field only. Under
 *  prefers-reduced-motion the rotation and pulses stop; the
 *  indicator still switches states instantly.
 *
 *  Copy provenance: state 01 is the Nov 10 Hero Correction text
 *  verbatim; states 02 and 03 are assembled from copy already
 *  live on the Content Desk / underwrite surfaces, approved by
 *  James as a set on 2026-11-11. */
import { useEffect, useState } from "react";
import Link from "next/link";
import Wordmark from "@/components/wordmark";

const DWELL_MS = 6000;
const TRANSITION_MS = 800;

type HeroState = {
  badge: "wordmark" | string;
  h1: string;
  support: string;
  bullets: [string, string, string];
  primary: { label: string; href: string; external?: boolean };
  quiet: { label: string; href: string; external?: boolean };
};

const STATES: HeroState[] = [
  {
    badge: "wordmark",
    h1: "Prove your property's P&L. Get financed faster.",
    support:
      "UZEmarkets is the information market where revenue, operating expenses, and net income are verified by AI, challenged on evidence, and trusted by lenders.",
    bullets: ["Verified by AI", "Challenged on evidence", "Trusted by lenders"],
    primary: { label: "Verify Your Property", href: "/onboard" },
    quiet: { label: "See our podcast", href: "https://podcast.uzemarkets.com", external: true },
  },
  {
    badge: "UZE UNDERWRITE",
    h1: "Verify P&L against regional comps.",
    support:
      "Harness Underwriting Super Intelligence to verify P&L against regional comps, unlock cost recovery, and generate a verified PDF in minutes.",
    bullets: ["T-12 in", "Comps checked", "Verified PDF out"],
    primary: { label: "Upload Financials", href: "/underwrite" },
    quiet: { label: "Explore micro-regions", href: "https://uzemarkets.com/micro-regions", external: true },
  },
  {
    badge: "UZE ACTIVE MARKETS",
    h1: "Brickell, not “Miami.”",
    support:
      "Micro-regions, the analytical unit of the marketplace: Brickell, not “Miami”; Bethesda, not “DC metro.”",
    bullets: ["South Florida / Miami", "Washington DC / Baltimore", "Costa Rica"],
    primary: { label: "See the Micro-Regions", href: "https://uzemarkets.com/micro-regions", external: true },
    quiet: { label: "Verify Your Property", href: "/onboard" },
  },
];

function Cta({
  cta,
  className,
}: {
  cta: HeroState["primary"];
  className: string;
}) {
  if (cta.external) {
    return (
      <a className={className} href={cta.href}>
        {cta.label}
      </a>
    );
  }
  return (
    <Link className={className} href={cta.href}>
      {cta.label}
    </Link>
  );
}

export default function Hero() {
  const [active, setActive] = useState(0);
  const [incoming, setIncoming] = useState<number | null>(null);
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const onChange = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  // Dwell: after 6s fully visible, begin the transition to the
  // next state. Manual jumps clear this timer via the deps.
  useEffect(() => {
    if (reduced || incoming !== null) return;
    const t = setTimeout(
      () => setIncoming((active + 1) % STATES.length),
      DWELL_MS,
    );
    return () => clearTimeout(t);
  }, [active, incoming, reduced]);

  // Transition: the incoming block animates in while the current
  // block animates out over the same 0.8s window; then commit.
  useEffect(() => {
    if (incoming === null) return;
    if (reduced) {
      setActive(incoming);
      setIncoming(null);
      return;
    }
    const t = setTimeout(() => {
      setActive(incoming);
      setIncoming(null);
    }, TRANSITION_MS);
    return () => clearTimeout(t);
  }, [incoming, reduced]);

  const goTo = (n: number) => {
    if (n !== active && incoming === null) setIncoming(n);
  };

  const shown = incoming ?? active;

  return (
    <section className="hero">
      {/* Ambient pulse (background only): the rings emanate on
          their loop while the whole field breathes on the spec's
          4s ambient cycle — scale 1→1.02, opacity .8→1. */}
      <div className="hero-pulse-field" aria-hidden="true">
        <span className="hero-ring" />
        <span className="hero-ring r2" />
        <span className="hero-ring r3" />
      </div>

      {/* All three blocks share one grid cell, so the stage height
          is always the tallest block: no layout shift on rotation,
          on desktop or mobile. Only the active block is visible;
          during a transition the outgoing and incoming blocks
          animate together as one move. */}
      <div className="hero-stage">
        {STATES.map((s, i) => {
          const cls =
            i === active && incoming === null
              ? "hero-block is-active"
              : i === active && incoming !== null
                ? "hero-block is-exiting"
                : i === incoming
                  ? "hero-block is-entering"
                  : "hero-block is-idle";
          return (
            <div className={cls} key={s.h1} aria-hidden={i !== shown}>
              {s.badge === "wordmark" ? (
                <span className="hero-pill">
                  <Wordmark tone="white" />
                </span>
              ) : (
                <span className="hero-pill">
                  <span className="wm-uze">UZE</span>
                  {s.badge.slice(3)}
                </span>
              )}
              <h1>{s.h1}</h1>
              <p className="hero-support">{s.support}</p>
              <div className="hero-chips">
                {s.bullets.map((b) => (
                  <span className="hero-chip" key={b}>
                    {b}
                  </span>
                ))}
              </div>
              <div className="hero-ctas">
                <Cta cta={s.primary} className="cta-primary" />
                <Cta cta={s.quiet} className="cta-quiet" />
              </div>
            </div>
          );
        })}
      </div>

      <div className="hero-dots" role="tablist" aria-label="Hero statements">
        {STATES.map((s, i) => (
          <button
            key={s.badge === "wordmark" ? "01" : s.badge}
            type="button"
            role="tab"
            aria-selected={i === shown}
            aria-label={`Statement ${i + 1}: ${s.h1}`}
            className={i === shown ? "hero-dot is-active" : "hero-dot"}
            onClick={() => goTo(i)}
          >
            {String(i + 1).padStart(2, "0")}
          </button>
        ))}
      </div>
    </section>
  );
}
