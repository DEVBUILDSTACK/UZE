import type { Metadata } from "next";
import { redirect } from "next/navigation";

export const metadata: Metadata = {
  title: "Partners — DevPartner Portal | UZEmarkets",
  description:
    "Partners at UZEmarkets: the DevPartner portal — partner software-stack implementations, the ingestion API reference, partner schemas, and API-key requests. This short route hands off to the localized portal.",
};

export const dynamic = "force-dynamic";

/** /partners — the short route named in the DevPartner directive.
 *  The portal itself lives under /devpartner (locale gateway +
 *  /en, /pt-BR, /es, /pt-PT); this route hands off to it. */
export default function PartnersAlias() {
  redirect("/devpartner");
}
