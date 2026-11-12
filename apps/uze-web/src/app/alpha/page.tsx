/** UZE Alpha — the signup list for the UZEguidance priced markets.
 *
 * Owner directive, 2026-11-12: every posted price comes off. The
 * levels for UZEBuilder, UZEaffiliate and UZEaffiliate-actively-
 * onramped are set by an autonomous guidance market — the market
 * bids the levels, and UZEmarkets honors them prospectively, only
 * for KYB entities and KYC partner agents, and only for signups
 * inside the window: November 15, 2026 – January 12, 2027,
 * 10:59 PM PST. Signing up whitelists ONE self-custodial wallet
 * (Solana / NEAR / Robinhood / Ink / LightLink) for the 2027
 * offerings. The form posts to the compose API; nothing is
 * recorded client-side, and an unreachable intake says so. */
"use client";

import { useState } from "react";
import Link from "next/link";
import {
  CHAIN_HINTS,
  submitAlphaSignup,
  validWallet,
  type AlphaChain,
  type AlphaLevel,
  type AlphaSignupResult,
  type OnrampLane,
} from "@/lib/alpha";

const LEVELS: { id: AlphaLevel; title: string; blurb: string }[] = [
  {
    id: "builder",
    title: "UZEBuilder",
    blurb:
      "Build on the stack. Agents and developers building offerings the market tests and uzes.",
  },
  {
    id: "affiliate",
    title: "UZEaffiliate",
    blurb:
      "Bring the demand. Affiliates whose buyers shape what gets offered, proven genuine, and improved every round.",
  },
  {
    id: "affiliate_onramped",
    title: "UZEaffiliate — actively onramped",
    blurb:
      "The affiliate level, actively onramped uzing TradeLayer or SigLayer — capital in motion, not just reach.",
  },
];

const CHAINS: { id: AlphaChain; label: string }[] = [
  { id: "solana", label: "Solana" },
  { id: "near", label: "NEAR" },
  { id: "robinhood", label: "Robinhood" },
  { id: "ink", label: "Ink" },
  { id: "lightlink", label: "LightLink" },
];

