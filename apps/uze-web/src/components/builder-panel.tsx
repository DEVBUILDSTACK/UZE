"use client";

import { useState } from "react";

/** UZE Builders registration (owner's tap, 2026-11-11 —
 *  Directives 2 + 3). The low-friction lane: an autonomous
 *  agent registers with an email and an x401 wallet address,
 *  no KYB. The welcome copy is the ratified opaque-credit
 *  copy — it never names the credit source. The form posts to
 *  the compose API's mock registry
 *  (POST /api/v1/treasury/sub-builder/register); if the demo
 *  API is offline the panel says so and still shows the copy,
 *  because the copy is the published onboarding text. */
const COMPOSE_API =
  process.env.NEXT_PUBLIC_COMPOSE_API_URL ?? "https://uze-compose-api.onrender.com";

const WELCOME =
  "Welcome to UZE Builders. Your account is active. Workflows will render Compute Credits when available based on network capacity.";

export default function BuilderPanel() {
  const [email, setEmail] = useState("");
  const [wallet, setWallet] = useState("");
  const [state, setState] = useState<"idle" | "busy" | "done" | "offline">(
    "idle",
  );

  async function register() {
    setState("busy");
    try {
      const res = await fetch(
        `${COMPOSE_API}/api/v1/treasury/sub-builder/register`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            x401_wallet_address: wallet,
          }),
        },
      );
      setState(res.ok ? "done" : "offline");
    } catch {
      setState("offline");
    }
  }

  const input: React.CSSProperties = {
    width: "100%",
    padding: "10px 12px",
    borderRadius: 10,
    border: "1px solid #d8d2c9",
    margin: "6px 0 12px",
  };
  const btn: React.CSSProperties = {
    padding: "8px 18px",
    borderRadius: 999,
    border: "1px solid #1a1a1a",
    background: "#ff6b00",
    fontWeight: 700,
    cursor: "pointer",
  };

  return (
    <section style={{ marginTop: 36 }}>
      <h2>UZE Builders</h2>
      <p>
        Autonomous agents onboard here — an email and an x401 wallet, no
        KYB. Small work runs in this lane; the three-tier gate in the
        treasury routes anything large through an Entity.
      </p>
      <label>
        Email
        <input
          style={input}
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="agent@example.com"
        />
      </label>
      <label>
        x401 wallet address
        <input
          style={input}
          value={wallet}
          onChange={(e) => setWallet(e.target.value)}
          placeholder="wallet address"
        />
      </label>
      <button
        type="button"
        style={btn}
        disabled={state === "busy" || !email || wallet.length < 8}
        onClick={register}
      >
        {state === "busy" ? "Registering…" : "Register as a UZE Builder"}
      </button>
      {state === "done" && (
        <p role="status" style={{ marginTop: 14 }}>
          {WELCOME}
        </p>
      )}
      {state === "offline" && (
        <p role="status" style={{ marginTop: 14 }}>
          The registration service is offline in this demo environment —
          the published onboarding text stands: {WELCOME}
        </p>
      )}
    </section>
  );
}
