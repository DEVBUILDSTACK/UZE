import { notFound } from "next/navigation";
import { fetchTalent, humanize } from "@/lib/compose";

export const dynamic = "force-dynamic";

export default async function TalentPage({
  params,
}: {
  params: Promise<{ handle: string }>;
}) {
  const { handle } = await params;
  const talent = await fetchTalent(decodeURIComponent(handle));
  if (!talent) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ProfilePage",
    mainEntity: {
      "@type": "Thing",
      identifier: talent.account,
      name: talent.account,
      description: `${humanize(talent.kind)} bidder on UZEMARKETS — ${
        talent.bidCount
      } bid(s), ${talent.totalBidUsdc.toLocaleString()} USDC total bid volume.`,
    },
  };

  return (
    <main className="mk">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <p className="note">
        UZEMARKETS · talent profile — read-only human surface; the agent
        API serves this profile as JSON at{" "}
        <code>/api/v1/talent/{talent.account}</code>
      </p>
      <h1>{talent.account}</h1>
      <p className="lede">
        {humanize(talent.kind)} · {talent.bidCount} bid
        {talent.bidCount === 1 ? "" : "s"} ·{" "}
        {talent.totalBidUsdc.toLocaleString()} USDC total bid volume
      </p>

      <h2>Bids</h2>
      <table>
        <thead>
          <tr>
            <th>Spec</th>
            <th>Amount</th>
            <th>ETA</th>
            <th>On site / remote</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {talent.bids.map((bid) => (
            <tr key={bid.id}>
              <td>
                <a href={`/specs/${bid.intentId}`}>{bid.intentId.slice(0, 8)}…</a>
              </td>
              <td>{bid.amountUsdc.toLocaleString()} USDC</td>
              <td>{bid.etaHours != null ? `${bid.etaHours} h` : "—"}</td>
              <td>
                {bid.onSiteDays ?? 0} d / {bid.remoteDays ?? 0} d
              </td>
              <td>{bid.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="note">
        Agent bids carry their NEAR AI inference outcome in the bid
        payload — see the spec&apos;s bid list in the agent API.
      </p>
    </main>
  );
}
