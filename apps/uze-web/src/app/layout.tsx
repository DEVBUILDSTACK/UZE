import type { ReactNode } from "react";

export const metadata = {
  title: "UZE",
  description: "Talent, tickets, touring and stay — one AI ecosystem.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
