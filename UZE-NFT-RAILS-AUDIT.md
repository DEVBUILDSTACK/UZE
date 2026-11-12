# UZE NFT Rails Audit — For the Lead Engineer

**Audience:** the lead engineer (DeepSeek). **Status: 🟡 BUILT
AS MOCK.** Filed 2026-11-12. File paths, schemas and code logic
for the ticketing + Delphi mock layer as integrated into
DEVBUILDSTACK/UZE. One naming correction up front: the bridge
endpoint is **`POST /api/v1/ticketing/bridge-intents`** — there
is no `/bridge` route. The narrative companion is
`docs/NFT-TOPOLOGY-AUDIT.md`; the executed-numbers record is
`docs/TICKETING-DELPHI-EXECUTION.md`.

---

## 1. The NEAR-primary hub

**File:** `services/compose/src/ticketing.py` (single module,
382 lines; registered in `services/compose/src/app.py` via
`app.include_router(ticketing.router)`).

There is no TicketNFT class and no database table. A ticket is
a dict built by `_mint()` and held in module state. The mint
record, verbatim:

```python
t = {
    "id": tid, "eventId": event["id"], "sector": sector, "ring": ring,
    "row": row, "seat": seat, "price": price, "currency": event["currency"],
    "owner": owner, "mintChain": "near", "acquiredVia": acquired_via,
    "listed": listed,
    "provenance": [{"from": ISSUER, "to": owner, "kind": "Primary mint"}],
}
```

- **NEAR default:** `mintChain: "near"` is set in `_mint()` —
  every record from every path (primary mint, seed) carries it.
  History: integrated as `"lightlink"` in `2a952bb` under the
  then-ratified design law; flipped by the owner's forward fix
  `d350271` after his own-words topology ruling. The bridge
  (§2) reads `fromChain` off this field, so the flip needed no
  bridge change.
- **Per-seat minting:** the `/mint` handler loops
  `range(qty)` (validated 1–10), one `_mint()` per seat, ids
  from a module counter starting at 1042, seats
  `seat_start + i`, each priced at the unit price
  `round(sector.base × ring.factor)`.
- **Provenance storage:** an ordered list on the record itself
  — `{"from", "to", "kind"}` entries. Mint seeds it with the
  issuer entry; transfer appends
  `{"from": seller, "to": buyer, "kind": "Secondary sale · <price>"}`
  and mutates owner/`acquiredVia` on the **same id** — no
  re-mint path exists in the module. State is three module
  globals (`_tickets: dict[int, dict]`, `_calls`, `_bridges`)
  behind a `threading.Lock`; persistence is process memory and
  a restart reseeds the demo fixtures (3 seeded listings, 5
  seeded calls). That is the stated mock boundary, recorded in
  the module docstring.

## 2. The multi-chain bridge intents

```python
CHAINS = {"near", "lightlink", "solana", "ink", "base", "robinhood"}

class BridgeIn(BaseModel):
    ticket_id: int
    to_chain: str

@router.post("/api/v1/ticketing/bridge-intents")
def bridge_intent(body: BridgeIn) -> dict[str, Any]:
    # A RECORDED mock bridge intent (NEAR Intents / OmniBridge
    # seam). Nothing moves; production bridging is separate.
    t = _tickets.get(body.ticket_id)
    if t is None:
        raise HTTPException(404, "ticket not found")
    if body.to_chain not in CHAINS:
        raise HTTPException(422, f"unsupported chain: {body.to_chain}")
    rec = {
        "id": len(_bridges) + 1, "ticketId": t["id"],
        "fromChain": t["mintChain"], "toChain": body.to_chain,
        "status": "mock_recorded",
    }
    _bridges.append(rec)
    return {"status": "mock", "bridgeIntent": rec}
```

(In the source, the two comment lines above are the handler's
docstring; rendered as comments here for this document's
formatting.)

The exact payload generated for a NEAR → Solana intent:

