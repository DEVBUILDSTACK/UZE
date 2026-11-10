/** Site footer — the Altitude-pattern page bottom (James, 2026-11-10):
 *  a © line and a row of VISUAL SYMBOLS ONLY for the social branding —
 *  UZEmarkets Blog, X, Instagram, and WhatsApp for International
 *  Affiliates. The WhatsApp channel is gated by the UZE on-ramped
 *  Entity flow, so its symbol routes to the entity on-ramp (/onboard)
 *  rather than a public chat link. */
import Link from "next/link";
import Wordmark from "@/components/wordmark";

const SOCIALS = [
  {
    label: "UZEmarkets Blog",
    href: "https://blog.uzemarkets.com",
    external: true,
    glyph: (
      <>
        <rect x="9.4" y="9" width="5.2" height="11" rx="2.6" />
        <circle cx="12" cy="4.6" r="2.3" />
      </>
    ),
  },
  {
    label: "X.com",
    href: "https://x.com/UZEmarkets_fyi",
    external: true,
    glyph: (
      <path d="M17.9 3H21l-6.78 7.74L22.2 21h-6.24l-4.89-6.4L5.47 21H2.34l7.25-8.28L2.2 3h6.4l4.42 5.85L17.9 3Zm-1.1 16.13h1.73L7.7 4.77H5.85L16.8 19.13Z" />
    ),
  },
  {
    label: "Instagram",
    href: "https://instagram.com/uzemarkets",
    external: true,
    glyph: (
      <>
        <rect
          x="3"
          y="3"
          width="18"
          height="18"
          rx="5.5"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        />
        <circle
          cx="12"
          cy="12"
          r="4"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        />
        <circle cx="17.2" cy="6.8" r="1.3" />
      </>
    ),
  },
  {
    label:
      "WhatsApp — International Affiliates (gated by the UZE on-ramped Entity flow)",
    href: "/onboard",
    external: false,
    glyph: (
      <path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.9 9.9 0 0 0 4.79 1.22h.01c5.46 0 9.9-4.45 9.9-9.91 0-2.65-1.03-5.14-2.9-7.01A9.83 9.83 0 0 0 12.04 2Zm0 18.03h-.01a8.2 8.2 0 0 1-4.19-1.15l-.3-.18-3.12.82.83-3.04-.2-.31a8.2 8.2 0 0 1-1.26-4.38c0-4.54 3.7-8.24 8.25-8.24 2.2 0 4.27.86 5.82 2.42a8.18 8.18 0 0 1 2.41 5.83c0 4.54-3.7 8.23-8.23 8.23Zm4.52-6.16c-.25-.12-1.47-.72-1.69-.81-.23-.08-.39-.12-.56.13-.16.24-.64.8-.78.97-.14.16-.29.18-.54.06-.25-.13-1.05-.38-1.99-1.23-.74-.66-1.23-1.47-1.38-1.72-.14-.25-.01-.38.11-.51.11-.11.25-.29.37-.43.12-.15.16-.25.25-.41.08-.17.04-.31-.02-.43-.06-.13-.56-1.35-.77-1.84-.2-.48-.41-.42-.56-.43h-.48c-.17 0-.43.06-.66.31-.22.25-.86.85-.86 2.07 0 1.22.89 2.4 1.01 2.56.13.17 1.75 2.67 4.23 3.74.59.26 1.05.41 1.41.52.6.19 1.13.16 1.56.1.48-.07 1.47-.58 1.74-1.14.27-.56.27-1.04.19-1.14-.08-.1-.23-.16-.48-.28Z" />
    ),
  },
];

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="social-row">
        {SOCIALS.map((s) =>
          s.external ? (
            <a
              key={s.label}
              className="social-btn"
              href={s.href}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={s.label}
              title={s.label}
            >
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                {s.glyph}
              </svg>
            </a>
          ) : (
            <Link
              key={s.label}
              className="social-btn"
              href={s.href}
              aria-label={s.label}
              title={s.label}
            >
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                {s.glyph}
              </svg>
            </Link>
          ),
        )}
      </div>
      <p className="copyright">
        © 2026 <Wordmark />
      </p>
    </footer>
  );
}
