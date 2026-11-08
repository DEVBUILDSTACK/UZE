import { headers } from "next/headers";
import { redirect } from "next/navigation";
import type { Locale } from "@/lib/devpartner";

export const dynamic = "force-dynamic";

/** /devpartner — locale gateway. Serves the portal in the visitor's
 *  browser locale: /devpartner/pt-BR for Portuguese, /devpartner/es
 *  for Spanish, /devpartner/en otherwise. The locale routes
 *  themselves are public and ungated. */
export default async function DevPartnerIndex() {
  const accept = ((await headers()).get("accept-language") ?? "").toLowerCase();
  const locale: Locale = accept.startsWith("pt")
    ? "pt-BR"
    : accept.startsWith("es")
      ? "es"
      : "en";
  redirect(`/devpartner/${locale}`);
}
