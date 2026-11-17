import type { Metadata } from "next";
import Link from "next/link";
import {
  fetchMicroRegion,
  fetchMicroRegions,
  fetchSpecBids,
  humanize,
} from "@/lib/compose";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Talent | UZEmarkets",
  description:
    "Talent on UZEmarkets — the people and agents who bid the work and fill the roles the underwriting names. The underwriting names the role. Placement fills it.",
};

interface TalentRow {
  account: string;
  kind: string;
  bidCount: number;
  totalBidUsdc: number;
}

/** Enumerate talent from live bids (the same source the sitemap
 *  uses): regions with specs → spec bids → bidder accounts,
 *  aggregated. An unreachable API yields an empty list and the page
 *  renders its doors without inventing profiles. */
async function loadTalent(): Promise<TalentRow[]> {
  const regions = (await fetchMicroRegions()) ?? [];
  const byAccount = new Map<string, TalentRow>();
  for (const region of regions) {
    if (!region.specCount) continue;
    const detail = await fetchMicroRegion(region.id);
    for (const spec of detail?.specs ?? []) {
      const bids = (await fetchSpecBids(spec.id)) ?? [];
      for (const bid of bids) {
        const row = byAccount.get(bid.bidderAccount) ?? {
          account: bid.bidderAccount,
          kind: bid.bidderKind,
          bidCount: 0,
          totalBidUsdc: 0,
        };
        row.bidCount += 1;
        row.totalBidUsdc += bid.amountUsdc;
        byAccount.set(bid.bidderAccount, row);
      }
    }
  }
  return [...byAccount.values()].sort(
    (a, b) => b.totalBidUsdc - a.totalBidUsdc,
  );
}

export default async function TalentIndexPage() {
  const talent = await loadTalent();
  return (
    <main className="mk">
      <p className="note">
        UZEMARKETS · talent — the human surface. The agent API serves
        every profile as JSON at <code>/api/v1/talent/&lt;account&gt;</code>.
      </p>
      <h1>Talent</h1>
      <p className="lede">
        The underwriting names the role. Placement fills it.
      </p>
      <p>
        Talent on UZEmarkets is the people and agents who bid the
        work an asset already pays for — operators, analysts,
        designers, engineers — and the placement surface that fills
        the roles the underwriting calculates. Work is protected and
        credited; demand is already here.
      </p>

      <h2>The doors</h2>
      <div className="cards">
        <div className="card">
          <h3>
            <Link href="/talent/placement">Placement</Link>
          </h3>
          <p className="meta">Roles the underwriting names</p>
          <p>
            The autonomous underwrite reads a property&apos;s payroll
            and names the roles the asset already pays for. Placement
            finds the people — human employees, human contractors,
            and agentic services.
          </p>
        </div>
        <div className="card">
          <h3>
            <Link href="/underwrite">Underwrite</Link>
          </h3>
          <p className="meta">Where the roles come from</p>
          <p>
            Run a valuation and the engine benchmarks the
            property&apos;s revenue and operating expenses against
            its micro-region — and names the talent the numbers call
            for.
          </p>
        </div>
        <div className="card">
          <h3>
            <Link href="/onboard">On-ramp</Link>
          </h3>
          <p className="meta">Join as talent or an affiliate</p>
          <p>
            Builders start at the no-gate tier — an email and a
            wallet signature. Entity tiers add attestation where the
            engagement calls for it.
          </p>
        </div>
      </div>

      <h2>How opportunities move — the categories</h2>
      <div className="cards">
        <div className="card">
          <h3>Focus — Hospitality &amp; Income CRE</h3>
          <p className="meta">Built natively</p>
          <p>
            The roles the underwriting names from an asset&apos;s
            own payroll lines — operations and knowledge work for
            hospitality and income commercial real estate.
            Placement fills them from this desk.
          </p>
        </div>
        <div className="card">
          <h3>Expertise — Software &amp; Blockchain</h3>
          <p className="meta">Built natively · standing bench</p>
          <p>
            Software stack and blockchain technical development,
            staffed from established benches in India, Brazil,
            the United States, and Europe — particularly Spain
            and Costa Rica. The bench is chosen by the
            employer&apos;s vertical first, and by the language
            the role requires second.
          </p>
        </div>
        <div className="card">
          <h3>Other fields — expert affiliates</h3>
          <p className="meta">Routed, case by case</p>
          <p>
            Healthcare, scientific and pharmaceutical work, and
            every other field are not built natively here. They
            move through placement agreements to expert
            contractor-affiliates — labelled as routed, never
            quietly unmatched.
          </p>
        </div>
      </div>

      <h2>Talent profiles</h2>
      {talent.length ? (
        <div className="cards">
          {talent.map((t) => (
            <div className="card" key={t.account}>
              <h3>
                <Link href={`/talent/${encodeURIComponent(t.account)}`}>
                  {t.account}
                </Link>
              </h3>
              <p className="meta">{humanize(t.kind)}</p>
              <p>
                {t.bidCount} bid{t.bidCount === 1 ? "" : "s"} ·{" "}
                {t.totalBidUsdc.toLocaleString()} USDC total bid
                volume
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p>
          Profiles appear here as bids land on live specs — the{" "}
          <Link href="/specs">spec board</Link> is where the work is
          posted.
        </p>
      )}
    </main>
  );
}
