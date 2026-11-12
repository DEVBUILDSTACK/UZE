# Ticketing + Delphi Execution — How the Integrated Mock Actually Works

**Status: 🟡 BUILT AS MOCK.** Filed 2026-11-12. Documents commit `2a952bb`
exactly as built: `services/compose/src/ticketing.py` (382 lines, one
module — there is no `delphi.py`; the Delphi endpoints live in the same
file). Every section separates **Real code** from **Mock / not built**.

**Topology as built:** tickets carry `mintChain: "near"` — **NEAR is
the primary mint** under the owner's final topology ruling of
2026-11-12 (given in his own words, superseding the earlier
LightLink-mint design law in `DESIGN-RULES.md`,
DEVBUILDSTACK/uze-venue-ticketing; the module originally integrated
in `2a952bb` defaulted to LightLink, and the owner's forward fix
flipped the default the same day). The original NFT still transfers
on resale — the provenance invariant is unchanged. LightLink, Solana,
Ink, Base and Robinhood are bridge destinations. NEAR appears in this
module as the mint chain of record, as a permitted bridge-intent
destination, and as the named resolution source for solver clearing
prices (the matching layer). `mintChain` is stored as data on each
ticket.

---

## 1. The NFT stack (NEAR mint & bridging)

### The ticket record — Real code, in-memory

There is no `TicketNFT` class and **no database table**. A ticket is a
plain dict created by `_mint()` and held in the module-level store
`_tickets: dict[int, dict]`. The store is process memory: it resets on
restart. (Persistence is a post-hackathon migration, same batch as the
alpha-signups table.)

