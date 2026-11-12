"use client";

import { useMemo, useState } from "react";

/** Treasury panel — On-Ramp + Send/Receive (2026-11-11 build).
 *  DEMO SCOPE, stated on the panel itself: the on-ramp ladder
 *  validation is the real spec logic (mirrors the compose API,
 *  POST /api/v1/treasury/onramp/config); funding and swaps are
 *  simulated — no funds move and UZEmarkets never touches fiat. */

const ONRAMP_CHAINS = [
  { key: "SOLANA", label: "Solana — USDC (default)" },
  { key: "BASE", label: "Base — USDC" },
  { key: "ROBINHOOD", label: "Robinhood Chain — USDC" },
  { key: "INK", label: "Ink — USDC" },
  { key: "ARC", label: "Arc — USDC" },
];

const SR_CHAINS = ["Solana", "Base", "Ink", "Robinhood", "Arc", "NEAR"];

function ladderCheck(amount: number): { ok: boolean; message: string } {
  if (!Number.isFinite(amount) || amount < 5)
    return { ok: false, message: "Minimum on-ramp is $5." };
  if (amount > 1750)
    return { ok: false, message: "Maximum on-ramp is $1,750." };
  if (amount <= 100 && amount % 5 !== 0)
    return { ok: false, message: "$5–$100 moves in $5 increments." };
  if (amount > 100 && amount <= 250 && amount % 10 !== 0)
    return { ok: false, message: "$101–$250 moves in $10 increments." };
  if (amount > 250 && amount % 50 !== 0)
    return { ok: false, message: "$251–$1,750 moves in $50 increments." };
  return { ok: true, message: "Valid increment." };
}

function snapToLadder(amount: number): number {
  const a = Math.min(1750, Math.max(5, Math.round(amount)));
  if (a <= 100) return Math.round(a / 5) * 5;
  if (a <= 250) return Math.round(a / 10) * 10;
  return Math.round(a / 50) * 50;
}

export default function TreasuryPanel() {
  const [tab, setTab] = useState<"onramp" | "send">("onramp");

  // On-ramp state
  const [amount, setAmount] = useState(100);
  const [chain, setChain] = useState("SOLANA");
  const [funded, setFunded] = useState<string | null>(null);
  const check = useMemo(() => ladderCheck(amount), [amount]);

  // Send/Receive state
  const [srAmount, setSrAmount] = useState("10");
  const [source, setSource] = useState("Solana");
  const [target, setTarget] = useState("NEAR");
  const [agent, setAgent] = useState("SURA");
  const [sent, setSent] = useState<string | null>(null);

  const tabBtn = (active: boolean): React.CSSProperties => ({
    padding: "8px 18px",
    borderRadius: 999,
    border: "1px solid #ff6b00",
    background: active ? "#ff6b00" : "transparent",
    color: active ? "#ffffff" : "#ff6b00",
    fontWeight: 700,
    cursor: "pointer",
  });

  const field: React.CSSProperties = {
    display: "block",
    width: "100%",
    padding: "10px 12px",
    marginTop: 6,
    borderRadius: 10,
    border: "1px solid #d8d2c8",
    background: "#fffdf9",
    fontSize: 16,
  };

  return (
    <div>
      <div style={{ display: "flex", gap: 10, margin: "18px 0" }}>
        <button style={tabBtn(tab === "onramp")} onClick={() => setTab("onramp")}>
          On-Ramp
        </button>
        <button style={tabBtn(tab === "send")} onClick={() => setTab("send")}>
          Send / Receive
        </button>
      </div>

      {tab === "onramp" && (
        <div className="card">
          <h3>Fund your wallet with fiat</h3>
          <p className="meta">
            A third-party provider routes fiat directly to your
            self-custodial wallet. UZEmarkets never touches fiat.
            There is no off-ramp — funds move by Send &amp; Receive.
          </p>
          <label>
            Amount (USD)
            <input
              type="range"
              min={5}
              max={1750}
              step={5}
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              style={{ width: "100%", marginTop: 10 }}
            />
          </label>
          <p style={{ fontSize: 28, fontWeight: 800, margin: "8px 0" }}>
            ${amount.toLocaleString()}
            <span style={{ fontSize: 14, fontWeight: 600, marginLeft: 10, color: check.ok ? "#1d7a3a" : "#b3261e" }}>
              {check.message}
            </span>
          </p>
          {!check.ok && (
            <button
              style={tabBtn(false)}
              onClick={() => setAmount(snapToLadder(amount))}
            >
              Snap to ${snapToLadder(amount).toLocaleString()}
            </button>
          )}
          <label style={{ display: "block", marginTop: 14 }}>
            Destination
            <select value={chain} onChange={(e) => setChain(e.target.value)} style={field}>
              {ONRAMP_CHAINS.map((c) => (
                <option key={c.key} value={c.key}>{c.label}</option>
              ))}
            </select>
          </label>
          <button
            style={{ ...tabBtn(true), marginTop: 16 }}
            disabled={!check.ok}
            onClick={() =>
              setFunded(
                `Mock on-ramp configured: $${amount.toLocaleString()} → ` +
                `${ONRAMP_CHAINS.find((c) => c.key === chain)?.label}. ` +
                `Funds route from the third-party provider directly to your wallet.`
              )
            }
          >
            Fund with Fiat (mock)
          </button>
          {funded && <p className="note" style={{ marginTop: 12 }}>{funded}</p>}
        </div>
      )}

      {tab === "send" && (
        <div className="card">
          <h3>Send &amp; Receive — no off-ramp</h3>
          <p className="meta">
            Move funds P2P or cross-chain through the swap router.
            Agents swap into native NEAR to fund their own compute;
            identity is verified by x401 (Arc is a supported network
            for x401 identity routing) and payments ride x402 rails.
          </p>
          <label style={{ display: "block", marginTop: 10 }}>
            Amount
            <input
              type="number"
              min="0"
              value={srAmount}
              onChange={(e) => setSrAmount(e.target.value)}
              style={field}
            />
          </label>
          <label style={{ display: "block", marginTop: 12 }}>
            From
            <select value={source} onChange={(e) => setSource(e.target.value)} style={field}>
              {SR_CHAINS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </label>
          <label style={{ display: "block", marginTop: 12 }}>
            To
            <select value={target} onChange={(e) => setTarget(e.target.value)} style={field}>
              {SR_CHAINS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </label>
          <label style={{ display: "block", marginTop: 12 }}>
            Acting agent (optional)
            <select value={agent} onChange={(e) => setAgent(e.target.value)} style={field}>
              <option value="">Human / syndicate</option>
              <option value="SURA">SURA</option>
              <option value="GIRA">GIRA</option>
            </select>
          </label>
          <button
            style={{ ...tabBtn(true), marginTop: 16 }}
            onClick={() =>
              setSent(
                source === target
                  ? `Mock P2P send: ${srAmount} on ${source}. Recorded in the treasury log.`
                  : `Mock swap routed: ${srAmount} from ${source} → ${target}` +
                    (target === "NEAR" && agent
                      ? ` — ${agent}'s compute balance is funded and its next task can run.`
                      : ".")
              )
            }
          >
            {source === target ? "Send (mock)" : "Swap (mock)"}
          </button>
          {sent && <p className="note" style={{ marginTop: 12 }}>{sent}</p>}
        </div>
      )}
    </div>
  );
}
