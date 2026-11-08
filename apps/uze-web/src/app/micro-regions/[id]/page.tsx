import { notFound } from "next/navigation";
import { fetchMicroRegion, humanize } from "@/lib/compose";

export const dynamic = "force-dynamic";

export default async function MicroRegionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const region = await fetchMicroRegion(id);
  if (!region) notFound();

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

  return (
    <main className="mk">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
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
