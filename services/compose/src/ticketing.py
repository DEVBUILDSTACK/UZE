"""Ticketing + Delphi mock layer — integrated per OWNER OVERRIDE (2026-11-12).

The owner explicitly overrode the standing hackathon boundary on
2026-11-12 to integrate the venue-ticketing and information-market
schemas into this repository AS MOCKS. Everything here is in-memory,
labelled MOCK in every response, and settles nothing. The governing
design law is DESIGN-RULES.md in DEVBUILDSTACK/uze-venue-ticketing:

  - venue-as-data: an event is sectors x rings, never code;
  - allocation-not-picking at the UX layer (this API mints per seat);
  - provenance invariant: on resale the ORIGINAL ticket transfers —
    the id never changes and no re-mint occurs;
  - matching stays on NEAR (bridge intents below are records, not
    executions);
  - Event Market prizes come from the held-back primary allocation;
  - price calls require holding a primary-market purchase for the
    event (sybil resistance).

Ticket minting defaults to NEAR — the owner's final topology
ruling of 2026-11-12, given in his own words and superseding the
earlier LightLink-mint design law: NEAR is the primary mint and
the matching layer; LightLink, Solana, Ink, Base and Robinhood
are bridge destinations (the bridge intents below). `mintChain`
is recorded as data on every ticket.

The Delphi endpoints implement the transformation specified in
docs/GENSYN-BRIDGE-SPEC.md: scalar holder calls -> empirical
distribution -> threshold binary markets seeded by the share of calls
above each threshold. Markets are PROPOSED (mock), never settled here.

The server seed carries a reduced sector set for some events; the
full venue tables live in the demo (src/venue-data.js of the venue
repo) and are the data of record.
"""

from __future__ import annotations

import threading
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["ticketing"])

ISSUER = "UZEmarkets (issuer)"
CHAINS = {"near", "lightlink", "solana", "ink", "base", "robinhood"}

_RINGS = [
    {"name": "Lower Ring", "factor": 1.15},
    {"name": "Middle Ring", "factor": 1.0},
    {"name": "Upper Ring", "factor": 0.8},
]

EVENTS: list[dict[str, Any]] = [
    {
        "id": "soccer", "name": "Internacional vs São Paulo FC",
        "venue": "Estádio Beira-Rio", "city": "Porto Alegre", "kind": "soccer",
        "currency": "R$",
        "sectors": [
            {"name": "Tribuna Central", "base": 420},
            {"name": "Lateral Central", "base": 330},
            {"name": "Gol Nord", "base": 150},
        ],
        "rings": _RINGS,
        "focus": {"sector": "Tribuna Central", "ring": "Lower Ring"},
    },
    {
        "id": "music", "name": "Porto Alegre Music Nights",
        "venue": "Arena Bowl", "city": "Porto Alegre", "kind": "music",
        "currency": "R$",
        "sectors": [
            {"name": "Palco — Front Stage", "base": 690},
            {"name": "Camarote VIP", "base": 890},
            {"name": "Pista · North", "base": 290},
        ],
        "rings": _RINGS,
        "focus": {"sector": "Camarote VIP", "ring": "Lower Ring"},
    },
    {
        "id": "summit", "name": "South Summit Brazil 2027",
        "venue": "Cais Embarcadero", "city": "Porto Alegre", "kind": "summit",
        "currency": "R$",
        "sectors": [
            {"name": "Plenary — Main Stage", "base": 1490},
            {"name": "Investor Lounge", "base": 2990},
            {"name": "Expo Floor · North", "base": 490},
        ],
        "rings": [
            {"name": "Attendee Pass", "factor": 1.0},
            {"name": "Startup Pass", "factor": 1.35},
            {"name": "Executive Pass", "factor": 2.1},
        ],
        "focus": {"sector": "Plenary — Main Stage", "ring": "Executive Pass"},
    },
    {
        "id": "f1-miami", "name": "F1 Miami Grand Prix 2027",
        "venue": "Miami International Autodrome", "city": "Miami", "kind": "f1",
        "currency": "$",
        "sectors": [
            {"name": "Start/Finish Grandstand", "base": 890},
            {"name": "Paddock Club Hospitality", "base": 4900},
            {"name": "Campus Pass — GA · North", "base": 290},
        ],
        "rings": _RINGS,
        "focus": {"sector": "Start/Finish Grandstand", "ring": "Lower Ring"},
    },
    {
        "id": "f1-vegas", "name": "F1 Las Vegas Grand Prix 2027",
        "venue": "Las Vegas Strip Circuit", "city": "Las Vegas", "kind": "f1",
        "currency": "$",
        "sectors": [{"name": "Main Grandstand", "base": 1050}],
        "rings": _RINGS,
        "focus": {"sector": "Main Grandstand", "ring": "Lower Ring"},
    },
    {
        "id": "f1-austin", "name": "F1 Austin Grand Prix 2027",
        "venue": "Circuit of the Americas", "city": "Austin", "kind": "f1",
        "currency": "$",
        "sectors": [{"name": "Main Grandstand", "base": 950}],
        "rings": _RINGS,
        "focus": {"sector": "Main Grandstand", "ring": "Lower Ring"},
    },
    {
        "id": "la28", "name": "LA28 Olympics",
        "venue": "LA28 Showcase", "city": "Los Angeles", "kind": "la28",
        "currency": "$",
        "sectors": [
            {"name": "Basketball — Lower Bowl · North", "base": 650},
            {"name": "Aquatics — Pool Deck Premium", "base": 890},
            {"name": "Lacrosse Sixes — Grandstand", "base": 320},
            {"name": "Surfing — Trestles Premium · North", "base": 210},
        ],
        "rings": _RINGS,
        "focus": {"sector": "Basketball — Lower Bowl · North", "ring": "Lower Ring"},
    },
]
_EVENT_BY_ID = {e["id"]: e for e in EVENTS}

