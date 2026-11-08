import { notFound } from "next/navigation";
import { fetchMicroRegion, fetchPulse, humanize, pulseUrl } from "@/lib/compose";

export const dynamic = "force-dynamic";

export default async function MicroRegionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const region = await fetchMicroRegion(id);
  if (!region) notFound();
  const pulse = await fetchPulse(id);

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Place",
    identifier: region.id,
    name: region.label,
    address: {
      "@type": "PostalAddress",
      addressLocality: region.metro,
      addressRegion: region.region,
    },
  };

  // The Content Desk Dataset: the /pulse payload itself, verbatim,
  // plus its distribution pointer — what a crawler ingests here is
  // exactly what the API serves (D4).
  const pulseJsonLd = pulse
    ? {
        ...pulse,
        distribution: {
          "@type": "DataDownload",
          contentUrl: pulseUrl(region.id),
        },
      }
    : null;

  return (
    <main className="mk">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      {pulseJsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(pulseJsonLd) }}
        />
      )}
      <p className="note">
        UZEMARKETS · micro-region — the analytical unit of the
        marketplace. Every analyzed property becomes a comparable in
        its micro-region dataset at settlement.
      </p>
      <h1>{region.label}</h1>
      <p className="lede">
        {region.metro} · {region.region} — {region.specCount} spec
        {region.specCount === 1 ? "" : "s"} · {region.comparableCount}{" "}
        settled comparable{region.comparableCount === 1 ? "" : "s"}
      </p>

      {pulse && (
        <>
          <h2>Pulse — the Content Desk dataset</h2>
          <p className="note">
            Live from marketplace records
            {pulse.temporalCoverage
              ? ` · coverage ${pulse.temporalCoverage}`
              : ""}
            . The same payload is served as JSON at{" "}
            <code>/api/v1/micro-regions/{region.id}/pulse</code> — agent
            action: {pulse.agent_action}
          </p>
          <table>
            <thead>
              <tr>
                <th>Measure</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Specs posted</td>
                <td>{pulse.variableMeasured.spec_count}</td>
              </tr>
              <tr>
                <td>Settled comparables</td>
                <td>{pulse.variableMeasured.comparable_count}</td>
              </tr>
              <tr>
                <td>Settled volume</td>
                <td>
                  {pulse.variableMeasured.settled_volume_usdc.toLocaleString()}{" "}
                  USDC
                </td>
              </tr>
            </tbody>
          </table>
          {pulse.pulse_data ? (
            <table>
              <thead>
                <tr>
                  <th>Period aggregate</th>
                  <th>Data</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(pulse.pulse_data).map(([period, data]) => (
                  <tr key={period}>
                    <td>{period}</td>
                    <td>
                      <code>{JSON.stringify(data)}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="note">
              Period aggregates (prior 30d / 90d, 18m / 36m lookbacks) are
              populated by the data pipeline; the measured counts above
              are computed from live records, never estimated.
            </p>
          )}
        </>
      )}

      <h2>Specs in this micro-region</h2>
      {region.specs.length === 0 ? (
        <p className="note">No specs posted yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Work product</th>
              <th>Property</th>
              <th>Budget</th>
              <th>Bids</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {region.specs.map((spec) => (
              <tr key={spec.id}>
                <td>
                  <a href={`/specs/${spec.id}`}>
                    {humanize(spec.workProduct)}
                  </a>
                </td>
                <td>
                  {spec.assetContext.brandAffiliation ??
                    humanize(spec.assetContext.propertyType)}{" "}
                  · {spec.assetContext.doorCount} doors
                </td>
                <td>
                  {spec.budgetMinUsdc.toLocaleString()}–
                  {spec.budgetMaxUsdc.toLocaleString()} USDC
                </td>
                <td>{spec.bidCount}</td>
                <td>{spec.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
