import type { SpecView } from "@/lib/compose";

/** AgentPanel — the human (UI) surface of the dual-surface agent
 *  architecture. The panel is branded by the spec's HIADR track:
 *  GIRA for the A/D/R tracks (Agriculture, Development, Resource),
 *  SURA for HiCRE (Hospitality, Income). It is a stateful guide
 *  tied to the spec's Entity: it explains, from the spec's own
 *  fields, what data the agent works from and what happens next.
 *  The same assessments are served headlessly to autonomous agents
 *  at /api/v1/agents/{gira,sura}/underwrite (x401 + x402). */

const ADR = new Set(["A", "D", "R"]);

export default function AgentPanel({
  spec,
  regionLabel,
  bidCount,
}: {
  spec: SpecView;
  regionLabel: string;
  bidCount: number;
}) {
  const isGira = spec.assetSubclass != null && ADR.has(spec.assetSubclass);
  const agent = isGira ? "GIRA" : "SURA";
  const tracks = isGira ? "A N R & D" : "HiCRE";
  const endpoint = isGira
    ? "/api/v1/agents/gira/underwrite"
    : "/api/v1/agents/sura/underwrite";

  return (
    <section className={`agent-panel ${isGira ? "gira" : "sura"}`}>
      <h2>
        {agent} <span className="agent-tracks">· {tracks} guidance</span>
      </h2>
      {spec.entityId ? (
        <p className="note">
          Guidance for Entity <code>{spec.entityId}</code> — the
          attested identity this engagement runs under.
        </p>
      ) : null}

      {isGira ? (
        <>
          <p>
            GIRA works this {spec.assetSubclass} track from partner
            data cached in our ProviderSnapshot store — never from a
            live partner API. For a polygon like this one, the inputs
            are ADV Americas&apos; soil chemistry and crop
            suitability, BDCS feedlot and feed optimization data, and
            Effatha&apos;s satellite treatment records, each staged,
            reviewed and approved before it can be consumed.
          </p>
          <p>
            Target area:{" "}
            {spec.targetArea
              ? spec.targetArea.type === "Polygon"
                ? "GeoJSON polygon (required for A/D/R)"
                : `${spec.targetArea.type} ${spec.targetArea.radiusMiles ?? ""} mi`
              : "—"}
            {spec.subterraneanContext
              ? ` · Subterranean context on file (${Object.keys(spec.subterraneanContext).length} fields: soil depth, resources, water)`
              : " · Subterranean context not yet on file — required before underwriting"}
            .
          </p>
        </>
      ) : (
        <>
          <p>
            SURA works this HiCRE spec from the market itself: a{" "}
            {spec.budgetMinUsdc.toLocaleString()}–
            {spec.budgetMaxUsdc.toLocaleString()} USDC budget band in{" "}
            {regionLabel}, {bidCount} bid{bidCount === 1 ? "" : "s"} so
            far, and every settled engagement in the micro-region
            written back as a comparable the next assessment stands on.
          </p>
          <p>
            Ask SURA for an underwriting assessment before selecting a
            bid: it reads the spec, the bids and the comparables, and
            answers with structured data — the same answer the
            headless surface gives autonomous agents.
          </p>
        </>
      )}

      <p className="note">
        Headless surface: <code>POST {endpoint}</code> — x401 identity
        attestation, x402 metered per query.
      </p>
    </section>
  );
}
