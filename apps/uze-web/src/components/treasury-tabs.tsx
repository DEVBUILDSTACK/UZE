"use client";

import { useState } from "react";
import FundPanel from "@/components/fund-panel";
import MovePanel from "@/components/move-panel";
import TreasuryPanel from "@/components/treasury-panel";

/** Treasury journeys (treasury port, 2026-11-11 — owner's
 *  override, lock broken at his word): three tabs, three jobs.
 *   Fund — Coinbase Onramp: fiat into the user's own wallet.
 *   Move — Wormhole Connect: USDC across chains (CCTP corridor).
 *   Swap — the compose treasury: the on-ramp ladder, Send &
 *          Receive, and live 1Click quotes into NEAR compute.
 *  The Swap tab is the panel built earlier the same day,
 *  unchanged — its demo beats were verified against it. */
const TABS = [
  { key: "fund", label: "Fund" },
  { key: "move", label: "Move" },
  { key: "swap", label: "Swap" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

export default function TreasuryTabs() {
  const [tab, setTab] = useState<TabKey>("fund");
  const btn = (active: boolean): React.CSSProperties => ({
    padding: "8px 20px",
    borderRadius: 999,
    border: "1px solid #1a1a1a",
    background: active ? "#ff6b00" : "transparent",
    color: active ? "#1a1a1a" : "#1a1a1a",
    fontWeight: active ? 700 : 400,
    cursor: "pointer",
  });
  return (
    <div>
      <div style={{ display: "flex", gap: 8, margin: "18px 0" }} role="tablist">
        {TABS.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            style={btn(tab === t.key)}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "fund" && <FundPanel />}
      {tab === "move" && <MovePanel />}
      {tab === "swap" && <TreasuryPanel />}
    </div>
  );
}
