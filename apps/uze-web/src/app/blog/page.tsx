import type { Metadata } from "next";
import { HouseEmail } from "@/components/site-blocks";

export const metadata: Metadata = {
  title: "Blog — Alpha & Active Market Financings | UZEmarkets",
  description:
    "The UZEmarkets blog placeholder: alpha research and active market financing coverage, in preparation. Our weekly content lives on the Saturday POD at podcast.uzemarkets.com.",
};

/** The blog host is RESERVED for the future written publication
 *  (James's ruling, 2026-11-10): the multi-tenant article blog —
 *  house writing plus affiliate tenant blogs — which is not yet
 *  written or built. This page is its placeholder, under the
 *  name James gave it: "Blog — Alpha & Active Market
 *  Financings." The weekly content result lives on the podcast
 *  host. */
export default function BlogReservedPage() {
  return (
    <main className="mk">
      <h1>Blog</h1>
      <p className="lede">Alpha &amp; Active Market Financings</p>
      <p>
        Our written publication is in preparation. Alpha research
        and active market financing coverage from UZEmarkets and
        our affiliates will publish here.
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
