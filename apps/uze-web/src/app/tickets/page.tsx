import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Tickets | UZEmarkets",
  description:
    "Tickets on UZEmarkets — allocation, not picking. You choose the price area and how many seats together; the engine assigns. Every ticket an NFT minted once, with receipt and attestation.",
};

export default function TicketsPage() {
  return (
    <main className="mk">
      <p className="note">
        UZEMARKETS · tickets — venue ticketing under the design law:
        venue-as-data, allocation-not-picking, provenance invariant,
        matching on NEAR.
      </p>
      <h1>Tickets</h1>
      <p className="lede">
        Allocation, not picking. You choose the price area and how
        many seats together — the engine assigns.
      </p>
      <p>
        A UZE ticket is minted once on NEAR, as an NFT with its
        receipt and attestation attached. On resale the original NFT
        transfers — it is never re-minted — so the chain of custody
        is the proof. Everything bridges through NEAR — NEAR Intents
        and NEAR AI: the EVM L2s (Robinhood Chain, Ink, and Base),
        LightLink as the EVM home, and Solana. Settlement follows the chain — USDC
        on Solana and Base (CCTP through Wormhole), USDG on
        Robinhood Chain.
      </p>

      <h2>The built surface — live here</h2>
      <p>
        The venue ticketing build — the canonical standalone build,
        linked live from its own home: pick a sector in the
        3D venue and the engine allocates your seats; connect the
        wallet and your tickets land in it as NFTs, one per seat,
        each with its own provenance chain; list them and they
        surface in the secondary market beside the live secondary
        index. Demo build (flow-v10) — wallet and settlement are
        mocked inside it, and it says so.{" "}
        <a href="https://devbuildstack.github.io/uze-venue-ticketing-demo/" target="_blank" rel="noreferrer">
          Open the full ticketing surface →
        </a>
      </p>
      <iframe
        src="https://devbuildstack.github.io/uze-venue-ticketing-demo/"
        title="UZE venue ticketing — seat selection, NFT wallet, secondary market"
        style={{
          width: "100%",
          height: "880px",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          background: "var(--panel)",
        }}
        loading="lazy"
      />

      <h2>How it works</h2>
      <div className="cards">
        <div className="card">
          <h3>Venue as data</h3>
          <p className="meta">Sectors × rings</p>
          <p>
            A venue is data, never code — sectors and three rings
            describe any arena or theatre, so a new venue is a new
            dataset, not a new build.
          </p>
        </div>
        <div className="card">
          <h3>Allocation, not picking</h3>
          <p className="meta">Price area + seats together</p>
          <p>
            You pick the price area and the number of seats together;
            the engine assigns the seats and you accept or decline.
            No seat-map hunting, no cart races.
          </p>
        </div>
        <div className="card">
          <h3>Provenance invariant</h3>
          <p className="meta">Minted once, transferred whole</p>
          <p>
            The ticket, its receipt, and its attestation are one
            object. Resale moves that object — provenance can never
            fork.
          </p>
        </div>
        <div className="card">
          <h3>Your NFT wallet</h3>
          <p className="meta">The ticket lives with the buyer</p>
          <p>
            Tickets are held in the buyer&apos;s own wallet — no
            affiliate account needed. Primary mints and secondary
            purchases land in the same place: your tickets, each one
            the original NFT.
          </p>
        </div>
        <div className="card">
          <h3>The secondary market</h3>
          <p className="meta">Resale with a live index</p>
          <p>
            List a ticket and it surfaces in the secondary market at
            your ask, beside the secondary index — the premium the
            market currently puts on that seat. Resale transfers the
            same NFT; the provenance chain is the fraud check.
          </p>
        </div>
        <div className="card">
          <h3>Prize inventory</h3>
          <p className="meta">From the held-back allocation</p>
          <p>
            Prize inventory is minted from the platform&apos;s
            held-back primary allocation, never bought off the
            secondary market. Price calls require holding a
            primarily-purchased ticket.
          </p>
        </div>
      </div>

      <h2>Where tickets live</h2>
      <p>
        Ticketed experiences — and the touring and stay offerings
        around them — are browsed on the{" "}
        <Link href="/guidance">guidance board</Link>. Event offerings
        for the 2027 season ride the alpha window: the{" "}
        <Link href="/alpha">alpha signup</Link> whitelists one
        self-custodial wallet per signup for the B2B and B2C event
        offerings and the secondary UZEticket tech offerings.
      </p>
    </main>
  );
}