_lock = threading.Lock()
_counter = [1042]
_tickets: dict[int, dict[str, Any]] = {}
_calls: dict[tuple[str, str, str], dict[str, float]] = {}
_bridges: list[dict[str, Any]] = []


def _price(event: dict[str, Any], sector_name: str, ring_name: str) -> int:
    sector = next((s for s in event["sectors"] if s["name"] == sector_name), None)
    ring = next((r for r in event["rings"] if r["name"] == ring_name), None)
    if sector is None or ring is None:
        raise HTTPException(422, f"unknown sector/ring for event {event['id']}: {sector_name} / {ring_name}")
    return round(sector["base"] * ring["factor"])


def _event_or_422(event_id: str) -> dict[str, Any]:
    ev = _EVENT_BY_ID.get(event_id)
    if ev is None:
        raise HTTPException(422, f"unknown event: {event_id}")
    return ev


def _mint(event: dict[str, Any], sector: str, ring: str, price: int, owner: str,
          acquired_via: str, row: int | None = None, seat: int | None = None,
          listed: int | None = None) -> dict[str, Any]:
    tid = _counter[0]
    _counter[0] += 1
    t = {
        "id": tid, "eventId": event["id"], "sector": sector, "ring": ring,
        "row": row, "seat": seat, "price": price, "currency": event["currency"],
        "owner": owner, "mintChain": "near", "acquiredVia": acquired_via,
        "listed": listed,
        "provenance": [{"from": ISSUER, "to": owner, "kind": "Primary mint"}],
    }
    _tickets[tid] = t
    return t


def _seed() -> None:
    if _tickets:
        return
    soccer = _EVENT_BY_ID["soccer"]
    for sector, ring, price in [
        ("Tribuna Central", "Lower Ring", 460),
        ("Gol Nord", "Middle Ring", 165),
        ("Lateral Central", "Upper Ring", 285),
    ]:
        _mint(soccer, sector, ring, price, f"0xseed{_counter[0]}", "secondary", listed=price)
    focus = soccer["focus"]
    key = (soccer["id"], focus["sector"], focus["ring"])
    _calls[key] = {f"0xseedcaller{i}": float(v) for i, v in enumerate([540, 588, 645, 701, 488])}


_seed()


class MintIn(BaseModel):
    event_id: str
    sector: str
    ring: str
    qty: int
    wallet: str
    row: int | None = None
    seat_start: int | None = None


class ListIn(BaseModel):
    ticket_id: int
    wallet: str
    price: int


class TransferIn(BaseModel):
    ticket_id: int
    to_wallet: str


class BridgeIn(BaseModel):
    ticket_id: int
    to_chain: str


class CallIn(BaseModel):
    event_id: str
    sector: str
    ring: str
    wallet: str
    call: float


@router.get("/api/v1/ticketing/events")
def list_events() -> dict[str, Any]:
    return {"status": "mock", "events": EVENTS}


@router.get("/api/v1/ticketing/events/{event_id}")
def get_event(event_id: str) -> dict[str, Any]:
    return {"status": "mock", "event": _event_or_422(event_id)}


@router.post("/api/v1/ticketing/mint")
def mint(body: MintIn) -> dict[str, Any]:
    """Per-seat minting: qty N mints N distinct TicketNFT records at the
    unit sector price, each with its own seat and provenance chain."""
    ev = _event_or_422(body.event_id)
    if not 1 <= body.qty <= 10:
        raise HTTPException(422, "qty must be between 1 and 10")
    if len(body.wallet) < 8:
        raise HTTPException(422, "wallet looks invalid")
    unit = _price(ev, body.sector, body.ring)
    with _lock:
        minted = [
            _mint(ev, body.sector, body.ring, unit, body.wallet, "primary",
                  row=body.row, seat=(body.seat_start + i) if body.seat_start else None)
            for i in range(body.qty)
        ]
    return {"status": "mock", "unitPrice": unit, "tickets": minted}


@router.post("/api/v1/ticketing/list")
def list_ticket(body: ListIn) -> dict[str, Any]:
    t = _tickets.get(body.ticket_id)
    if t is None:
        raise HTTPException(404, "ticket not found")
    if t["owner"] != body.wallet:
        raise HTTPException(403, "only the owner can list a ticket")
    if body.price <= 0:
        raise HTTPException(422, "price must be positive")
    t["listed"] = body.price
    return {"status": "mock", "ticket": t}


