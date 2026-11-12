import type { ReactNode } from "react";
import SiteNav from "@/components/site-nav";
import SiteFooter from "@/components/site-footer";
import Providers from "@/components/providers";
import "./globals.css";

export const metadata = {
  metadataBase: new URL("https://uzemarkets.com"),
  title: "UZE",
  description:
    "UZEmarkets — the information market where offerings are tested and used.",
  openGraph: {
    type: "website",
    siteName: "UZEmarkets",
    title: "UZEmarkets — Information Markets",
    description:
      "Test and use Hospitality, Income, Agriculture, Development and Resource in one information market.",
    images: [
      {
        url: "/og-uzemarkets.png",
        width: 1200,
        height: 630,
        alt: "UZEmarkets — Information Markets",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "UZEmarkets — Information Markets",
    description:
      "Test and use Hospitality, Income, Agriculture, Development and Resource in one information market.",
    images: ["/og-uzemarkets.png"],
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <SiteNav />
          {children}
          <SiteFooter />
        </Providers>
      </body>
    </html>
  );
}
