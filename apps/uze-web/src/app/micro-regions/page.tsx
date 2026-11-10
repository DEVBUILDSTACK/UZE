import { fetchMicroRegions } from "@/lib/compose";
import { MICRO_REGIONS_SNAPSHOT } from "@/lib/micro-regions-snapshot";
import {
  MARKET_BY_SLUG,
  MARKETS,
  withPlaceholders,
} from "@/lib/markets";

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

  return (
    <main className="mk">
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
          for a spec. Forward your financials to UZE Underwrite.
          Harness Underwriting Super Intelligence to verify
          P&amp;L against regional comps, run an NOI valuation,
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
