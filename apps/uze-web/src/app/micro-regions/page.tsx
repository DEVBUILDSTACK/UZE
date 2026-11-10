import { fetchMicroRegions } from "@/lib/compose";
import { MICRO_REGIONS_SNAPSHOT } from "@/lib/micro-regions-snapshot";

export const dynamic = "force-dynamic";

export default async function MicroRegionsIndexPage() {
  const live = await fetchMicroRegions();
  const regions = live ?? MICRO_REGIONS_SNAPSHOT;

  return (
    <main className="mk">
      <p className="note">
        UZEMARKETS · micro-regions — the analytical unit of the
        marketplace: Brickell, not &quot;Miami&quot;; Bethesda, not
        &quot;DC metro&quot;.
      </p>
      <h1>Micro-regions</h1>
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
