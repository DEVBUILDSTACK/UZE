"""R4 read-through — commit-path reconciliation (Sprint 1, slice 2).

Implements R4 §6 (commit-time reconciliation) and §5 (the eight
typed divergence codes) for the TICKET kind, against the contract
(docs/sprint-0/READ-THROUGH-CONTRACT-v0.1.md, DRAFT v0.2) and the
fired filing items (directing agent, 2026-11-01):

  1. The eight codes are wired to the filed firing map (build plan,
     "Divergence-Code Firing Map", 2026-10-30). Evaluation ORDER is
     the contract's: TTL first — at/after `expiresAt`,
     SNAPSHOT_EXPIRED governs and is refused BEFORE any upstream
     read (TTL dominance: repeated transport failures can never
     extend a snapshot's life, and an expired snapshot is never
     reported as UPSTREAM_UNAVAILABLE).
  2. Reads go through upstream.ReconciliationReader, scoped to
     commit-path reconciliation only.
  3. SEAT_TAKEN carries its `reason` — MODERATION |
     DOUBLE_SETTLEMENT — on the EventLog divergence record AND in
     the returned result, so the approval gate (a later slice) can
     surface the true cause in plain language.
  4. The moderated-listing fixture is the first end-to-end
     divergence test (tests/test_readthrough.py).

Recording (R4 §5(d)): every code, when raised, is recorded in
EventLog by THIS module — eventType DIVERGENCE_DETECTED, aggregate
the snapshot, payload carrying the code, the SEAT_TAKEN reason, the
referenced ids, and the observed current state. For killing codes
the module then applies the one permitted annotation write
(divergenceCode/divergenceAt); the DB mirror trigger writes the
authoritative SNAPSHOT_DIVERGED row in the same transaction
(schema-review term 1: the annotation is derived, the EventLog is
authoritative). The mirror's fixed payload cannot carry the reason
or the observed state; this module's record is where they live.
UPSTREAM_UNAVAILABLE is recorded the same way but NEVER annotates:
it blocks without killing (R4 §5).

The two no-writer codes are typed branches below, not surveillance:
they fire if the state is ever observed, and cannot fire today.
Their revisit triggers, named per the filed discipline (build plan,
Post-Map item 3):
  - TICKET_REDEEMED becomes reachable when a redeem endpoint lands
    in services/api (today `redeemed` is a vocabulary state with no
    writer — verified in services/api source, R4 §1.1).
  - PRICE_MOVED becomes reachable when (a) a price-update endpoint
    or a moderation price-change path lands in services/api, or
    (b) the composition layer starts incorporating supplier-side
    price reads that can disagree with the snapshot (today a
    listing's priceCents/feeCents are set at creation and never
    mutated — verified in services/api source, R4 §1.1).

Deliberately NOT evaluated (no code is named for them in R4 §5 or
the firing map, and inventing codes is out of bounds): a tier
mismatch between payload and ticket, and a listing whose ticketId
names a different ticket than the payload's ticketRef.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

import models
from models import DivergenceCode
from upstream import (
    ListingState,
    ReconciliationReader,
    TicketState,
    UpstreamNotFound,
    UpstreamUnavailable,
)

# SEAT_TAKEN reasons (R4 §5 reason precision, 2026-10-30). Plain
# strings: the vocabulary lives in the EventLog payload and the
# read-through result, not in a column enum.
REASON_MODERATION = "MODERATION"
REASON_DOUBLE_SETTLEMENT = "DOUBLE_SETTLEMENT"

SURFACE_COMMIT = "commit"

EVENT_TYPE_DIVERGENCE = "DIVERGENCE_DETECTED"
ACTOR = "system:read-through"


@dataclass(frozen=True)
class Evaluation:
    """The typed outcome of one reconciliation evaluation.

    code is None exactly when the snapshot is CLEAN. kills_snapshot
    is True for every code except UPSTREAM_UNAVAILABLE.
    """

    code: DivergenceCode | None
    reason: str | None = None
    observed: dict | None = None

    @property
    def clean(self) -> bool:
        return self.code is None

    @property
    def kills_snapshot(self) -> bool:
        return self.code is not None and self.code is not DivergenceCode.UPSTREAM_UNAVAILABLE


@dataclass(frozen=True)
class Refs:
    """The upstream references a ticket-kind snapshot binds:
    payload first (ticketRef / listingRef — the ratified seat record
    location), sourceRef as the fallback for whichever the payload
    does not carry (R4 §3: sourceRef is a Ticket id or a Listing id
    per rail)."""

    ticket_id: str | None
    listing_id: str | None


def snapshot_refs(snapshot: models.OfferSnapshot) -> Refs:
    payload = snapshot.payload or {}
    ticket_id = payload.get("ticketRef")
    listing_id = payload.get("listingRef")
    if ticket_id is None and listing_id is None:
        ticket_id = snapshot.source_ref
    elif ticket_id is None:
        # Resale quote: sourceRef names the ticket, payload the listing.
        if snapshot.source_ref != listing_id:
            ticket_id = snapshot.source_ref
    elif listing_id is None and snapshot.source_ref != ticket_id:
        listing_id = snapshot.source_ref
    return Refs(ticket_id=ticket_id, listing_id=listing_id)


def frozen_price_cents(snapshot: models.OfferSnapshot) -> int:
    """The snapshot's frozen price as integer cents, the unit the
    listing read reports (price.amount is a major-unit number)."""
    return int(round(float(snapshot.price["amount"]) * 100))


def evaluate_observed(
    snapshot: models.OfferSnapshot,
    ticket: TicketState,
    listing: ListingState | None,
    settled_mints: frozenset[str],
) -> Evaluation:
    """The firing map over OBSERVED state. Pure: every input is
    explicit, so each branch can be exercised directly. Order is
    the contract's — ticket state before seat fulfillment before
    price (R4 §6.4 names TRANSFERRED / REDEEMED / SEAT_TAKEN /
    LISTING_GONE / PRICE_MOVED in that sequence).
    """
    observed = {
        "ticket": {
            "id": ticket.id,
            "eventId": ticket.event_id,
            "tier": ticket.tier,
            "status": ticket.status,
        },
        "listing": None
        if listing is None
        else {
            "id": listing.id,
            "ticketId": listing.ticket_id,
            "status": listing.status,
            "priceCents": listing.price_cents,
            "feeCents": listing.fee_cents,
        },
    }

    # Ticket state — the status branch detects every owner change
    # reachable through current writers (firing map note 1: the
    # transfer writer sets ownerId + status='transferred' in one
    # update, and the narrowed read returns no ownerId by design).
    if ticket.status == "transferred":
        return Evaluation(DivergenceCode.TICKET_TRANSFERRED, observed=observed)
    if ticket.status == "redeemed":
        # NO-WRITER STUB BRANCH: no services/api endpoint writes
        # `redeemed` today. Revisit trigger: a redeem endpoint
        # landing in services/api makes this reachable.
        return Evaluation(DivergenceCode.TICKET_REDEEMED, observed=observed)

    payload = snapshot.payload or {}

    # Seat fulfillment, trigger (ii): the seat's mint reference
    # already carries a settlement under a DIFFERENT commitment —
    # the composition layer's own double-fulfillment guard.
    mint_ref = payload.get("mintRef")
    if mint_ref is not None and mint_ref in settled_mints:
        return Evaluation(
            DivergenceCode.SEAT_TAKEN,
            reason=REASON_DOUBLE_SETTLEMENT,
            observed=observed,
        )

    if listing is not None:
        if listing.status == "sold":
            # The referenced offer no longer exists as an offer.
            # (Unreachable through current writers — buy is 501 —
            # but in the vocabulary and covered, per R4 §5.)
            return Evaluation(DivergenceCode.LISTING_GONE, observed=observed)
        if listing.status in ("cancelled", "flagged"):
            if ticket.status == "listed":
                # Seat trigger (i): the ticket persists as `listed`
                # but no active Listing fulfills it — moderation
                # removed the fulfillment path without resetting
                # the ticket (the primary divergence driver in the
                # current architecture). The task's moderated-
                # listing fixture fires exactly here.
                return Evaluation(
                    DivergenceCode.SEAT_TAKEN,
                    reason=REASON_MODERATION,
                    observed=observed,
                )
            return Evaluation(DivergenceCode.LISTING_GONE, observed=observed)
        # Listing is active: the frozen-price defense.
        if listing.price_cents != frozen_price_cents(snapshot) or (
            "feeCents" in (snapshot.terms or {})
            and listing.fee_cents != snapshot.terms["feeCents"]
        ):
            # NO-WRITER STUB BRANCH: no services/api code path
            # mutates a listing's price after creation today.
            # Revisit triggers: a price-update endpoint or a
            # moderation price-change path in services/api, or
            # supplier-side price reads entering the composition
            # layer (build plan, Post-Map item 3).
            return Evaluation(DivergenceCode.PRICE_MOVED, observed=observed)

    return Evaluation(None, observed=observed)


def settled_mints_elsewhere(
    session: Session, snapshot: models.OfferSnapshot
) -> frozenset[str]:
    """Mint references that already carry a settlement (a recorded
    chainTxRef) under a commitment against a DIFFERENT snapshot —
    the local half of seat trigger (ii)."""
    rows = (
        session.query(models.OfferSnapshot.payload)
        .join(
            models.Commitment,
            models.Commitment.offer_snapshot_id == models.OfferSnapshot.id,
        )
        .filter(models.Commitment.chain_tx_ref.isnot(None))
        .filter(models.OfferSnapshot.id != snapshot.id)
        .all()
    )
    return frozenset(
        payload["mintRef"]
        for (payload,) in rows
        if isinstance(payload, dict) and payload.get("mintRef")
    )


def _record(
    session: Session,
    snapshot: models.OfferSnapshot,
    refs: Refs,
    evaluation: Evaluation,
) -> None:
    """The R4 §5(d) record: code, reason, referenced ids, observed
    state — in EventLog, append-only, in the caller's transaction."""
    session.add(
        models.EventLog(
            aggregate_type="OfferSnapshot",
            aggregate_id=snapshot.id,
            event_type=EVENT_TYPE_DIVERGENCE,
            actor=ACTOR,
            payload={
                "divergenceCode": evaluation.code.value if evaluation.code else None,
                "reason": evaluation.reason,
                "surface": SURFACE_COMMIT,
                "ticketRef": refs.ticket_id,
                "listingRef": refs.listing_id,
                "sourceRef": snapshot.source_ref,
                "observed": evaluation.observed,
            },
        )
    )


