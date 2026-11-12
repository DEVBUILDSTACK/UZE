"use client";

import { useState } from "react";
import { useAccount, useConnect, useDisconnect } from "wagmi";

/** Fund tab (treasury port, 2026-11-11): minimal Coinbase
 *  Onramp UI — the OnchainKit modal from Fundio is deprecated
 *  upstream, so this panel talks to our own /api/session route
 *  directly: connect (or paste) a Base address, mint a session
 *  token server-side, and continue into Coinbase's hosted
 *  on-ramp with it. When the deployment has no CDP keys, the
 *  route answers 503 and the panel says so plainly — the tab
 *  is real, its activation waits on the owner's keys. */
export default function FundPanel() {
  const { address: connected, isConnected } = useAccount();
  const { connect, connectors, isPending } = useConnect();
  const { disconnect } = useDisconnect();
  const [address, setAddress] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const effective = (address || connected || "").trim();

  async function mintSession() {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          addresses: [{ address: effective, blockchains: ["base"] }],
          assets: ["USDC"],
        }),
      });
      const json = (await res.json().catch(() => ({}))) as {
        token?: string;
        error?: string;
        detail?: string;
      };
      if (res.status === 503) {
        setError(
          json.detail ??
            "Coinbase on-ramp is not configured in this deployment yet.",
        );
        return;
      }
      if (!res.ok || !json.token) {
        setError(json.error ?? `Session request failed (${res.status}).`);
        return;
      }
      setResult(
        `https://pay.coinbase.com/buy/select-asset?sessionToken=${encodeURIComponent(json.token)}`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Session request failed.");
    } finally {
      setBusy(false);
    }
  }

  const btn: React.CSSProperties = {
    padding: "8px 18px",
    borderRadius: 999,
    border: "1px solid #1a1a1a",
    background: "#1a1a1a",
    color: "#f5f2ee",
    cursor: "pointer",
  };
  const input: React.CSSProperties = {
    width: "100%",
    padding: "10px 12px",
    borderRadius: 10,
    border: "1px solid #d8d2c9",
    margin: "6px 0 12px",
    fontFamily: "monospace",
  };

  return (
    <section>
      <h3 style={{ marginTop: 0 }}>Fund — Coinbase Onramp</h3>
      <p>
        Fiat in, straight to your own Base wallet — UZEmarkets never
        touches the money. Connect a wallet or paste a Base address,
        and Coinbase&apos;s hosted on-ramp takes it from there.
      </p>
      {isConnected ? (
        <p>
          Connected: <code>{connected}</code>{" "}
          <button type="button" onClick={() => disconnect()} style={btn}>
            Disconnect
          </button>
        </p>
      ) : (
        <p>
          <button
            type="button"
            disabled={isPending || connectors.length === 0}
            onClick={() => connectors[0] && connect({ connector: connectors[0] })}
            style={btn}
          >
            {isPending ? "Connecting…" : "Connect wallet"}
          </button>
        </p>
      )}
      <label>
        Destination address (Base)
        <input
          style={input}
          placeholder={connected ?? "0x…"}
          value={address}
          onChange={(e) => setAddress(e.target.value)}
        />
      </label>
      <button
        type="button"
        style={btn}
        disabled={busy || !/^0x[a-fA-F0-9]{40}$/.test(effective)}
        onClick={mintSession}
      >
        {busy ? "Minting session…" : "Continue to Coinbase Onramp"}
      </button>
      {error && (
        <p role="alert" style={{ color: "#9a3412" }}>
          {error}
        </p>
      )}
      {result && (
        <p>
          Session minted.{" "}
          <a href={result} target="_blank" rel="noreferrer">
            Open the Coinbase on-ramp →
          </a>
        </p>
      )}
      <p className="note">
        Session tokens are minted server-side by <code>POST /api/session</code>{" "}
        (CDP JWT, adapted from Fundio&apos;s route). No keys, no token — the
        route answers an honest 503 until the owner configures them.
      </p>
    </section>
  );
}
