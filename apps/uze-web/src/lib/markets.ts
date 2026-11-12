/**
 * Markets — the Active Markets of the Hospitality & Income CRE
 * surface (James, 2026-11-10). Micro-regions exist ONLY in the active
 * markets; each market link in the navigation lands on the Content
 * Desk index filtered to that market's micro-regions, and every
 * market view looks the same way.
 *
 * These markets are Hospitality & Income only — nothing to do with
 * A/NR/D. The analysis attached to their micro-regions is the HiCRE
 * financial analysis: backward-looking (historical) operating
 * expenses, and forward-looking operating expenses and revenues.
 *
 * Costa Rica's micro-regions are PLACEHOLDERS (James, 2026-11-10):
 * the capital (San José), the two largest Pacific-coast hospitality
 * markets (Tamarindo, Jacó) and the largest eastern city (Puerto
 * Limón) — structure only, no data, analysis in preparation.
 */
import type { MicroRegionDetail, MicroRegionView } from "@/lib/compose";

export interface MarketDef {
  slug: string;
  /** Navigation label, as James named the markets. */
  label: string;
  regionIds: string[];
  /** Shown on the market's filtered index view. */
  note?: string;
}

export const MARKETS: MarketDef[] = [
  {
    slug: "south-florida",
    label: "South Florida / Miami",
    regionIds: [
      "miami-brickell",
      "miami-aventura",
      "fort-lauderdale",
      "orlando-kissimmee",
      "tampa-fl",
    ],
  },
  {
    slug: "mid-atlantic",
    label: "Washington DC / Baltimore",
    regionIds: [
      "bethesda-cbd",
      "arlington-va",
      "baltimore-city",
      "baltimore-nw",
      "towson",
    ],
  },
  {
    slug: "costa-rica",
    label: "Costa Rica",
    regionIds: ["san-jose-cr", "tamarindo", "jaco", "puerto-limon"],
    note: "Placeholder micro-regions — coverage in preparation. The analysis for this market is Hospitality & Income CRE: backward-looking and forward-looking operating expenses and revenues.",
  },
];

export const MARKET_BY_SLUG: Record<string, MarketDef> = Object.fromEntries(
  MARKETS.map((m) => [m.slug, m]),
);

export const MARKET_BY_REGION_ID: Record<string, MarketDef> =
  Object.fromEntries(
    MARKETS.flatMap((m) => m.regionIds.map((id) => [id, m] as const)),
  );

/** Placeholder micro-regions (Costa Rica) — structure only. Merged
 *  into the index and detail views alongside live/snapshot records;
 *  ids that ever arrive from the live API take precedence. */
export const PLACEHOLDER_REGIONS: MicroRegionView[] = [
  {
    id: "san-jose-cr",
    label: "San José",
    metro: "San José",
    region: "Costa Rica",
    specCount: 0,
    comparableCount: 0,
  },
  {
    id: "tamarindo",
    label: "Tamarindo",
    metro: "Guanacaste",
    region: "Costa Rica",
    specCount: 0,
    comparableCount: 0,
  },
  {
    id: "jaco",
    label: "Jacó",
    metro: "Puntarenas",
    region: "Costa Rica",
    specCount: 0,
    comparableCount: 0,
  },
  {
    id: "puerto-limon",
    label: "Puerto Limón",
    metro: "Limón",
    region: "Costa Rica",
    specCount: 0,
    comparableCount: 0,
  },
];

export const PLACEHOLDER_REGION_IDS = new Set(
  PLACEHOLDER_REGIONS.map((r) => r.id),
);

export const PLACEHOLDER_DETAILS: Record<string, MicroRegionDetail> =
  Object.fromEntries(
    PLACEHOLDER_REGIONS.map((r) => [r.id, { ...r, specs: [] }]),
  );

/** Append placeholder regions whose ids are not already present. */
export function withPlaceholders(
  regions: MicroRegionView[],
): MicroRegionView[] {
  const present = new Set(regions.map((r) => r.id));
  return [
    ...regions,
    ...PLACEHOLDER_REGIONS.filter((r) => !present.has(r.id)),
  ];
}
