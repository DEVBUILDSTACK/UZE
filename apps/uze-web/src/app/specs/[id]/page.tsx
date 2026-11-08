import { notFound } from "next/navigation";
import AgentPanel from "@/components/agent-panel";
import {
  epochDate,
  fetchMicroRegion,
  fetchSpec,
  fetchSpecBids,
  humanize,
} from "@/lib/compose";

export const dynamic = "force-dynamic";

function buildJsonLd(
  spec: NonNullable<Awaited<ReturnType<typeof fetchSpec>>>,
  regionLabel: string,
) {
  return {
    "@context": "https://schema.org",
    "@type": "Demand",
    identifier: spec.id,
    name: `${humanize(spec.workProduct)} — ${regionLabel}`,
    description: Object.values(spec.deliverable).join(" · "),
    itemOffered: {
      "@type": "Service",
      name: humanize(spec.workProduct),
      areaServed: regionLabel,
    },
    priceSpecification: {
      "@type": "PriceSpecification",
      minPrice: spec.budgetMinUsdc,
      maxPrice: spec.budgetMaxUsdc,
      priceCurrency: "USD",
    },
    availabilityStarts: epochDate(spec.availableFrom),
    availabilityEnds: epochDate(spec.availableUntil),
  };
}

export default async function SpecPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const spec = await fetchSpec(id);
  if (!spec) notFound();
  const bids = (await fetchSpecBids(id)) ?? [];
  const region = await fetchMicroRegion(spec.microRegionId);
  const regionLabel = region?.label ?? spec.microRegionId;
  const asset = spec.assetContext;

  return (
    <main className="mk">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(buildJsonLd(spec, regionLabel)),
        }}
      />
      <p className="note">
        UZEMARKETS · read-only human surface — the agent API serves this
        same spec as JSON at <code>/api/v1/specs/{spec.id}</code>
      </p>
      <h1>
        {humanize(spec.workProduct)} ·{" "}
        {asset.brandAffiliation ?? humanize(asset.propertyType)} ·{" "}
        {asset.doorCount} doors
      </h1>
      <p className="lede">{Object.values(spec.deliverable).join(" · ")}</p>

      <div className="card">
        <dl>
          <dt>Micro-region</dt>
          <dd>
            <a href={`/micro-regions/${spec.microRegionId}`}>{regionLabel}</a>
          </dd>
          <dt>Budget</dt>
          <dd>
            {spec.budgetMinUsdc.toLocaleString()}–
            {spec.budgetMaxUsdc.toLocaleString()} USDC
          </dd>
          <dt>Domain</dt>
          <dd>{humanize(spec.domain)}</dd>
          <dt>Track (HIADR)</dt>
          <dd>
            {spec.assetSubclass
              ? `${spec.assetSubclass} — ${
                  {
                    H: "Hospitality",
                    I: "Income",
                    A: "Agriculture",
                    D: "Development",
                    R: "Resource",
                  }[spec.assetSubclass] ?? spec.assetSubclass
                }`
              : "—"}
            {spec.targetArea
              ? spec.targetArea.type === "Radius"
                ? ` · Radius ${spec.targetArea.radiusMiles ?? ""} mi`
                : ` · ${spec.targetArea.type}`
              : ""}
          </dd>
          <dt>Property</dt>
          <dd>
            {humanize(asset.propertyType)} · {asset.doorCount} doors ·{" "}
            {humanize(asset.acquisitionStage)}
          </dd>
          <dt>Engagement</dt>
          <dd>
            {spec.onSiteDays ?? 0} days on site · {spec.remoteDays ?? 0} days
            remote · tier {spec.tier}
          </dd>
          <dt>Availability</dt>
          <dd>
            {epochDate(spec.availableFrom)} → {epochDate(spec.availableUntil)}
          </dd>
          <dt>Posted by</dt>
          <dd>
            {spec.posterAccount} ({spec.posterKind})
          </dd>
          <dt>Status</dt>
          <dd>{spec.status}</dd>
        </dl>
      </div>

      <AgentPanel spec={spec} regionLabel={regionLabel} bidCount={bids.length} />

      <h2>Bids ({bids.length})</h2>
      {bids.length === 0 ? (
        <p className="note">No bids yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Bidder</th>
              <th>Kind</th>
              <th>Amount</th>
              <th>ETA</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {bids.map((bid) => (
              <tr key={bid.id}>
                <td>
                  <a href={`/talent/${bid.bidderAccount}`}>
                    {bid.bidderAccount}
                  </a>
                </td>
                <td>{bid.bidderKind}</td>
                <td>{bid.amountUsdc.toLocaleString()} USDC</td>
                <td>{bid.etaHours != null ? `${bid.etaHours} h` : "—"}</td>
                <td>{bid.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
