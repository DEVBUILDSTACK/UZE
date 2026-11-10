import type { Metadata } from "next";
import { HouseEmail } from "@/components/site-blocks";

export const metadata: Metadata = {
  title: "Blog — in preparation | UZEmarkets",
  description:
    "The UZEmarkets written publication is in preparation. Our weekly content lives on the Saturday POD at podcast.uzemarkets.com.",
};

/** The blog host is RESERVED for the future written publication
 *  (James's ruling, 2026-11-10): the multi-tenant article blog —
 *  house writing plus affiliate tenant blogs — which is not yet
 *  written or built. The Content Desk no longer displays here;
 *  the weekly content result lives on the podcast host. */
export default function BlogReservedPage() {
  return (
    <main className="mk">
      <h1>The UZEmarkets Blog</h1>
      <p className="lede">
        Our written publication is in preparation. Articles and
        market writing from UZEmarkets and our affiliates will
        publish here.
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
