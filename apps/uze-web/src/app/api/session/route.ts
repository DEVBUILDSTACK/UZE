// app/api/session/route.ts
// Coinbase Onramp session-token route, ADAPTED from Fundio's
// src/app/api/session/route.ts (treasury port, 2026-11-11,
// owner's override). Same mechanism — a CDP JWT
// (@coinbase/cdp-sdk/auth) exchanged at /onramp/v1/token for
// a session token — with the owner's corrections applied:
// credentials are read per-request (never at module load),
// and when CDP keys are not configured the route answers an
// honest 503 ("not configured") instead of a 500 or a dummy-
// secret success path. Real keys arrive via the environment
// (CDP_API_KEY_ID / CDP_API_KEY_SECRET), never via the repo.
import "server-only";
import { generateJwt } from "@coinbase/cdp-sdk/auth";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function normalizeSecret(raw: string): string {
  const fixed = raw.replace(/\\n/g, "\n").trim();
  if (fixed.startsWith("-----BEGIN") && fixed.includes("END")) return fixed; // PEM
  return fixed.replace(/\s+/g, ""); // base64
}

type Addr = { address: string; blockchains: readonly ("base")[] };

function normalizeAddresses(input: unknown): Addr[] {
  if (!input) return [];
  if (Array.isArray(input)) {
    return input
      .map((x) =>
        typeof x === "string"
          ? { address: x, blockchains: ["base"] as const }
          : {
              address: String((x as { address?: unknown })?.address ?? ""),
              blockchains:
                Array.isArray((x as { blockchains?: unknown })?.blockchains) &&
                ((x as { blockchains: unknown[] }).blockchains.length ?? 0)
                  ? ((x as { blockchains: ("base")[] }).blockchains)
                  : (["base"] as const),
            },
      )
      .filter((a) => /^0x[a-fA-F0-9]{40}$/.test(a.address));
  }
  return [];
}

export async function POST(req: Request) {
  try {
    const id = process.env.CDP_API_KEY_ID;
    const rawSecret = process.env.CDP_API_KEY_SECRET;
    if (!id || !rawSecret) {
      return NextResponse.json(
        {
          error: "coinbase_onramp_not_configured",
          detail:
            "CDP_API_KEY_ID / CDP_API_KEY_SECRET are not set in this deployment's environment. The on-ramp activates when the owner configures the CDP keys; no session token can be minted until then.",
        },
        { status: 503 },
      );
    }

    const body = await req.json().catch(() => ({}));
    const addresses = normalizeAddresses(
      (body as { addresses?: unknown })?.addresses,
    );
    const assets =
      Array.isArray((body as { assets?: unknown })?.assets) &&
      ((body as { assets: unknown[] }).assets.length ?? 0)
        ? ((body as { assets: string[] }).assets)
        : ["USDC"];

    if (!addresses.length) {
      return NextResponse.json(
        {
          error:
            'addresses[] required. Example: [{"address":"0xYourAddress","blockchains":["base"]}]',
        },
        { status: 400 },
      );
    }

    const jwt = await generateJwt({
      apiKeyId: id,
      apiKeySecret: normalizeSecret(rawSecret),
      requestMethod: "POST",
      requestHost: "api.developer.coinbase.com",
      requestPath: "/onramp/v1/token",
      expiresIn: 120,
    });

    const upstream = await fetch(
      "https://api.developer.coinbase.com/onramp/v1/token",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${jwt}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ addresses, assets }),
        cache: "no-store",
      },
    );

    const text = await upstream.text();
    let json: Record<string, unknown>;
    try {
      json = text ? (JSON.parse(text) as Record<string, unknown>) : {};
    } catch {
      json = { raw: text };
    }

    if (!upstream.ok) {
      const baseMsg =
        (json?.error as string) || (json?.message as string) || text || "Coinbase Onramp error";
      const mapped =
        upstream.status === 401
          ? `${baseMsg} (check CDP keys & server time; JWT must be valid)`
          : upstream.status === 403
            ? `${baseMsg} (add your origin to Allowed Origins in the Coinbase developer dashboard)`
            : upstream.status === 400
              ? `${baseMsg} (did you send addresses[] with blockchains:["base"]? is the address checksummed/valid?)`
              : baseMsg;
      return NextResponse.json({ error: mapped }, { status: upstream.status });
    }

    const token = json?.token as string | undefined;
    if (!token) {
      return NextResponse.json({ error: "No token in response" }, { status: 502 });
    }
    return NextResponse.json({ token }, { headers: { "Cache-Control": "no-store" } });
  } catch (e) {
    console.error("[onramp] server error", e);
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Unexpected server error" },
      { status: 500 },
    );
  }
}
