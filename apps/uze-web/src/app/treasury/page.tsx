import type { Metadata } from "next";
import TreasuryTabs from "@/components/treasury-tabs";
import BuilderPanel from "@/components/builder-panel";
import PrivateAiToggle from "@/components/private-ai-toggle";

export const metadata: Metadata = {
  title: "Treasury | UZEmarkets",
  description:
    "The UZEmarkets Treasury: permissionless, self-custodial on-ramp configuration and Send & Receive for human syndicates and autonomous agents.",
};

/** Treasury (2026-11-11, owner's override build): the
 *  self-custodial treasury surface. On-ramp amounts follow the
 *  fixed increment ladder ($5–$100 by $5, $101–$250 by $10,
 *  $251–$1,750 by $50); funds move by Send & Receive only —
 *  there is no off-ramp. Demonstration scope is stated on the
 *  page: funding and swaps are simulated against the compose
 *  treasury API's mock router; no funds move. */
export default function TreasuryPage() {
  return (
    <main className="mk">
      <h1>Treasury</h1>
      <p className="lede">
        Permissionless, self-custodial — for syndicates and agents alike
      </p>
      <p>
        An autonomous agent cannot be chained to a corporate credit
        card, and a syndicate should not have to trust a platform with
        its funds. The UZEmarkets Treasury lets humans and agents fund
        AI inference and real-world-asset transactions from their own
        wallets: fiat arrives through a third-party provider directly
        into the user&apos;s wallet — UZEmarkets never touches fiat —
        and from there, everything moves by Send &amp; Receive.
      </p>
      <TreasuryTabs />
      <BuilderPanel />
      <PrivateAiToggle />
      <p className="note">
        Demonstration build — three journeys: Fund (Coinbase Onramp,
        activates when the owner configures CDP keys), Move (Wormhole
        Connect with the route set pinned to CCTP), and Swap (the
        compose treasury: on-ramp ladder + Send &amp; Receive + live
        1Click quotes — <code>POST /api/v1/treasury/onramp/config</code>,{" "}
        <code>POST /api/v1/treasury/send-receive</code>,{" "}
        <code>POST /api/v1/treasury/swap</code>). Swap execution against
        the compose API is simulated; no funds move from this page.
      </p>
    </main>
  );
}
