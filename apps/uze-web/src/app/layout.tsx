import type { ReactNode } from "react";
import SiteNav from "@/components/site-nav";
import "./globals.css";

export const metadata = {
  title: "UZE",
  description: "Talent, tickets, touring and stay — one AI ecosystem.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SiteNav />
        {children}
      </body>
    </html>
  );
}
