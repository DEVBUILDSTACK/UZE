import type { ReactNode } from "react";
import Link from "next/link";
import "./globals.css";

export const metadata = {
  title: "UZE",
  description: "Talent, tickets, touring and stay — one AI ecosystem.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <nav>
            <Link className="brand" href="/">
              UZE
            </Link>
            <Link href="/guidance">GIRA Guidance</Link>
            <Link href="/onboard">Create your profile</Link>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
