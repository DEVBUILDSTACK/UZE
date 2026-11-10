"use client";

/** Landing hero (James, 2026-11-10) - the Altitude grammar applied to
 *  UZEmarkets: one fixed headline frame, a rotating area of focus
 *  (the five HIADR tracks), one constant USP support line, and a
 *  single primary CTA. "Run ___ from one global business account"
 *  becomes "Test and use ___ in one information market." */
import { useEffect, useState } from "react";
import Link from "next/link";

const FOCUS = ["Hospitality", "Income", "Agriculture", "Development", "Resource"];

export default function Hero() {
  const [i, setI] = useState(0);
  const [out, setOut] = useState(false);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const id = setInterval(() => {
      setOut(true);
      setTimeout(() => {
        setI((v) => (v + 1) % FOCUS.length);
        setOut(false);
      }, 380);
    }, 2800);
    return () => clearInterval(id);
  }, []);

  return (
    <section className="hero">
      <span className="hero-pill">UZEmarkets</span>
      <h1>
        Test and use{" "}
        <span className={`hero-rot${out ? " out" : ""}`}>{FOCUS[i]}</span>
        <br />
        in one information market.
      </h1>
      <p className="hero-support">
        Buyer demand shapes what&apos;s offered. Every offering is proven
        genuine through AssurativeV2, and every use makes it better.
      </p>
      <div className="hero-ctas">
        <Link className="cta-primary" href="/onboard">
          Create your profile
        </Link>
        <a className="cta-quiet" href="https://blog.uzemarkets.com">
          Read the blog
        </a>
      </div>
    </section>
  );
}
