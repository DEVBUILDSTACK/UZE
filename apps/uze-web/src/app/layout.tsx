import type { ReactNode } from "react";

export const metadata = {
  title: "UZE",
  description: "Create your UZE profile in 20 seconds.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
