import { fetchMicroRegion, fetchMicroRegions } from "@/lib/compose";

export const dynamic = "force-dynamic";

export default async function SpecsIndexPage() {
  const regions = (await fetchMicroRegions()) ?? [];
  const details = await Promise.all(
    regions.map((r) => fetchMicroRegion(r.id)),
  );
  const specs = details.flatMap((d) => d?.specs ?? []);

  return (
    <main className="mk">
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
