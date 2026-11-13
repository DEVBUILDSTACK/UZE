/** Client for the UZEMARKETS composition layer (services/compose) —
 *  the Sprint 1.5 CRE marketplace backend.
 *
 *  D4: one backend, two projections. The pages under app/specs,
 *  app/talent and app/micro-regions render exactly the fields the
 *  agent JSON API serves; nothing is renamed or reshaped here.
 *  Read-only: this client only GETs. Interactive human UI is
 *  Sprint 2; the agent surface is the interactive one today.
 */

const COMPOSE_API = process.env.COMPOSE_API_URL ?? "https://uze-compose-api.onrender.com";

export interface SpecView {
  id: string;
  kind: string;
  posterKind: string;
  posterAccount: string;
  domain: string;
  workProduct: string;
  deliverable: Record<string, string>;
  microRegionId: string;
  assetContext: {
    propertyType: string;
    doorCount: number;
    brandAffiliation?: string | null;
    acquisitionStage: string;
  };
  assetSubclass: string | null;
  entityId: string | null;
  affiliateId: string | null;
  executionEnvironment: string | null;
  agentAttestation: string | null;
  countryCode: string | null;
  macroDistressExit: boolean | null;
  targetArea: { type: string; [key: string]: unknown } | null;
  subterraneanContext: Record<string, unknown> | null;
  onSiteDays: number | null;
  remoteDays: number | null;
  budgetMinUsdc: number;
  budgetMaxUsdc: number;
  availableFrom: number;
  availableUntil: number;
  tier: string;
  referringPartner: string | null;
  status: string;
  chainIntentRef: string | null;
  bidCount: number;
}

export interface BidView {
  id: string;
  intentId: string;
  bidderAccount: string;
  bidderKind: string;
  amountUsdc: number;
  etaHours: number | null;
  onSiteDays: number | null;
  remoteDays: number | null;
  payload: Record<string, unknown>;
  status: string;
  chainBidRef: string | null;
}

export interface MicroRegionView {
  id: string;
  label: string;
  metro: string;
  region: string;
  specCount: number;
  comparableCount: number;
}

export interface MicroRegionDetail extends MicroRegionView {
  specs: SpecView[];
}

export interface TalentView {
  account: string;
  kind: string;
  bidCount: number;
  totalBidUsdc: number;
  bids: BidView[];
}

async function get<T>(path: string): Promise<T | null> {
  // Degradation contract: an unreachable or erroring composition API
  // yields null, never a thrown error — every consuming page renders
  // its empty / snapshot / not-found state instead of a server error.
  // (2026-11-10: the blog surface 500'd on Vercel, where no compose
  // API listens on the default loopback URL.)
  try {
    const res = await fetch(`${COMPOSE_API}${path}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const fetchSpec = (id: string) =>
  get<SpecView>(`/api/v1/specs/${encodeURIComponent(id)}`);

export const fetchSpecBids = (id: string) =>
  get<BidView[]>(`/api/v1/specs/${encodeURIComponent(id)}/bids`);

export const fetchMicroRegions = () =>
  get<MicroRegionView[]>(`/api/v1/micro-regions`);

export const fetchMicroRegion = (id: string) =>
  get<MicroRegionDetail>(`/api/v1/micro-regions/${encodeURIComponent(id)}`);

export const fetchTalent = (handle: string) =>
  get<TalentView>(`/api/v1/talent/${encodeURIComponent(handle)}`);

export interface PulseView {
  "@context": string;
  "@type": string;
  name: string;
  temporalCoverage: string | null;
  variableMeasured: {
    spec_count: number;
    comparable_count: number;
    settled_volume_usdc: number;
  };
  pulse_data: Record<string, unknown> | null;
  agent_action: string;
}

export const fetchPulse = (id: string) =>
  get<PulseView>(`/api/v1/micro-regions/${encodeURIComponent(id)}/pulse`);

/** Absolute URL of the pulse endpoint — the Dataset's download. */
export const pulseUrl = (id: string) =>
  `${COMPOSE_API}/api/v1/micro-regions/${encodeURIComponent(id)}/pulse`;

/** Epoch seconds -> YYYY-MM-DD (the wire carries unix timestamps). */
export function epochDate(epochSeconds: number): string {
  return new Date(epochSeconds * 1000).toISOString().slice(0, 10);
}

/** "operating_budget" -> "Operating budget" for display only. */
export function humanize(slug: string): string {
  const words = slug.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}
