"use client";

import { useState } from "react";

/** Private AI Mode (owner tap, 2026-11-13). The toggle
 * reflects the routing that actually exists in
 * services/compose/src/inference.py: NEAR AI Cloud with
 * gateway + model attestation verified before sending. It
 * deliberately does NOT claim the Trace Commons desktop
 * Gateway app (a client-side tool for coding agents — see
 * docs/specifications/private-inference-gateway-proposal.md)
 * and it shows the honest account state: NEAR AI balance
 * $0.00, live inference returns HTTP 402 until credits land.
 * No credit balance, earned or estimated, appears here. */
export default function PrivateAiToggle() {
  const [on, setOn] = useState(true);
  return (
    <section>
      <h2>Private AI Mode</h2>
      <p>
        Route inference through NEAR AI Gateway (Private TEE) —
        in this build, that means the attestation-verified NEAR
        AI Cloud routing the inference layer already performs:
        gateway and model attestation are verified before any
        prompt is sent, so financial data is answered inside
        hardware-attested enclaves, never on an unattested
        endpoint.
      </p>
      <p>
        <button
          type="button"
          role="switch"
          aria-checked={on}
          onClick={() => setOn(!on)}
          style={{
            padding: "0.5rem 1rem",
            borderRadius: "999px",
            border: "2px solid #1a1a1a",
            background: on ? "#ff6b00" : "#f5f2ee",
            color: on ? "#fff" : "#1a1a1a",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          Private AI Mode: {on ? "ON" : "OFF"}
        </button>
      </p>
      <p className="note">
        {on
          ? "On: inference is routed only to attestation-verified endpoints. Current account state — NEAR AI balance $0.00; live calls return HTTP 402 until credits land. That error is shown, never papered over: no credits are earned, estimated, or claimed here."
          : "Off: inference calls are refused rather than routed to an unattested endpoint. Current account state — NEAR AI balance $0.00; live calls return HTTP 402 until credits land."}{" "}
        Data-sharing consent is a separate, tiered choice
        (debugging &amp; evaluation always on; benchmark
        generation, ranking-model training, and model training
        each opt-in) recorded through the gateway opt-in
        endpoint — signing in alone shares nothing.
      </p>
    </section>
  );
}