def reconcile(
    session: Session,
    snapshot: models.OfferSnapshot,
    reader: ReconciliationReader,
    *,
    now: datetime | None = None,
) -> Evaluation:
    """Run §6 reconciliation for one ticket-kind snapshot.

    Side effects (one transaction, committed here): the §5(d)
    EventLog record for any raised code, plus the divergence
    annotation for killing codes. A snapshot already carrying an
    annotation is dead: its recorded outcome is returned without
    new reads, new records, or a second annotation (which the
    schema refuses anyway).
    """
    now = now or datetime.now(timezone.utc)
    refs = snapshot_refs(snapshot)

    if snapshot.divergence_code is not None:
        prior = (
            session.query(models.EventLog)
            .filter_by(
                aggregate_type="OfferSnapshot",
                aggregate_id=snapshot.id,
                event_type=EVENT_TYPE_DIVERGENCE,
            )
            .order_by(models.EventLog.id.desc())
            .first()
        )
        return Evaluation(
            snapshot.divergence_code,
            reason=prior.payload.get("reason") if prior else None,
            observed=prior.payload.get("observed") if prior else None,
        )

    # Step 1 — TTL. Refused before reconciliation begins; no
    # upstream read is performed, so transport state is irrelevant
    # (TTL dominance, R4 §5).
    if now >= snapshot.expires_at:
        evaluation = Evaluation(DivergenceCode.SNAPSHOT_EXPIRED, observed=None)
        _record(session, snapshot, refs, evaluation)
        _annotate(session, snapshot, evaluation, now)
        session.commit()
        return evaluation

    # Step 2 — read-through re-read, at request time, of the
    # referenced Ticket and its fulfilling Listing.
    try:
        ticket = reader.read_ticket(refs.ticket_id) if refs.ticket_id else None
        listing = reader.read_listing(refs.listing_id) if refs.listing_id else None
    except UpstreamNotFound:
        evaluation = Evaluation(DivergenceCode.SOURCE_NOT_FOUND, observed=None)
        _record(session, snapshot, refs, evaluation)
        _annotate(session, snapshot, evaluation, now)
        session.commit()
        return evaluation
    except UpstreamUnavailable:
        # Blocks without killing: recorded, never annotated, and
        # never force-fit into SOURCE_NOT_FOUND (R4 §5).
        evaluation = Evaluation(DivergenceCode.UPSTREAM_UNAVAILABLE, observed=None)
        _record(session, snapshot, refs, evaluation)
        session.commit()
        return evaluation

    if ticket is None:
        # A ticket-kind snapshot with no resolvable ticket reference
        # cannot be reconciled; treat the reference itself as the
        # missing source rather than proceeding blind.
        evaluation = Evaluation(DivergenceCode.SOURCE_NOT_FOUND, observed=None)
        _record(session, snapshot, refs, evaluation)
        _annotate(session, snapshot, evaluation, now)
        session.commit()
        return evaluation

    # Steps 3–4 — comparison; divergence is a typed failure.
    evaluation = evaluate_observed(
        snapshot, ticket, listing, settled_mints_elsewhere(session, snapshot)
    )
    if evaluation.code is not None:
        _record(session, snapshot, refs, evaluation)
        _annotate(session, snapshot, evaluation, now)
        session.commit()
    return evaluation


def _annotate(
    session: Session,
    snapshot: models.OfferSnapshot,
    evaluation: Evaluation,
    now: datetime,
) -> None:
    """The one permitted post-insert write (NULL -> code, once).
    The mirror trigger materializes the authoritative
    SNAPSHOT_DIVERGED EventLog row in the same transaction."""
    assert evaluation.kills_snapshot
    snapshot.divergence_code = evaluation.code
    snapshot.divergence_at = now
    session.flush()
