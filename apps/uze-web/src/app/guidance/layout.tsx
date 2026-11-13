import type { ReactNode } from "react";

/** Metadata lives here, not in page.tsx: the guidance page is a
 *  client component and cannot export metadata (same pattern as
 *  src/app/alpha/layout.tsx). */
export const metadata = {
  title: "GIRA Guidance | UZEmarkets",
  description:
    "GIRA Guidance: the UZE concierge for talent, tickets, touring and stay — browse experiences by category and ask GIRA. Preview for evaluation; live listings arrive with the full service launch.",
};

export default function GuidanceLayout({
  children,
}: {
  children: ReactNode;
}) {
  return children;
}
