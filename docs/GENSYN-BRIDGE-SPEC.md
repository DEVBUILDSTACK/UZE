# GENSYN BRIDGE SPEC — From Scalar Price Calls to Delphi Threshold Markets

**Status:** 🔴 PROPOSAL — this document is the grant deliverable specification. It describes a
build that does **not** exist yet. Filed 2026-11-12 in the private `uze-venue-ticketing` repo;
filed in this repository on the same day by the owner's explicit override of the hackathon
boundary (2026-11-12, 13:56 ET), alongside the mock endpoints described in §5 (which now exist
as 🟡 BUILT AS MOCK in `services/compose/src/ticketing.py`). Nothing in this document is public
website copy, and the internal protocol names used here never appear on any public surface
(the public product is the **UZE Event Market**).
**Basis:** forensic audit of the demo, 2026-11-12 (`UZE-VENUE-TICKETING-GENSYN-AUDIT`), and the
settled contracts in `DESIGN-RULES.md`, which this spec conforms to.

## 1. Current state (what the demo actually has — 🟡 built as mock)

- A **price call** is a scalar estimate recorded against a wallet:

```json
{ "addr": "0x…", "call": 600 }
```

- Calls exist **per event** (state keyed by event id), one call per wallet, and are accepted only
  from wallets holding a **primary-market purchase for that event** (DESIGN-RULES rule 6 — the
  eligibility invariant; secondary purchases and prize wins do not qualify).
- Settlement in the demo is a mock constant per event; ranking is by distance to the settled
  price, `|call − settledPrice|`; the top two ranks win tickets minted from the platform's
  held-back primary allocation (rule 5).
- Tickets are **per-seat NFTs** (one token per seat since flow-v8), each with its own provenance
  ledger (`history[]` of `{from, to, kind, hash}`) — outcome granularity exists at seat level.
- There is **no backend, no persistence, no API, and no market object**. All state is in-page.

## 2. Target state (the proposed build)

A Delphi information market is a **threshold binary** derived from the call stream:

```json
{
  "marketId": "em-soccer-tribuna-central-600",
  "question": "Will the settled secondary price of a Tribuna Central (Lower Ring) ticket for Internacional vs São Paulo FC exceed R$600?",
  "subject": { "eventId": "soccer", "sector": "Tribuna Central", "ring": "Lower Ring" },
  "outcomes": ["Yes", "No"],
  "threshold": 600, "currency": "BRL",
  "resolutionSource": "The actual secondary clearing price produced by NEAR solver matching for the subject sector/ring at market close",
  "settlementCriteria": "Yes if clearingPrice > threshold at close; No otherwise. The clearing price is the solver-matched secondary price, not an oracle estimate.",
  "eligibility": "Positions open to wallets holding a primary-market purchase for the subject event (DESIGN-RULES rule 6)",
  "opensAt": "on-sale", "closesAt": "event week, at first secondary settlement"
}
```

## 3. The transformation (scalar calls → threshold market)

1. **Collect** the holder call stream for a subject (event, sector, ring): one scalar per eligible
   wallet. Sybil resistance is inherited from the eligibility rule — a call requires owning the
   asset — not from stake.
2. **Distribute:** the calls form an empirical distribution of expected settled prices.
3. **Ladder:** choose thresholds at informative points of that distribution (e.g. the quartiles
   and round psychological levels — the levels incumbent grids skip, per the NVDA $150 finding:
   ladders must land on round numbers, not step around them). Each threshold becomes one binary
   market as in §2.
4. **Seed:** the share of calls above a threshold sets that market's initial price, and the
   distribution's spread sets the LMSR liquidity parameter — tight consensus, deep market;
   wide disagreement, shallow market. The crowd's own revealed distribution prices the open.
5. **Settle:** at close, the resolution source is the system's own secondary clearing price
   (NEAR solver matching, DESIGN-RULES rule 4). The market settles on a number the same system
   produces — no external oracle, no self-reported price.
6. **Prizes and positions:** the demo's rank-by-distance game remains the consumer surface;
   threshold positions are the information-market layer beneath it. Prize inventory continues to
   come only from the held-back primary allocation (rule 5), so no position can inflate a prize.

## 4. Worked example (the demo's soccer board)

Calls on Tribuna Central (Lower Ring): `488 · 540 · 588 · 600 · 645 · 701` (R$).
Median ≈ 594. Derived ladder: exceed R$550 (4 of 6 calls above → open ≈ 0.67) · exceed R$600
(2 of 6 strictly above, 1 at → open ≈ 0.42) · exceed R$650 (1 of 6 → open ≈ 0.17). The demo's mock
settlement (R$612) resolves them Yes / Yes / No — consistent with ranking the raw calls, where
600 and 645 are the two closest and take the pair and the single.

## 5. What the grant funds (the ingestion and market-object layer)

- Persistence + an ingestion API for calls, positions and provenance events (per event, per seat).
- The market-object service: subject registry, ladder generation, LMSR seeding from call
  distributions.
- The settlement connector: solver clearing prices on NEAR in, resolutions out.
- Per-event market instances in production (the demo's per-event state is the reference shape).

## 6. Honest framing (from the audit — use this wording)

> "UX and invariants proven in a partner-facing demo; the ingestion and market-object layer is
> the proposed build."

Do not claim the demo is an ingestion engine, and do not claim any existing integration with the
Delphi SDK. What is proven: holder-eligibility, per-seat NFT provenance, settlement ranked by the
clearing price, and a call stream whose distribution is sufficient to seed threshold markets.
