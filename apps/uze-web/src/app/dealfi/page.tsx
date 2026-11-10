import type { Metadata } from "next";
import { HouseEmail } from "@/components/site-blocks";

export const metadata: Metadata = {
  title: "DealFi — Regional Market Deals & Financings | UZEmarkets",
  description:
    "DealFi: the UZEmarkets regional market deal and financing page — preliminary, in preparation.",
};

/** DealFi (James's naming, 2026-11-10): dealfi.uzemarkets.com is,
 *  preliminarily, the regional market deal and financing page.
 *  This is its placeholder while the page is prepared. It
 *  replaces the short-lived blog placeholder: the blog host was
 *  renamed to the DealFi host before any blog content existed. */
export default function DealFiPage() {
  return (
    <main className="mk">
      <h1>DealFi</h1>
      <p className="lede">Regional Market Deals &amp; Financings</p>
      <p>
        This page is in preparation. DealFi will carry the
        regional market deal and financing coverage for the
        UZEmarkets markets — the deals, the financings, and the
        verified numbers behind them.
      </p>
      <p>
        Until then, our weekly content lives on the Saturday POD:{" "}
        <a href="https://podcast.uzemarkets.com">
          podcast.uzemarkets.com
        </a>
        .
      </p>
      <HouseEmail />
    </main>
  );
}