```json
{"status": "mock",
 "bridgeIntent": {"id": 1, "ticketId": 1042, "fromChain": "near",
                  "toChain": "solana", "status": "mock_recorded"}}
```

Representation only: the intent is an append to an in-memory
list. No 1Click request, no OmniBridge message, no asset
movement — the record is the seam where production bridging
plugs in (`docs/GENSYN-BRIDGE-SPEC.md`, 🔴 PROPOSAL).

## 3. The Delphi market bridge

**The gate** — `POST /api/v1/delphi/calls`, before any call is
recorded (DESIGN-RULES rule 6):

```python
holds_primary = any(
    t["owner"] == body.wallet and t["acquiredVia"] == "primary"
    and t["eventId"] == ev["id"]
    for t in _tickets.values()
)
if not holds_primary:
    raise HTTPException(403, "calls require holding a primary-market purchase for this event")
```

**The transformation** — `GET /api/v1/delphi/markets`
(`derive_markets`): the subject's scalar call stream, sorted;
thresholds at the quartiles, rounded to the nearest 10; initial
Yes as the above-threshold share with at-threshold counting
one half:

```python
def pct(q: float) -> float:
    return stream[min(n - 1, max(0, int(q * n)))]

thresholds = sorted({round(pct(q) / 10) * 10 for q in (0.25, 0.5, 0.75)})
for th in thresholds:
    above = sum(1.0 if c > th else 0.5 if c == th else 0.0 for c in stream)
    markets.append({
        "marketId": f"em-{ev['id']}-{sector.lower().replace(' ', '-')}-{th}",
        "question": (f"Will the settled secondary price of a {sector} ({ring}) "
                     f"ticket for {ev['name']} exceed {ev['currency']}{th}?"),
        "subject": {"eventId": ev["id"], "sector": sector, "ring": ring},
        "outcomes": ["Yes", "No"],
        "threshold": th, "currency": ev["currency"],
        "initialYes": round(above / n, 3),
        "resolutionSource": "The actual secondary clearing price produced by "
                            "NEAR solver matching for the subject sector/ring at market close",
        "settlementCriteria": "Yes if clearingPrice > threshold at close; No otherwise",
        "eligibility": "Holders of a primary-market purchase for the subject event",
        "status": "mock_proposed",
    })
```

That dict **is** the DelphiMarket object as built — there is no
separate schema class. Executed on the seeded soccer stream
{488, 540, 588, 645, 701} it yields thresholds 540 / 590 / 640
with initialYes 0.7 / 0.4 / 0.4. `initialYes` is the empirical
seed for the spec's LMSR maker; no LMSR runs in this module,
and no settlement exists in the backend at all — ranking and
prize minting live only in the venue demo's front-end.

## 4. Repo integration & isolation

**How it landed.** One self-contained module plus one router
registration line; no existing module was edited except
`app.py`'s include list:

```
services/compose/src/ticketing.py            (new, 382 lines)
services/compose/src/app.py                  (+import, +include_router)
services/compose/tests/test_ticketing.py     (new, 7 tests)
docs/GENSYN-BRIDGE-SPEC.md                  (copied from the venue repo)
README.md / PARTNER-SHARE.md                 (status-labelled sections)
```

Suite arithmetic: the pre-integration baseline was **286
passed**. The integration commit `2a952bb` reported **300**
(+7 alpha signups, +7 ticketing). The suite has since grown
through the owner's subsequent taps to **312**, with the
ticketing tests untouched since integration — the isolation
claim is simply that the module's only coupling to the rest of
the service is its router registration and the shared test
substrate.

**Proof it is a mock.** The module's complete import block:

```python
import threading
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
```

No web3, NEAR, LightLink, or Gensyn client exists in the file;
no HTTP client at all. Every handler returns `"status": "mock"`
(or `"mock_proposed"` for derived markets); every state change
is a dict/list mutation in process memory. There is no
background task, no RPC endpoint configured, and no code path
by which the module could execute a chain call — the absence
is structural, not configurational.
