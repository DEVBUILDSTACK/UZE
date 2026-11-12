import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "The Delphi Bridge — Design Exhibit | UZEmarkets",
  description:
    "How UZEmarkets' verified property claims — issued, judged, and anchored on NEAR — become priced information markets on Gensyn's Delphi. A design exhibit prepared for the Gensyn Foundation Grant Programme.",
};

/** Demo host — the Delphi Bridge showcase (James's ruling,
 *  2026-11-10): the Gensyn Delphi grant track's quarantine is
 *  lifted for THIS surface only. The page is labelled as design
 *  throughout: the bridge is a specification and grant proposal,
 *  not a live integration; no Delphi market exists for any
 *  UZEmarkets claim. The NEAR-side claims system it builds on is
 *  built and proven on testnet. All other quarantine rules stand:
 *  no live Delphi calls, no markets, no money. */
export default function DemoHome() {
  return (
    <main className="mk">
      <h1>The Delphi Bridge</h1>
      <p className="lede">
        From verified claims to priced information markets: how the
        property claims UZEmarkets issues, judges, and anchors on
        NEAR become USDC-traded information markets on Gensyn&rsquo;s
        Delphi — without ever letting price replace proof.
      </p>
      <p>
        <strong>DESIGN EXHIBIT.</strong> The bridge on this page is a
        specification, prepared for the Gensyn Foundation Grant
        Programme. It is not a live integration: no Delphi market
        exists for any UZEmarkets claim today, and the bridge code
        lands in the Sprint 2 window (from November 15). Nothing on
        this host is a live market: balances are testnet, and
        listings are fixtures.
      </p>

      <section>
        <h2>Built on NEAR: the claims system (live on testnet)</h2>
        <p>
          UZEmarkets prices the truth about income property. A claim
          about a property — its revenue, its operating expenses, its
          net income — is issued by an owner, a broker, or one of our
          underwriting agents; the introducer posts a bond, escrowed
          on NEAR; anyone may challenge it, and each dispute doubles
          the bond. Judgment runs through a Juror Team: a panel of AI
          juror seats whose inference runs as attested NEAR AI, and
          whose verdict must be reproducible — deterministic
          re-judgment and receipt verification must reproduce the
          outcome for it to stand. A claim confirmed through that
          process is <strong>Assuratized</strong>: reconciled, anchored
          on NEAR, and served through our Reliance API to financing
          partners. The full pipeline — claim model, challenge and
          panel mechanics, attestation anchoring, Reliance API — is
          built and proven end to end on testnet (206 passing tests,
          a live on-chain settlement on Solana devnet authorized via
          NEAR Chain Signatures, and live attestation anchors from a
          three-seat juror panel). It is non-monetized by design: no
          claim transition ever executes a financial transaction.
          What our claims have is verification. What they do not yet
          have is a price.
        </p>
      </section>

      <section>
        <h2>The bridge: how a claim becomes a market</h2>
        <p>
          When a standard-tier claim is contested — the moment its
          truth is genuinely in dispute — the bridge renders it as a
          Delphi information market, following Delphi&rsquo;s own
          discipline of one authority, one threshold, one date. From
          our live demo asset, the 340-room Aloft Miami-Brickell:
        </p>
        <p>
          <em>
            &ldquo;Will the audited total operating expenses of the
            340-room Aloft Miami-Brickell for Q3 2026 come in at or
            below US$2,840,000.00?&rdquo;
          </em>
        </p>
        <p>
          Yes / No / catch-all outcomes, LMSR pricing in USDC, and
          settlement criteria that restate our exact threshold rule:
          cent-exact minor units, a single round-half-to-even
          conversion point, and the asset&rsquo;s local timezone rule
          for period boundaries.
        </p>
      </section>

      <section>
        <h2>A price is a signal, never the verdict</h2>
        <p>
          The market&rsquo;s price feeds our juror process as evidence
          of the crowd&rsquo;s assessment. The claim itself still
          resolves only through our panel, our precedents, and our
          human authorization gate. The two systems dual-anchor: NEAR
          anchors the claim&rsquo;s attestation, and the Delphi
          market&rsquo;s REE settlement receipt — Gensyn&rsquo;s proof
          that its judge&rsquo;s computation ran as specified — is
          recorded by hash in our Adjudication Manifest, the signed
          dossier that binds the claim, its precedent snapshot, its
          panel policy, its verdicts, and both anchors into one record
          a lender can verify end to end.
        </p>
      </section>

      <section>
        <h2>Three buckets, never mixed</h2>
        <p>
          Accounting stays separated in three buckets that never flow
          into each other: the claim bond (our side, on NEAR); the
          market collateral (the creator&rsquo;s LMSR liquidity inside
          Delphi, at risk under Delphi&rsquo;s terms); and lending
          settlement (USDC on Solana, executed only through our
          existing settlement path on an authorized Assuratized claim —
          never by a market event).
        </p>
      </section>

      <section>
        <h2>Stated openly</h2>
        <p>
          Market creation on Delphi is currently a guided web-app
          flow; the published SDK reads markets, quotes, and executes
          trades, but exposes no programmatic creation. The bridge
          therefore launches with an assisted creation console —
          software that prepares every field of a market from a claim
          and walks an operator through Delphi&rsquo;s own flow — and
          a programmatic creation path is proposed as a grant
          deliverable to build with Gensyn. Delphi configures its own
          settlement: our Juror Team never judges a Delphi market, and
          Delphi&rsquo;s settlement never settles our claims; the two
          judgments are deliberately independent, and their agreement
          or disagreement is itself recorded information. Confidential
          claims — the sealed-bid tier whose evidence cannot be a
          public source — never spawn Delphi markets; the bridge
          carries the standard tier only. Delphi trading is not
          available in the United States, so the bridge launches
          where Delphi operates — Brazil and Uruguay first — while US
          users receive the information and reliance layer without the
          trading surface. And a REE receipt, as Gensyn&rsquo;s own
          documentation notes, proves a computation ran — not that its
          output is true. Delphi proves the crowd was priced and the
          judge computed; Assuraties prove the claim.
        </p>
      </section>

      <section>
        <h2>The grant shape</h2>
        <p>
          Six weeks, four milestones, each paid in $AI on delivery and
          acceptance: bridge logic (the claim-to-market renderer, the
          Adjudication Manifest builder, the tier, geography, and
          authorization gates); the read-side bridge (live signal
          ingestion and REE receipt recording); the assisted creation
          console; and a pilot — the first live markets spawned from
          contested standard-tier claims in a non-US market, with the
          dual-anchor Manifest published for inspection and a clean
          handoff. The bridge, the renderer, the console, and the
          Manifest tooling will be released under an open-source
          licence, per the Programme&rsquo;s expectation. The NEAR-side
          system this builds on is public for inspection:{" "}
          <a href="https://github.com/DEVBUILDSTACK/UZE">
            github.com/DEVBUILDSTACK/UZE
          </a>
          .
        </p>
      </section>
    </main>
  );
}
