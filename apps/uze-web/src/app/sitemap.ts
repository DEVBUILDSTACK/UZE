import type { MetadataRoute } from "next";
import { ENV } from "@/lib/env";
import {
  fetchMicroRegion,
  fetchMicroRegions,
  fetchSpecBids,
} from "@/lib/compose";

export const dynamic = "force-dynamic";

/** The marketplace sitemap. Built from the compose API so every
 *  spec, micro-region and talent profile the agent surface knows
 *  is crawlable on the human surface (D4). If the API is down the
 *  sitemap degrades to the static routes rather than failing. */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = ENV.baseUrl.replace(/\/$/, "");
  const entries: MetadataRoute.Sitemap = [
    { url: `${base}/` },
    { url: `${base}/micro-regions` },
    { url: `${base}/specs` },
  ];
  try {
    const regions = (await fetchMicroRegions()) ?? [];
    const talent = new Set<string>();
    for (const region of regions) {
      entries.push({ url: `${base}/micro-regions/${region.id}` });
      const detail = await fetchMicroRegion(region.id);
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