@router.post("/api/v1/ticketing/transfer")
def transfer(body: TransferIn) -> dict[str, Any]:
    """Secondary sale under the provenance invariant: the ORIGINAL
    ticket transfers — same id, provenance appended, never re-minted."""
    t = _tickets.get(body.ticket_id)
    if t is None:
        raise HTTPException(404, "ticket not found")
    if not t["listed"]:
        raise HTTPException(409, "ticket is not listed for resale")
    paid = t["listed"]
    t["provenance"].append({"from": t["owner"], "to": body.to_wallet, "kind": f"Secondary sale · {paid}"})
    t["owner"] = body.to_wallet
    t["price"] = paid
    t["listed"] = None
    t["acquiredVia"] = "secondary"
    return {"status": "mock", "ticket": t}


@router.get("/api/v1/ticketing/verify/{ticket_id}")
def verify(ticket_id: int) -> dict[str, Any]:
    t = _tickets.get(ticket_id)
    if t is None:
        raise HTTPException(404, "ticket not found")
    return {
        "status": "mock", "genuine": True, "issuer": ISSUER,
        "ticketId": t["id"], "mintChain": t["mintChain"],
        "currentOwner": t["owner"], "provenance": t["provenance"],
    }


@router.post("/api/v1/ticketing/bridge-intents")
def bridge_intent(body: BridgeIn) -> dict[str, Any]:
    """A RECORDED mock bridge intent (NEAR Intents / OmniBridge seam).
    Nothing moves; production bridging is a separate build."""
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


@router.post("/api/v1/delphi/calls")
def submit_call(body: CallIn) -> dict[str, Any]:
    """Holder-gated scalar price call (DESIGN-RULES rule 6): the
    wallet must hold a primary-market purchase for this event."""
    ev = _event_or_422(body.event_id)
    _price(ev, body.sector, body.ring)
    if body.call <= 0:
        raise HTTPException(422, "call must be positive")
    holds_primary = any(
        t["owner"] == body.wallet and t["acquiredVia"] == "primary" and t["eventId"] == ev["id"]
        for t in _tickets.values()
    )
    if not holds_primary:
        raise HTTPException(403, "calls require holding a primary-market purchase for this event")
    key = (ev["id"], body.sector, body.ring)
    with _lock:
        _calls.setdefault(key, {})[body.wallet] = float(body.call)
    return {"status": "mock", "recorded": {"wallet": body.wallet, "call": body.call, "subject": key}}


@router.get("/api/v1/delphi/calls")
def list_calls(event_id: str, sector: str, ring: str) -> dict[str, Any]:
    ev = _event_or_422(event_id)
    stream = _calls.get((ev["id"], sector, ring), {})
    return {"status": "mock", "subject": [ev["id"], sector, ring],
            "calls": [{"wallet": w, "call": c} for w, c in sorted(stream.items())]}


@router.get("/api/v1/delphi/markets")
def derive_markets(event_id: str, sector: str, ring: str) -> dict[str, Any]:
    """The bridge-spec transformation: the scalar call stream becomes
    threshold binary markets. Thresholds sit at the call distribution's
    quartiles rounded to the nearest 10 — and the ladder lands on round
    levels rather than stepping around them. Initial Yes = share of
    calls above the threshold (a call exactly at it counts one half)."""
    ev = _event_or_422(event_id)
    stream = sorted(_calls.get((ev["id"], sector, ring), {}).values())
    if len(stream) < 2:
        return {"status": "mock_proposed", "markets": [], "note": "at least two calls are required to derive a ladder"}
    n = len(stream)

    def pct(q: float) -> float:
        return stream[min(n - 1, max(0, int(q * n)))]

    thresholds = sorted({round(pct(q) / 10) * 10 for q in (0.25, 0.5, 0.75)})
    markets = []
    for th in thresholds:
        above = sum(1.0 if c > th else 0.5 if c == th else 0.0 for c in stream)
        markets.append({
            "marketId": f"em-{ev['id']}-{sector.lower().replace(' ', '-')}-{th}",
            "question": (
                f"Will the settled secondary price of a {sector} ({ring}) ticket "
                f"for {ev['name']} exceed {ev['currency']}{th}?"
            ),
            "subject": {"eventId": ev["id"], "sector": sector, "ring": ring},
            "outcomes": ["Yes", "No"],
            "threshold": th, "currency": ev["currency"],
            "initialYes": round(above / n, 3),
            "resolutionSource": "The actual secondary clearing price produced by NEAR solver matching for the subject sector/ring at market close",
            "settlementCriteria": "Yes if clearingPrice > threshold at close; No otherwise",
            "eligibility": "Holders of a primary-market purchase for the subject event",
            "status": "mock_proposed",
        })
    return {"status": "mock_proposed", "callsObserved": n, "markets": markets}