export default function AlphaPage() {
  const [level, setLevel] = useState<AlphaLevel>("builder");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [entityName, setEntityName] = useState("");
  const [kyb, setKyb] = useState(false);
  const [kyc, setKyc] = useState(false);
  const [chain, setChain] = useState<AlphaChain>("solana");
  const [wallet, setWallet] = useState("");
  const [lane, setLane] = useState<OnrampLane>("tradelayer");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState<AlphaSignupResult | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!validWallet(chain, wallet)) {
      setError(`That address does not match the ${chain} format. ${CHAIN_HINTS[chain]}`);
      return;
    }
    if (kyb && !entityName.trim()) {
      setError("A KYB entity signup needs the legal entity name.");
      return;
    }
    setBusy(true);
    const res = await submitAlphaSignup({
      level,
      name: name.trim(),
      email: email.trim(),
      entity_name: entityName.trim() || undefined,
      kyb_attested: kyb,
      kyc_attested: kyc,
      chain,
      wallet_address: wallet.trim(),
      onramp_lane: level === "affiliate_onramped" ? lane : undefined,
    });
    setBusy(false);
    if (res.ok) setDone(res.result);
    else setError(res.message);
  }

  return (
    <main>
      <h1>UZE Alpha — the signup list</h1>
      <p>
        The posted prices are gone. From here, the levels for{" "}
        <strong>UZEBuilder</strong>, <strong>UZEaffiliate</strong> and{" "}
        <strong>UZEaffiliate actively onramped</strong> are set by the
        UZEguidance priced markets: the market bids the levels, and we
        honor them prospectively — for KYB entities and KYC partner
        agents who sign up inside the window.
      </p>
      <p className="note">
        Honored window: <strong>November 15, 2026</strong> through{" "}
        <strong>January 12, 2027 at 10:59 PM PST</strong>. The list is
        open now; a signup outside the window stays on the list, and
        the market levels are honored only for verified signups inside
        it.
      </p>

      <h2>The levels</h2>
      <ul className="cards">
        {LEVELS.map((l) => (
          <li key={l.id} className="card">
            <h3>{l.title}</h3>
            <p>{l.blurb}</p>
            <p className="meta">Level: set by the UZEguidance market — no posted price.</p>
          </li>
        ))}
      </ul>

      <h2>What the whitelist unlocks in 2027</h2>
      <p>
        One self-custodial wallet, whitelisted once, for the 2027 B2B
        and B2C event offerings, the secondary UZEticket tech
        offerings, and the music festival Frontier NFT collectibles
        paired as payment tech innovation from the L2Launch Launchpad.
      </p>

      <h2>Join the list</h2>
      {done ? (
        <section aria-label="Signup confirmed">
          <p>
            <strong>You are on the alpha list.</strong>{" "}
            {done.duplicate
              ? "This wallet and email were already listed — one seat, kept."
              : `Signup ${done.id} — ${done.level} level, ${done.chain} wallet whitelisted.`}
          </p>
          <p>
            {done.window_state === "in_window"
              ? "Your signup landed inside the honored window."
              : done.window_state === "pre_window"
                ? "The honored window opens November 15, 2026 — signups inside it carry the honored levels. You are on the list from today."
                : "The honored window closed January 12, 2027 at 10:59 PM PST. You are on the list; the market levels were honored for verified signups inside the window."}
          </p>
          <p className="note">
            {done.honored
              ? "With your KYB/KYC attestation on file, the market levels are honored for this signup, prospectively."
              : "Market levels are honored for KYB entities and KYC partner agents — complete that verification and the honored levels attach to this signup when it is inside the window."}
          </p>
          <p>
            <Link href="/guidance">Back to UZEguidance</Link> ·{" "}
            <Link href="/">Home</Link>
          </p>
        </section>
      ) : (
        <form onSubmit={submit}>
          <fieldset>
            <legend>1 — Pick your level</legend>
            <div className="chips" role="group" aria-label="Level">
              {LEVELS.map((l) => (
                <button
                  key={l.id}
                  type="button"
                  className="chip"
                  aria-pressed={level === l.id}
                  onClick={() => setLevel(l.id)}
                >
                  {l.title}
                </button>
              ))}
            </div>
            {level === "affiliate_onramped" && (
              <label>
                Onramp lane
                <select
                  value={lane}
                  onChange={(e) => setLane(e.target.value as OnrampLane)}
                >
                  <option value="tradelayer">TradeLayer</option>
                  <option value="siglayer">SigLayer</option>
                </select>
              </label>
            )}
          </fieldset>

          <fieldset>
            <legend>2 — Who is signing up</legend>
            <label>
              Name
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name or agent name"
              />
            </label>
            <label>
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </label>
            <label>
              Legal entity name (for KYB entities)
              <input
                type="text"
                value={entityName}
                onChange={(e) => setEntityName(e.target.value)}
                placeholder="Entity LLC"
              />
            </label>
            <label>
              <input
                type="checkbox"
                checked={kyb}
                onChange={(e) => setKyb(e.target.checked)}
              />{" "}
              We are a KYB-verified entity
            </label>
            <label>
              <input
                type="checkbox"
                checked={kyc}
                onChange={(e) => setKyc(e.target.checked)}
              />{" "}
              I am a KYC-verified partner agent
            </label>
          </fieldset>

          <fieldset>
            <legend>3 — Whitelist your wallet</legend>
            <div className="chips" role="group" aria-label="Chain">
              {CHAINS.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className="chip"
                  aria-pressed={chain === c.id}
                  onClick={() => setChain(c.id)}
                >
                  {c.label}
                </button>
              ))}
            </div>
            <label>
              Self-custodial wallet address
              <input
                type="text"
                required
                value={wallet}
                onChange={(e) => setWallet(e.target.value)}
                placeholder="Your wallet address"
              />
            </label>
            <p className="note">{CHAIN_HINTS[chain]} Self-custodial only — the wallet stays yours.</p>
          </fieldset>

          {error && <p role="alert">{error}</p>}
          <button type="submit" disabled={busy}>
            {busy ? "Joining…" : "Join the alpha list"}
          </button>
        </form>
      )}
    </main>
  );
}
