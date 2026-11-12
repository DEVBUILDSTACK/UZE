import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";

/** /partners — the short route named in the DevPartner directive.
 *  The portal itself lives under /devpartner (locale gateway +
 *  /en, /pt-BR, /es, /pt-PT); this route hands off to it. */
export default function PartnersAlias() {
  redirect("/devpartner");
}
