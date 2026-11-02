"""Upstream reads for R4 read-through — the reconciliation reader.

The composition layer never joins services/api's database (R4 §8.4);
commit-path reconciliation observes the source of record through
READS. This module is the whole read surface Slice 2 is allowed:
exactly two reads — the referenced Ticket by id and its fulfilling
Listing by id. Nothing else. No inventory projection, no browsing,
no writes: the proxy discipline (directing agent's filing item 2,
2026-11-01) scopes this adapter to COMMIT-PATH RECONCILIATION ONLY,
and the interface is the scope — a caller cannot ask for more
because there is nothing more to ask for.

Two implementations, one interface (ReconciliationReader):

- HttpReconciliationReader — the direct reads: GET /tickets/{id}
  (the narrowed read landed in services/api `53be2f1`: exactly
  {id, eventId, tier, status} — ownerId deliberately excluded; the
  firing map's status branch covers owner changes) and
  GET /listings/{id} (full row). This is the production reader, and
  it becomes usable when the coordinated redeploy makes the ticket
  read live; until then a deployment simply does not configure it.

- ListingReadProxy — THE INTERIM READ (firing map, 2026-10-30:
  "until services/api redeploys, the listing-read proxy is the
  interim reconciliation read"). An in-process stand-in implementing
  the same interface over a caller-supplied dataset shaped like
  services/api rows. It is a development/test adapter: it never
  claims a live upstream answered, and production wiring never
  selects it implicitly. Swapping it for the direct reader when the
  redeploy lands is a factory change, not a call-site change —
  that drop-in property is the point of the interface.

- UnavailableReader — what the app wires when no upstream base URL
  is configured: every read raises UpstreamUnavailable. Honest by
  construction: with the ticket read not yet deployed, a fresh
  snapshot's truth is unobservable, and the reconciliation reports
  exactly that (UPSTREAM_UNAVAILABLE) instead of pretending.

Error vocabulary (mapped from the transport, never invented):
- UpstreamNotFound    — the referenced id returned 404. This is the
  ONLY shape that may become SOURCE_NOT_FOUND: it asserts the
  inventory does not exist.
- UpstreamUnavailable — transport failure, timeout, or 5xx: no
  state could be observed at all (R4 §5, UPSTREAM_UNAVAILABLE). It
  must never be collapsed into NotFound.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol


class UpstreamNotFound(Exception):
    """The referenced id returned 404 at the source of record."""


class UpstreamUnavailable(Exception):
    """No state could be observed: transport failure, timeout, 5xx."""


@dataclass(frozen=True)
class TicketState:
    """A Ticket as the narrowed read projects it (services/api
    GET /tickets/{id}: exactly these four fields)."""

    id: str
    event_id: str
    tier: str
    status: str  # active | listed | transferred | redeemed


@dataclass(frozen=True)
class ListingState:
    """A Listing as GET /listings/{id} returns it (full row)."""

    id: str
    ticket_id: str
    seller_id: str
    price_cents: int
    fee_cents: int
    status: str  # active | sold | cancelled | flagged


class ReconciliationReader(Protocol):
    """The reconciliation read surface — two reads, nothing else."""

    def read_ticket(self, ticket_id: str) -> TicketState: ...

    def read_listing(self, listing_id: str) -> ListingState: ...


# ---------------------------------------------------------------------------
# The interim proxy (pre-redeploy)
# ---------------------------------------------------------------------------


@dataclass
class ListingReadProxy:
    """Interim reconciliation read over a supplied dataset.

    Shaped like services/api rows because it stands in for
    services/api reads; labeled a proxy everywhere it appears so no
    result it produces is ever mistaken for a live observation.
    `unavailable_ids` simulates transport failure per referenced id
    (or pass unavailable=True for total failure) so the
    UPSTREAM_UNAVAILABLE path is exercisable without a network.
    `reads` records every attempted read (kind, id) so tests can
    prove, e.g., that a TTL refusal performed NO upstream read.
    """

    tickets: dict[str, TicketState] = field(default_factory=dict)
    listings: dict[str, ListingState] = field(default_factory=dict)
    unavailable_ids: frozenset[str] = frozenset()
    unavailable: bool = False
    reads: list[tuple[str, str]] = field(default_factory=list)

    def _gate(self, kind: str, ref_id: str) -> None:
        self.reads.append((kind, ref_id))
        if self.unavailable or ref_id in self.unavailable_ids:
            raise UpstreamUnavailable(f"proxy: transport failure for {ref_id}")

    def read_ticket(self, ticket_id: str) -> TicketState:
        self._gate("ticket", ticket_id)
        try:
            return self.tickets[ticket_id]
        except KeyError:
            raise UpstreamNotFound(f"proxy: ticket {ticket_id} -> 404") from None

    def read_listing(self, listing_id: str) -> ListingState:
        self._gate("listing", listing_id)
        try:
            return self.listings[listing_id]
        except KeyError:
            raise UpstreamNotFound(f"proxy: listing {listing_id} -> 404") from None


# ---------------------------------------------------------------------------
# The direct reader (post-redeploy drop-in)
# ---------------------------------------------------------------------------


class HttpReconciliationReader:
    """Direct read-through against a live services/api base URL.

    Reads the APIResponse envelope's `data`. 404 maps to
    UpstreamNotFound; any transport error, timeout, or non-404
    failure status maps to UpstreamUnavailable — a failed read is
    never reported as an absent inventory (R4 §5).
    """

    def __init__(self, base_url: str, timeout: float = 5.0):
        import httpx

        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)

    def _get(self, path: str) -> dict:
        import httpx

        try:
            resp = self._client.get(path)
        except httpx.HTTPError as exc:
            raise UpstreamUnavailable(f"{path}: transport failure: {exc}") from exc
        if resp.status_code == 404:
            raise UpstreamNotFound(f"{path}: 404")
        if resp.status_code != 200:
            raise UpstreamUnavailable(
                f"{path}: unexpected status {resp.status_code}"
            )
        data = resp.json().get("data")
        if not isinstance(data, dict):
            raise UpstreamUnavailable(f"{path}: malformed envelope")
        return data

    def read_ticket(self, ticket_id: str) -> TicketState:
        row = self._get(f"/tickets/{ticket_id}")
        return TicketState(
            id=row["id"],
            event_id=row["eventId"],
            tier=row["tier"],
            status=row["status"],
        )

    def read_listing(self, listing_id: str) -> ListingState:
        row = self._get(f"/listings/{listing_id}")
        return ListingState(
            id=row["id"],
            ticket_id=row["ticketId"],
            seller_id=row["sellerId"],
            price_cents=row["priceCents"],
            fee_cents=row["feeCents"],
            status=row["status"],
        )


class UnavailableReader:
    """No upstream configured: every read is unobservable, stated as
    such. Selected only when COMPOSE_UPSTREAM_BASE_URL is unset."""

    def read_ticket(self, ticket_id: str) -> TicketState:
        raise UpstreamUnavailable("no upstream base URL configured")

    def read_listing(self, listing_id: str) -> ListingState:
        raise UpstreamUnavailable("no upstream base URL configured")


def build_reader() -> ReconciliationReader:
    """Factory — the ONE place the proxy/direct choice is made.

    COMPOSE_UPSTREAM_BASE_URL set -> the direct reader (the
    post-redeploy drop-in). Unset -> UnavailableReader. The interim
    proxy is never selected here: it is constructed explicitly by
    tests and development harnesses that supply its dataset.
    """
    base_url = os.environ.get("COMPOSE_UPSTREAM_BASE_URL")
    if base_url:
        return HttpReconciliationReader(base_url)
    return UnavailableReader()
