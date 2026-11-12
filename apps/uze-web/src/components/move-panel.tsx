"use client";

import { useEffect, useState, type ComponentType } from "react";

/** Move tab (treasury port, 2026-11-11): Wormhole Connect,
 *  adapted from Fundio's WormholeBridgeModal — with the
 *  correction the audit demanded: the route set is EXPLICIT,
 *  not Connect's defaults. The config below pins:
 *   - chains: Solana / Base / Ethereum only;
 *   - routes: [CCTPRoute] only — Circle's CCTP is the single
 *     enabled route, so native USDC moves as native USDC
 *     (burn-and-mint), never as a wrapped bridge asset. The
 *     CCTP route carries USDC by construction, which is what
 *     makes the corridor USDC-only;
 *   - network: Mainnet.
 *  Connect v6's CCTP route is the Executor-powered route
 *  (@wormhole-labs/cctp-executor-route), the CCTP V2
 *  generation — pinned by the installed 6.0.0 package plus
 *  this explicit routes array. The widget renders only after
 *  the route constructor has loaded, so it can never mount
 *  with the default route set.
 *  Loaded client-side only (browser wallet APIs); Connect
 *  manages its own wallet plumbing here — wagmi serves Fund. */
type ConnectProps = {
  config?: Record<string, unknown>;
  theme?: Record<string, unknown>;
};

export default function MovePanel() {
  const [Widget, setWidget] = useState<ComponentType<ConnectProps> | null>(
    null,
  );
  const [cctpRoute, setCctpRoute] = useState<unknown>(null);
  const [failed, setFailed] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    import("@wormhole-foundation/wormhole-connect")
      .then((m) => {
        if (!live) return;
        const mod = m as unknown as Record<string, unknown>;
        setCctpRoute(mod.CCTPRoute);
        setWidget(
          () => (mod.default ?? m) as unknown as ComponentType<ConnectProps>,
        );
      })
      .catch((e) =>
        setFailed(e instanceof Error ? e.message : "Bridge failed to load."),
      );
    return () => {
      live = false;
    };
  }, []);

  const config: Record<string, unknown> = {
    network: "Mainnet",
    chains: ["Solana", "Base", "Ethereum"],
    ...(cctpRoute ? { routes: [cctpRoute] } : {}),
    ui: { title: "Move USDC" },
  };
  const theme: Record<string, unknown> = {
    mode: "dark",
    primary: "#ff6b00",
    background: "#1a1a1a",
    text: "#f5f2ee",
  };

  return (
    <section>
      <h3 style={{ marginTop: 0 }}>Move — Wormhole Bridge (CCTP)</h3>
      <p>
        Bridge native USDC between Solana, Base and Ethereum. The route
        set is pinned in code to Circle&apos;s CCTP — USDC is burned on
        the source chain and minted natively on the destination, never
        wrapped.
      </p>
      {failed && (
        <p role="alert" style={{ color: "#9a3412" }}>
          {failed}
        </p>
      )}
      {!Widget && !failed && <p>Loading the bridge…</p>}
      {Widget && cctpRoute ? (
        <Widget config={config} theme={theme} />
      ) : (
        Widget && <p>Loading the CCTP route pin…</p>
      )}
      <p className="note">
        Configuration is explicit (chains + CCTPRoute only) — verified
        against the installed @wormhole-foundation/wormhole-connect
        6.0.0 type surface, not left to widget defaults.
      </p>
    </section>
  );
}