| Field | Meaning |
|---|---|
| `id` | Sequential integer from a counter starting at 1042 |
| `eventId` | One of the seven venue-as-data event ids |
| `sector` / `ring` | The price area chosen (venue-as-data names, never code) |
| `row` / `seat` | Per-seat identity: `row` from the request, `seat = seat_start + i` for seat *i* of the order |
| `price` / `currency` | Unit price actually paid; event currency (`R$` / `$`) |
| `owner` | Current holder wallet string |
| `mintChain` | `"near"` on every minted record (owner's topology ruling, 2026-11-12) |
| `acquiredVia` | `"primary"` (mint endpoint), `"secondary"` (transfer), `"prize"` reserved |
| `listed` | Resale ask price, or `null` when not listed |
| `provenance` | Ordered list of `{"from", "to", "kind"}` entries — the fraud check |

### Minting — `POST /api/v1/ticketing/mint` — Real logic, mock chain

Validation: `qty` must be 1–10 (else 422); the wallet string must be at
least 8 characters (else 422); sector and ring must exist in the event's
venue-as-data (else 422). Unit price is `round(sector.base × ring.factor)`
— e.g. Tribuna Central (base 420) × Lower Ring (1.15) = **483**.

Per-seat minting is real: a qty-4 order creates **four distinct records**,
four consecutive ids, seats `seat_start … seat_start+3`, each priced at
the unit price, each with its own provenance chain seeded with one entry:

```json
{"from": "UZEmarkets (issuer)", "to": "<buyer wallet>", "kind": "Primary mint"}
```

**Mock boundary:** the "NEAR mint attestation" is not simulated
cryptographically. The endpoint stamps `mintChain: "near"` as data
and records the issuer as the first provenance entry. No NEAR or
LightLink RPC call, no contract, no signature exists in this module. (The REE receipt
and attestation badges in the partner demo are front-end presentation in
the venue repo, not backend cryptography.)

### Resale — Real invariant enforcement

- `POST /api/v1/ticketing/list` — owner only (403 otherwise), price must
  be positive (422).
- `POST /api/v1/ticketing/transfer` — 409 if the ticket is not listed.
  The transfer **mutates the same record**: same `id`, owner changes,
  `acquiredVia` becomes `"secondary"`, and provenance gains
  `{"from": <seller>, "to": <buyer>, "kind": "Secondary sale · <price>"}`.
  No re-mint path exists anywhere in the module — the provenance
  invariant is enforced by there being nothing else to call.
- `GET /api/v1/ticketing/verify/{id}` — returns the full provenance
  chain and `genuine: true`. **Mock boundary:** "genuine" means "this id
  exists in the issuer's store," not a cryptographic verification.

### Bridge intents — `POST /api/v1/ticketing/bridge-intents` — Recorded, never executed

(The directive that requested this document called this `bridge_asset`;
the endpoint as built is `bridge-intents`.)

The request names a ticket and a `to_chain` from the closed set
`{near, lightlink, solana, ink, base, robinhood}` (else 422). The module
appends one record to an in-memory list:

```json
{"id": 1, "ticketId": 1042, "fromChain": "near", "toChain": "solana", "status": "mock_recorded"}
```

**Mock boundary:** that is the entire implementation. No NEAR Intents
1Click call, no OmniBridge message, no asset movement of any kind. The
record exists so the seam — where a production intent would be
submitted — is visible in the API shape.

---

## 2. The Delphi connection (threshold information markets)

Specification: `docs/GENSYN-BRIDGE-SPEC.md`. Delphi and Gensyn are
internal plumbing names; the public product name is **UZE Event
Market**, and neither name appears in any response payload.

### Step 1 — the scalar call — `POST /api/v1/delphi/calls`

A holder submits one number: their call for the settled secondary price
of a subject (event, sector, ring), e.g. `600` for Tribuna Central /
Lower Ring at the soccer fixture.

**The gate is real code** (DESIGN-RULES rule 6). Before recording, the
endpoint scans the ticket store for any ticket where
`owner == wallet AND acquiredVia == "primary" AND eventId == event`.
If none exists, the call is refused:

```
403 — "calls require holding a primary-market purchase for this event"
```

Secondary purchases and prize wins do not satisfy the gate — the check
is on `acquiredVia`, not on mere possession. One call per wallet per
subject: resubmitting overwrites the wallet's previous call.

### Step 2 — the transformation — `GET /api/v1/delphi/markets`

Given the subject's call stream (sorted list of scalars), and requiring
at least two calls:

1. **Thresholds** are taken at the distribution's quartiles
   (25th / 50th / 75th percentile by index), each **rounded to the
   nearest 10** — the ladder deliberately lands on round levels instead
   of stepping around them.
2. **One binary market per threshold.** The question is generated from
   the subject, e.g. *"Will the settled secondary price of a Tribuna
   Central (Lower Ring) ticket for Internacional vs São Paulo FC exceed
   R$590?"*
3. **Initial Yes** = share of calls above the threshold, with a call
   exactly at the threshold counting one half:
   `initialYes = (count(c > th) + 0.5 × count(c == th)) / n`.

Worked example, verified by executing the function on the seeded
soccer stream `{488, 540, 588, 645, 701}`: the quartile thresholds come
out **540 / 590 / 640**, and the exceed-590 market opens at
`initialYes = 2/5 = 0.4` (the exceed-540 market opens at 0.7 — three
calls above, the at-threshold call counting one half).

**Mock boundary:** `initialYes` is the empirical share the bridge spec
uses as the *seed input* to an LMSR market maker. No LMSR curve, order
book, or trading exists in this module — markets are derived and
returned with status `"mock_proposed"`, and nothing here settles them.

### The market object — Real schema

```json
{
  "marketId": "em-soccer-tribuna-central-590",
  "question": "Will the settled secondary price of a Tribuna Central (Lower Ring) ticket for Internacional vs São Paulo FC exceed R$590?",
  "subject": {"eventId": "soccer", "sector": "Tribuna Central", "ring": "Lower Ring"},
  "outcomes": ["Yes", "No"],
  "threshold": 590,
  "currency": "R$",
  "initialYes": 0.4,
  "resolutionSource": "The actual secondary clearing price produced by NEAR solver matching for the subject sector/ring at market close",
  "settlementCriteria": "Yes if clearingPrice > threshold at close; No otherwise",
  "eligibility": "Holders of a primary-market purchase for the subject event",
  "status": "mock_proposed"
}
```

(Field names are camelCase as built — `resolutionSource`,
`settlementCriteria` — not the snake_case the requesting directive used.)

---

## 3. Execution flow, traced through the code

1. **Buy 4 seats** — `POST /api/v1/ticketing/mint {event_id: "soccer",
   sector: "Tribuna Central", ring: "Lower Ring", qty: 4, wallet,
   seat_start: 5}` → four records, ids consecutive from the counter,
   seats 5–8, R$483 each, `acquiredVia: "primary"`, one provenance entry
   each. Response: `{"status": "mock", "unitPrice": 483, "tickets": […]}`.
2. **Call a price** — `POST /api/v1/delphi/calls {…, call: 600}` → the
   gate finds the step-1 primary tickets → the call is recorded in
   `_calls[(event, sector, ring)][wallet]`.
3. **Markets derive** — `GET /api/v1/delphi/markets?event_id=soccer&…`
   → quartile thresholds over all recorded calls for the subject, one
   market object per threshold, as in §2.
4. **Settlement and prizes — NOT IN THIS BACKEND.** There is no settle
   endpoint, no ranking function, and no prize minting in
   `ticketing.py`. Ranking calls against a settled price and minting
   the pair/single prize tickets exists **only in the partner demo's
   front-end** (`src/app.js` in DEVBUILDSTACK/uze-venue-ticketing,
   in-page, against a mock settled price). Any document claiming the
   compose backend settles Event Markets is wrong; production
   settlement — solver clearing price in, ranking and prize minting
   from the held-back primary allocation out — is the proposed build
   in `docs/GENSYN-BRIDGE-SPEC.md`.

Seed data, for reproducibility: three seeded soccer listings
(`acquiredVia: "secondary"`, listed at 460 / 165 / 285) and five seeded
calls on the soccer focus subject `{488, 540, 588, 645, 701}`.

---

## 4. Real vs. mock — the honesty ledger

**Real (code that executes and is tested):**

- FastAPI routing and the full error contract (422 unknown
  event/sector/ring or bad qty · 403 non-owner listing and non-holder
  call · 404 unknown ticket · 409 unlisted transfer).
- Venue-as-data: seven events as sector × ring tables, consumed by the
  pricing function — new venues are new data rows.
- Per-seat minting arithmetic and record creation; the provenance
  append-only transfer logic; the holder gate; one-call-per-wallet.
- The call-stream → threshold-ladder transformation, including the
  quartile selection, round-level rounding, and the at-threshold
  one-half rule for `initialYes`.
- Seven tests in `services/compose/tests/test_ticketing.py`; the module
  ships inside the 300-test suite.

**Mock / not built (named so nobody has to guess):**

- **Persistence.** In-memory dicts and lists. There are no database
  tables for ticketing or calls; a restart reseeds the demo state.
- **Every blockchain interaction.** No on-chain mint on NEAR or any
  other chain, no bridge execution, no USDC settlement. `mintChain` is a data field;
  bridge intents are records with status `"mock_recorded"`.
- **The Gensyn/Delphi integration.** No SDK, no network call. The
  transformation above is a local function implementing the filed
  bridge spec; its outputs are labelled `"mock_proposed"`.
- **Settlement.** No clearing price is consumed, no market resolves,
  no prize is minted by this backend (§3, step 4).
- **Attestation.** Provenance is an issuer-kept list, not a signed or
  on-chain proof; `verify` is a store lookup.
