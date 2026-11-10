/** Site header + hamburger drawer — mirrors the mockup's collapsible
 *  Command & Control navigation pattern: brand wordmark up top, the
 *  full menu (sections + active and pilot markets) behind the
 *  hamburger. */
"use client";

import { useState } from "react";
import Link from "next/link";
import Wordmark from "@/components/wordmark";
import { usePathname } from "next/navigation";

// Active Markets — the Hospitality & Income CRE markets. Each link
// lands on the Content Desk index filtered to that market's
// micro-regions; micro-regions exist only in the active markets.
const ACTIVE_MARKETS = [
  {
    label: "South Florida / Miami",
    href: "https://podcast.uzemarkets.com/micro-regions?market=south-florida",
  },
  {
    label: "Washington DC / Baltimore",
    href: "https://podcast.uzemarkets.com/micro-regions?market=mid-atlantic",
  },
  {
    label: "Costa Rica",
    href: "https://podcast.uzemarkets.com/micro-regions?market=costa-rica",
  },
];

const PILOT_MARKETS = [
  "Rio de Janeiro",
  "São Paulo",
  "Barcelona",
];

export default function SiteNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const [lastPath, setLastPath] = useState(pathname);

  // Close the drawer whenever navigation lands on a new page.
  if (pathname !== lastPath) {
    setLastPath(pathname);
    setOpen(false);
  }

  const close = () => setOpen(false);

  return (
    <>
      <header className="site-header">
        <div className="bar">
          <button
            className="menu-btn"
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? "✕" : "☰"}
          </button>
          <Link className="brand" href="/" onClick={close}>
            <Wordmark />
          </Link>
          <Link className="quick" href="/onboard" onClick={close}>
            Create profile
          </Link>
        </div>
      </header>

      <div
        className={`drawer-overlay${open ? " open" : ""}`}
        onClick={close}
        aria-hidden={!open}
      />
      <aside className={`drawer${open ? " open" : ""}`} aria-hidden={!open}>
        <div className="drawer-head">
          <span className="brand">
            <Wordmark />
          </span>
          <button className="menu-btn" aria-label="Close menu" onClick={close}>
            ✕
          </button>
        </div>
        <nav>
          <Link href="/" onClick={close}>
            Home
          </Link>
          <Link href="/guidance" onClick={close}>
            GIRA Guidance
          </Link>
          <Link href="/devpartner" onClick={close}>
            Dev Docs
          </Link>
          <Link href="/onboard" onClick={close}>
            Create your profile
          </Link>
        </nav>
        <h3>Active Markets</h3>
        <ul className="markets active">
          <li>
            <a href="https://podcast.uzemarkets.com" onClick={close}>
              Hospitality &amp; Income CRE
            </a>
          </li>
          {ACTIVE_MARKETS.map((m) => (
            <li key={m.label}>
              <a href={m.href} onClick={close}>
                {m.label}
              </a>
            </li>
          ))}
        </ul>
        <h3>Pilot Markets</h3>
        <ul className="markets">
          {PILOT_MARKETS.map((m) => (
            <li key={m}>
              <Link href="/guidance" onClick={close}>
                {m}
              </Link>
            </li>
          ))}
        </ul>
        <p className="drawer-foot">Talent · Tickets · Touring · Stay</p>
      </aside>
    </>
  );
}
