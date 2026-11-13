import type { Metadata } from "next";
import {
  fetchMicroRegion,
  fetchMicroRegions,
  humanize,
} from "@/lib/compose";
import { ENV } from "@/lib/env";

export const metadata: Metadata = {
  title: "Specs | UZEmarkets",
  description:
    "UZEmarkets specifications: assessment and advisory specs posted against micro-regions in the Talent marketplace — the read-only index of every posted spec and its status.",
};

export const dynamic = "force-dynamic";

export default async function SpecsIndexPage() {
  const regions = (await fetchMicroRegions()) ?? [];
  const details = await Promise.all(
    regions.map((r) => fetchMicroRegion(r.id)),
  );
  const specs = details.flatMap((d) => d?.specs ?? []);

  // ItemList over exactly the rows rendered below, from the same
  // fetch; Demand items mirror the /specs/[id] JSON-LD shape.
  const labelByRegion = new Map(
    details.flatMap((d) => (d ? [[d.id, d.label] as const] : [])),
  );
  const base = ENV.baseUrl.replace(/\/$/, "");
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: "UZEmarkets specs",
    url: `${base}/specs`,
    itemListElement: specs.map((spec, i) => ({
      "@type": "ListItem",
      position: i + 1,
      item: {
        "@type": "Demand",
        identifier: spec.id,
        name: `${humanize(spec.workProduct)} — ${
          labelByRegion.get(spec.microRegionId) ?? spec.microRegionId
        }`,
        url: `${base}/specs/${spec.id}`,
      },
    })),
  };

  return (
    <main className="mk">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <p className="note">UZEMARKETS · specifications — read-only</p>
      <h1>Specs</h1>
      {specs.length === 0 ? (
        <p className="note">No specs posted yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Spec</th>
              <th>Micro-region</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {specs.map((spec) => (
              <tr key={spec.id}>
                <td>
                  <a href={`/specs/${spec.id}`}>{spec.id.slice(0, 8)}…</a>
                </td>
                <td>{spec.microRegionId}</td>
                <td>{spec.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
