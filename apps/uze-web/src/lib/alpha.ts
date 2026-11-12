/** Alpha signup list client — UZEguidance priced markets.
 *
 * Posts to the compose API (POST /api/v1/alpha/signups), the same
 * NEXT_PUBLIC_COMPOSE_API_URL pattern as the builder panel. The
 * server is the authority on validation and on the honored window;
 * the checks here only save a round trip. If the API is unreachable
 * the caller must say so — a signup is never faked client-side. */

const COMPOSE_API =
  process.env.NEXT_PUBLIC_COMPOSE_API_URL ?? "http://localhost:8100";

export type AlphaLevel = "builder" | "affiliate" | "affiliate_onramped";
export type AlphaChain = "solana" | "near" | "robinhood" | "ink" | "lightlink";
export type OnrampLane = "tradelayer" | "siglayer";

export interface AlphaSignup {
  level: AlphaLevel;
  name: string;
  email: string;
  entity_name?: string;
  kyb_attested: boolean;
  kyc_attested: boolean;
  chain: AlphaChain;
  wallet_address: string;
  onramp_lane?: OnrampLane;
}

export interface AlphaSignupResult {
  id: string;
  level: string;
  chain: string;
  window_state: "pre_window" | "in_window" | "post_window";
  in_honored_window: boolean;
  honored: boolean;
  verification_status: string;
  duplicate?: boolean;
}

const SOLANA = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
const EVM = /^0x[0-9a-fA-F]{40}$/;
const NEAR_IMPLICIT = /^[0-9a-f]{64}$/;
const NEAR_NAMED = /^(([a-z0-9]+[-_])*[a-z0-9]+\.)*([a-z0-9]+[-_])*[a-z0-9]+$/;

export function validWallet(chain: AlphaChain, address: string): boolean {
  const a = address.trim();
  if (chain === "solana") return SOLANA.test(a);
  if (chain === "near")
    return NEAR_IMPLICIT.test(a) || (a.length >= 2 && a.length <= 64 && NEAR_NAMED.test(a));
  return EVM.test(a);
}

export const CHAIN_HINTS: Record<AlphaChain, string> = {
  solana: "Solana address — base58, 32–44 characters.",
  near: "NEAR account (name.near) or the 64-character implicit address.",
  robinhood: "Robinhood Chain EVM address — 0x, 42 characters.",
  ink: "Ink EVM address — 0x, 42 characters.",
  lightlink: "LightLink EVM address — 0x, 42 characters.",
};

export async function submitAlphaSignup(
  body: AlphaSignup,
): Promise<
  | { ok: true; result: AlphaSignupResult }
  | { ok: false; kind: "offline" | "rejected"; message: string }
> {
  try {
    const res = await fetch(`${COMPOSE_API}/api/v1/alpha/signups`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (res.ok) {
      return { ok: true, result: (await res.json()) as AlphaSignupResult };
    }
    let message = `The list refused the signup (${res.status}).`;
    try {
      const data = (await res.json()) as { detail?: string };
      if (data.detail) message = data.detail;
    } catch {
      /* keep the status message */
    }
    return { ok: false, kind: "rejected", message };
  } catch {
    return {
      ok: false,
      kind: "offline",
      message:
        "The alpha intake is not reachable from this page yet — your signup was NOT recorded. The list itself is open; try again once the intake service is live, or write to UZEmarket@uzemarkets.com.",
    };
  }
}
