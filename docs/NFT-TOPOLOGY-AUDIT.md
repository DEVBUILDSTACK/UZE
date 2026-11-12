# NFT Ticketing & Multi-Chain Topology — Internal Audit

**Audience:** James and the dev team only — not the analyst,
not partners. **Status: 🟡 BUILT AS MOCK.** Filed 2026-11-12.
Documentation only. The code-level companion is
`docs/TICKETING-DELPHI-EXECUTION.md` (the executed-numbers
record); the production build is specified in
`docs/GENSYN-BRIDGE-SPEC.md` (🔴 PROPOSAL). Source:
`services/compose/src/ticketing.py`.

**Corrections carried in this audit:** the endpoint is
`bridge-intents`, not `bridge_assets`; the mock implements no
NEP-171/177 (or any) token standard — the mint chain is a data
field on an in-memory record; the ticketing partner on record
is **Tickify** (tickify.io), not "Tickparty"; and the compose
backend contains **no settlement** — call ranking and prize
minting exist only in the partner demo's front-end.

---

## 1. The NEAR-primary hub

**The ruling.** NEAR is the primary mint and the matching
layer — the owner's final topology ruling of 2026-11-12, given
in his own words, superseding the LightLink-mint element of
the earlier design law. The history is short and worth keeping
straight, because the relays muddied it: the integration
(`2a952bb`) was built defaulting to LightLink under the
then-ratified law; the owner reversed the mint topology the
same afternoon; the forward fix (`d350271`) flipped the
default. The other design-law contracts were never in dispute
and stand: venue-as-data, allocation-not-picking, the
provenance invariant, held-back prize inventory, and the
primary-holder gate.

**The minting logic, as coded.** `_mint()` creates each ticket
record with `mintChain: "near"` — a field on the record,
read by the bridge and verify paths. `POST
/api/v1/ticketing/mint` validates event/sector/ring against
the venue-as-data tables, enforces qty 1–10, prices the seat
at `round(sector base × ring factor)`, and creates one record
per seat (§3). There is no NEAR contract call, no NEP-171
mint, no signature: "NEAR-primary" describes where the
production mint will live and what the records assert, and the
mock asserts it as data. Matching's NEAR role is likewise
represented, not executed: derived markets name the NEAR
solver clearing price as their resolution source, and bridge
intents (§2) are the recorded seam where NEAR Intents would
be submitted in production.

## 2. The bridge spokes

`POST /api/v1/ticketing/bridge-intents` accepts a ticket id
and a destination from the closed set `{near, lightlink,
solana, ink, base, robinhood}` (anything else: 422) and
appends one record:

```json
{"id": 1, "ticketId": 1042, "fromChain": "near",
 "toChain": "solana", "status": "mock_recorded"}
```

`fromChain` reads off the ticket's own `mintChain`, so the
topology flip propagated with no bridge-code change. Nothing
moves: no 1Click call, no OmniBridge message, no wrapped
asset. The destinations are the production spokes the record
shape anticipates — LightLink (the Tickify gasless-ticketing
track; Roy Hui advising), Solana (the ecosystem's settlement
home), Ink, Base, and Robinhood Chain — named here as intended
roles, not integrations. Production bridging is a separate
build; this endpoint exists so its seam is visible in the API.

## 3. Per-seat provenance

**Minting granularity.** A qty-N primary purchase creates N
distinct records at the unit price — 4 seats = 4 NFTs — each
with its own sequential id, its own Row/Seat (the assignment
row, seats `seat_start … seat_start+N−1`), and its own
provenance array:

```json
"provenance": [
  {"from": "UZEmarkets (issuer)", "to": "<buyer>", "kind": "Primary mint"},
  {"from": "<seller>", "to": "<buyer>", "kind": "Secondary sale · 612"}
]
```

**The invariant.** Resale never re-mints. `POST
/api/v1/ticketing/transfer` (listed tickets only; unlisted →
409) mutates the same record: owner changes, `acquiredVia`
becomes `"secondary"`, the sale appends to provenance, the id
is untouched. `GET /api/v1/ticketing/verify/{id}` returns the
full chain — the chain **is** the fraud check: any ticket
whose history doesn't walk issuer → … → current owner is not
genuine, and in the mock "genuine" means exactly "this id and
chain exist in the issuer's store."

**Why per-seat matters (the arbitrage surface).** Seat-level
granularity is what makes the rest of the economics possible:
single-seat resale instead of whole-order resale; the
secondary index priced per sector/ring rather than per event;
the Event Market's holder gate evaluated per ticket
(`acquiredVia` is per record, so one primary seat qualifies
its holder while a secondary seat never does); and prize
inventory minted per seat from the held-back allocation.
Whole-order tokens would collapse all four.

## 4. The Delphi prediction bridge

Internal plumbing names (Delphi/Gensyn) stay off every public
surface — the product is the **UZE Event Market**.

**The gate.** `POST /api/v1/delphi/calls` records one scalar
per wallet per subject (event, sector, ring) — the holder's
call for the settled secondary price — and refuses any wallet
that does not hold a **primary** purchase for that event
(403). Secondary holders and prize winners cannot call: you
must own the asset to price its secondary market.

**The transformation.** `GET /api/v1/delphi/markets` turns the
call stream into threshold binary markets: thresholds at the
distribution's quartiles, rounded to the nearest 10 so the
ladder lands on round levels; one market per threshold ("Will
the settled secondary price of a Tribuna Central (Lower Ring)
ticket … exceed R$590?"); initial Yes = the share of calls
above the threshold, at-threshold counting one half — the
empirical seed the bridge spec feeds to an LMSR maker. No
LMSR, order book, or trading exists in the module; markets
return as `"mock_proposed"`.

**Settlement — the honest boundary.** The backend never
settles. Ranking calls by distance to a settled price and
minting the pair/single prize tickets happens **only in the
partner demo's front-end** (`uze-venue-ticketing`, in-page,
against a mock settled price). In production, per the bridge
spec, the resolution source is the actual NEAR solver
clearing price for the subject sector/ring at close; the
settlement connector that consumes it is part of the proposed
build, not this mock.
