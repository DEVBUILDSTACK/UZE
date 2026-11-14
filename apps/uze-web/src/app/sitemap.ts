import type { MetadataRoute } from "next";
import { ENV } from "@/lib/env";
import {
  fetchMicroRegion,
  fetchMicroRegions,
  fetchSpecBids,
} from "@/lib/compose";
import {
  MICRO_REGION_DETAILS_SNAPSHOT,
  MICRO_REGIONS_SNAPSHOT,
} from "@/lib/micro-regions-snapshot";

export const dynamic = "force-dynamic";

/** The marketplace sitemap. Built from the compose API so every
 *  spec, micro-region and talent profile the agent surface knows
 *  is crawlable on the human surface (D4). If the API has no records
 *  (down, unconfigured, or its database not yet seeded) the sitemap
 *  falls back to the Content Desk snapshot regions rather than
 *  failing or shrinking to the static routes. */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = ENV.baseUrl.replace(/\/$/, "");
  const entries: MetadataRoute.Sitemap = [
    { url: `${base}/` },
    { url: `${base}/micro-regions` },
    { url: `${base}/specs` },
    { url: `${base}/devpartner/en` },
    { url: `${base}/devpartner/pt-BR` },
    { url: `${base}/devpartner/pt-PT` },
    { url: `${base}/devpartner/es` },
  ];
  try {
    const liveRegions = await fetchMicroRegions();
    const snapshotMode = !liveRegions?.length;
    const regions = snapshotMode
      ? MICRO_REGIONS_SNAPSHOT
      : (liveRegions ?? []);
    const talent = new Set<string>();
    for (const region of regions) {
      entries.push({ url: `${base}/micro-regions/${region.id}` });
      const detail =
        (await fetchMicroRegion(region.id)) ??
        (snapshotMode ? MICRO_REGION_DETAILS_SNAPSHOT[region.id] : undefined);
      for (const spec of detail?.specs ?? []) {
        entries.push({ url: `${base}/specs/${spec.id}` });
        const bids = (await fetchSpecBids(spec.id)) ?? [];
        for (const bid of bids) talent.add(bid.bidderAccount);
      }
    }
    for (const handle of talent) {
      entries.push({ url: `${base}/talent/${handle}` });
    }
  } catch {
    // Static entries only — see docstring.
  }
  return entries;
}
