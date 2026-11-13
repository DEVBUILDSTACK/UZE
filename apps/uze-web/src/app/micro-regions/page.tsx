import type { Metadata } from "next";
import { fetchMicroRegions } from "@/lib/compose";
import { ENV } from "@/lib/env";
import { MICRO_REGIONS_SNAPSHOT } from "@/lib/micro-regions-snapshot";
import {
  MARKET_BY_SLUG,
  MARKETS,
  withPlaceholders,
} from "@/lib/markets";

export const metadata: Metadata = {
  title: "Micro-regions | UZEmarkets",
  description:
    "UZEmarkets micro-regions: the analytical unit of the marketplace for Hospitality & Income CRE — every micro-region with its spec and comparable counts. Brickell, not \"Miami\"; Bethesda, not \"DC metro\".",
};

export const dynamic = "force-dynamic";

export default async function MicroRegionsIndexPage({
  searchParams,
}: {
  searchParams: Promise<{ market?: string }>;
}) {
  const { market: marketSlug } = await searchParams;
  const market = marketSlug ? MARKET_BY_SLUG[marketSlug] : undefined;

  const live = await fetchMicroRegions();
  const all = withPlaceholders(live ?? MICRO_REGIONS_SNAPSHOT);
  const regions = market
    ? all.filter((r) => market.regionIds.includes(r.id))
    : all;

  // ItemList over exactly the rows rendered below — same source,
  // same filter (live API when reachable, Content Desk snapshot
  // otherwise); Place items mirror the /micro-regions/[id] JSON-LD.
  const base = ENV.baseUrl.replace(/\/$/, "");
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: market
      ? `${market.label} — micro-regions`
      : "UZEmarkets micro-regions",
    url: market
      ? `${base}/micro-regions?market=${market.slug}`
      : `${base}/micro-regions`,
    itemListElement: regions.map((region, i) => ({
      "@type": "ListItem",
      position: i + 1,
      item: {
        "@type": "Place",
        identifier: region.id,
        name: region.label,
        url: `${base}/micro-regions/${region.id}`,
        address: {
          "@type": "PostalAddress",
          addressLocality: region.metro,
          addressRegion: region.region,
        },
      },
    })),
  };

  return (
    <main className="mk">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <p className="note">
        UZEMARKETS · Hospitality &amp; Income CRE — micro-regions, the
        analytical unit of the marketplace: Brickell, not
        &quot;Miami&quot;; Bethesda, not &quot;DC metro&quot;.
      </p>
      <h1>{market ? market.label : "Micro-regions"}</h1>
      <p className="note">
        Markets: <a href="/micro-regions">All</a>
        {MARKETS.map((m) => (
          <span key={m.slug}>
            {" · "}
            <a href={`/micro-regions?market=${m.slug}`}>{m.label}</a>
          </span>
        ))}
      </p>
      <div className="uw-banner">
        <p>
          <strong>Have a T-12 or P&amp;L?</strong> Don&apos;t wait
          for a spec. Forward your hospitality or income property
          financials to UZE Underwrite. Harness Underwriting Super
          Intelligence to verify P&amp;L against regional comps,
          unlock cost recovery, and generate a verified PDF in
          minutes.
        </p>
        <a className="uw-btn" href="/underwrite">
          Upload Financials
        </a>
      </div>
      {market?.note && <p className="note">{market.note}</p>}
      {!live && (
        <p className="note">
          Index snapshot from the Content Desk dataset — live records
          replace it when the composition API is connected.
        </p>
      )}
      <table>
        <thead>
          <tr>
            <th>Micro-region</th>
            <th>Metro</th>
            <th>Specs</th>
            <th>Comparables</th>
          </tr>
        </thead>
        <tbody>
          {regions.map((region) => (
            <tr key={region.id}>
              <td>
                <a href={`/micro-regions/${region.id}`}>{region.label}</a>
              </td>
              <td>
                {region.metro} · {region.region}
              </td>
              <td>{region.specCount}</td>
              <td>{region.comparableCount}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
