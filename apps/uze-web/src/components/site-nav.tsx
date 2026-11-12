/** Site header + hamburger drawer — mirrors the mockup's collapsible
 *  Command & Control navigation pattern: brand wordmark up top, the
 *  full menu (sections + active and pilot markets) behind the
 *  hamburger. */
"use client";

import { useState } from "react";
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
          <a className="brand" href="https://uzemarkets.com" aria-label="UZEmarkets — home">
            <Wordmark />
          </a>
          <a className="quick" href="https://uzemarkets.com/onboard">
            Create profile
          </a>
        </div>
      </header>

      <div
        className={`drawer-overlay${open ? " open" : ""}`}
        onClick={close}
        aria-hidden={!open}
      />
      <aside className={`drawer${open ? " open" : ""}`} aria-hidden={!open}>
        <div className="drawer-head">
          <a className="brand" href="https://uzemarkets.com" aria-label="UZEmarkets — home">
            <Wordmark />
          </a>
          <button className="menu-btn" aria-label="Close menu" onClick={close}>
            ✕
          </button>
        </div>
        <nav>
          <a href="https://uzemarkets.com" onClick={close}>
            Home
          </a>
          <a href="https://uzemarkets.com/guidance" onClick={close}>
            GIRA Guidance
          </a>
          <a className="underwrite" href="https://uzemarkets.com/underwrite" onClick={close}>
            UZE Underwrite
          </a>
          <a href="https://devpartner.uzemarkets.com" onClick={close}>
            Dev Docs
          </a>
          <a href="https://dealfi.uzemarkets.com" onClick={close}>
            DealFi
          </a>
          <a href="https://uzemarkets.com/onboard" onClick={close}>
            Create your profile
          </a>
        </nav>
        <h3>Active Markets</h3>
        <ul className="markets active">
          <li>
            <a href="https://podcast.uzemarkets.com/micro-regions" onClick={close}>
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
              <a href="https://uzemarkets.com/guidance" onClick={close}>
                {m}
              </a>
            </li>
          ))}
        </ul>
        <p className="drawer-foot">Talent · Tickets · Touring · Stay</p>
      </aside>
    </>
  );
}
