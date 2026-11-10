/** Site header + hamburger drawer — mirrors the mockup's collapsible
 *  Command & Control navigation pattern: brand wordmark up top, the
 *  full menu (sections + active and pilot markets) behind the
 *  hamburger. */
"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const ACTIVE_MARKETS = [
  "South Florida / Miami",
  "Washington DC / Baltimore",
  "Costa Rica",
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
            UZE<span className="gira">GIRA</span>
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
            UZE<span className="gira">GIRA</span>
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
          <Link href="/onboard" onClick={close}>
            Create your profile
          </Link>
        </nav>
        <h3>Active Markets</h3>
        <ul className="markets active">
          {ACTIVE_MARKETS.map((m) => (
            <li key={m}>
              <Link href="/guidance" onClick={close}>
                {m}
              </Link>
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
