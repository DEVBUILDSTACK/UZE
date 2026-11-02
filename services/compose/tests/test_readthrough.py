"""Sprint 1 slice 2 — R4 read-through reconciliation, end to end.

Substrate: the REAL migrated Postgres (conftest's session fixture)
for snapshots, EventLog, and commitments; the upstream source of
record is the interim LISTING-READ PROXY (upstream.ListingReadProxy)
seeded with rows shaped like services/api's — the pre-redeploy
interim read the firing map names. No live services/api is claimed:
the proxy is a labeled stand-in behind the ReconciliationReader
interface, and the direct HTTP reader drops in behind the same
interface when the redeploy lands.

Every test can fail against intended behavior: each seeds upstream
state that MUST produce a specific typed outcome (or none), then
asserts the HTTP result, the EventLog record, and the snapshot
annotation — the three places R4 says the outcome must land.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import db
import models
import snapshots as snapshots_module
from app import create_app
from upstream import ListingReadProxy, ListingState, TicketState

NOW = datetime.now(timezone.utc)


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def ticket_state(ticket_id: str, status: str = "listed", tier: str = "general"):
    return TicketState(id=ticket_id, event_id="evt-1", tier=tier, status=status)


def listing_state(
    listing_id: str,
    ticket_id: str,
    status: str = "active",
    price_cents: int = 12050,
    fee_cents: int = 250,
):
    return ListingState(
        id=listing_id,
        ticket_id=ticket_id,
        seller_id="seller-1",
        price_cents=price_cents,
        fee_cents=fee_cents,
        status=status,
    )


def make_snapshot(
    *,
    ticket_ref: str,
    listing_ref: str | None,
    mint_ref: str | None = None,
    expired: bool = False,
    price_amount: float = 120.50,
    fee_cents: int = 250,
    kind: str = "ticket",
) -> str:
    """Persist a snapshot chain (TripProfile -> SearchSession ->
    TripCandidate -> OfferSnapshot) and return the snapshot id."""
    session = db.session()
    try:
        trip = models.TripProfile(
            buyer_id="buyer-1",
            modules=[models.ModuleType.TICKETS],
            authorization={},
        )
        session.add(trip)
        session.flush()
        search = models.SearchSession(trip_profile_id=trip.id, query={})
        session.add(search)
        session.flush()
        candidate = models.TripCandidate(search_session_id=search.id, constraints={})
        session.add(candidate)
        session.flush()
        if kind == "ticket":
            payload = {
                "kind": "ticket",
                "seat": "A1",
                "tier": "general",
                "gate": "G1",
                "ticketRef": ticket_ref,
            }
            if listing_ref is not None:
                payload["listingRef"] = listing_ref
            if mint_ref is not None:
                payload["mintRef"] = mint_ref
        else:
            payload = {"kind": kind, "phaseKind": "EVENT", "nights": 2}
        snapshot = models.OfferSnapshot(
            trip_candidate_id=candidate.id,
            rail=models.Rail.SOLANA_NFT,
            source_ref=listing_ref or ticket_ref,
            commitment_class=models.CommitmentClass.IRREVERSIBLE_ON_CHAIN,
            price={
                "amount": price_amount,
                "currency": "USDC",
                "taxesIncluded": True,
            },
            terms={"feeCents": fee_cents},
            payload=payload,
            expires_at=NOW - timedelta(hours=1)
            if expired
            else NOW + timedelta(hours=1),
        )
        session.add(snapshot)
        session.commit()
        return snapshot.id
    finally:
        session.close()


def client_for(proxy: ListingReadProxy) -> TestClient:
    app = create_app()
    app.dependency_overrides[snapshots_module.get_reader] = lambda: proxy
    return TestClient(app, raise_server_exceptions=False)


def reconcile(client: TestClient, snapshot_id: str):
    return client.post(f"/snapshots/{snapshot_id}/reconcile")


def divergence_rows(snapshot_id: str, event_type: str = "DIVERGENCE_DETECTED"):
    session = db.session()
    try:
        return (
            session.query(models.EventLog)
            .filter_by(
                aggregate_type="OfferSnapshot",
                aggregate_id=snapshot_id,
                event_type=event_type,
            )
            .order_by(models.EventLog.id.asc())
            .all()
        )
    finally:
        session.close()


def snapshot_row(snapshot_id: str) -> models.OfferSnapshot:
    session = db.session()
    try:
        row = session.get(models.OfferSnapshot, snapshot_id)
        session.expunge(row)
        return row
    finally:
        session.close()


@pytest.fixture()
def ids():
    return _uid("tkt"), _uid("lst")


# --- TTL dominance ----------------------------------------------------------


def test_expired_snapshot_refused_before_any_read(migrated_db, ids):
    ticket_id, listing_id = ids
    proxy = ListingReadProxy(unavailable=True)  # would fail any read
    snapshot_id = make_snapshot(
        ticket_ref=ticket_id, listing_ref=listing_id, expired=True
    )
    resp = reconcile(client_for(proxy), snapshot_id)
    assert resp.status_code == 409
    body = resp.json()
    # TTL dominance: expiry governs even though every upstream read
    # would have failed with a transport error.
    assert body["code"] == "SNAPSHOT_EXPIRED"
    assert body["killsSnapshot"] is True
    # Refused BEFORE reconciliation: no upstream read was attempted.
    assert proxy.reads == []
    assert snapshot_row(snapshot_id).divergence_code is models.DivergenceCode.SNAPSHOT_EXPIRED


# --- Clean pass ---------------------------------------------------------------


def test_clean_pass_no_divergence(migrated_db, ids):
    ticket_id, listing_id = ids
    proxy = ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id)},
        listings={listing_id: listing_state(listing_id, ticket_id)},
    )
    snapshot_id = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    resp = reconcile(client_for(proxy), snapshot_id)
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] == "CLEAN"
    assert body["code"] is None
    assert body["killsSnapshot"] is False
    assert snapshot_row(snapshot_id).divergence_code is None
    assert divergence_rows(snapshot_id) == []


# --- The moderated-listing fixture (first end-to-end divergence test) --------


def test_moderated_listing_flagged_is_seat_taken_moderation(migrated_db, ids):
    """THE fixture (build plan Post-Map item 2; filing item 4):
    moderation flags the listing; the ticket persists as `listed`;
    the seat's fulfillment path is gone -> SEAT_TAKEN / MODERATION,
    with the reason on the EventLog divergence record AND in the
    read-through result."""
    ticket_id, listing_id = ids
    proxy = ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id, status="listed")},
        listings={listing_id: listing_state(listing_id, ticket_id, status="flagged")},
    )
    snapshot_id = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    resp = reconcile(client_for(proxy), snapshot_id)
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "SEAT_TAKEN"
    assert body["reason"] == "MODERATION"
    assert body["killsSnapshot"] is True
    assert body["observed"]["listing"]["status"] == "flagged"

    rows = divergence_rows(snapshot_id)
    assert len(rows) == 1
    assert rows[0].payload["divergenceCode"] == "SEAT_TAKEN"
    assert rows[0].payload["reason"] == "MODERATION"
    assert rows[0].payload["listingRef"] == listing_id
    assert rows[0].payload["observed"]["ticket"]["status"] == "listed"

    # The annotation landed, and the mirror trigger wrote its
    # authoritative SNAPSHOT_DIVERGED row in the same transaction.
    assert snapshot_row(snapshot_id).divergence_code is models.DivergenceCode.SEAT_TAKEN
    assert len(divergence_rows(snapshot_id, "SNAPSHOT_DIVERGED")) == 1


def test_moderated_listing_cancelled_is_seat_taken_moderation(migrated_db, ids):
    ticket_id, listing_id = ids
    proxy = ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id, status="listed")},
        listings={
            listing_id: listing_state(listing_id, ticket_id, status="cancelled")
        },
    )
    snapshot_id = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    resp = reconcile(client_for(proxy), snapshot_id)
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "SEAT_TAKEN"
    assert body["reason"] == "MODERATION"


# --- Remaining firing-map branches -------------------------------------------


def test_listing_sold_is_listing_gone(migrated_db, ids):
    ticket_id, listing_id = ids
    proxy = ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id)},
        listings={listing_id: listing_state(listing_id, ticket_id, status="sold")},
    )
    snapshot_id = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    resp = reconcile(client_for(proxy), snapshot_id)
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "LISTING_GONE"
    assert body["reason"] is None


def test_ticket_transferred(migrated_db, ids):
    ticket_id, listing_id = ids
    proxy = ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id, status="transferred")},
        listings={listing_id: listing_state(listing_id, ticket_id)},
    )
    snapshot_id = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    resp = reconcile(client_for(proxy), snapshot_id)
    assert resp.status_code == 409
    assert resp.json()["code"] == "TICKET_TRANSFERRED"
    assert snapshot_row(snapshot_id).divergence_code is models.DivergenceCode.TICKET_TRANSFERRED


def test_ticket_redeemed_stub_branch(migrated_db, ids):
    """No services/api writer produces `redeemed` today; the branch
    must still fire if the state is ever observed (typed stub with
    its revisit trigger named in readthrough.py)."""
    ticket_id, listing_id = ids
    proxy = ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id, status="redeemed")},
        listings={listing_id: listing_state(listing_id, ticket_id)},
    )
    snapshot_id = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    resp = reconcile(client_for(proxy), snapshot_id)
    assert resp.status_code == 409
    assert resp.json()["code"] == "TICKET_REDEEMED"


def test_price_moved_stub_branch(migrated_db, ids):
    """No writer mutates a listing's price today; the comparison
    must still fire on an observed difference (typed stub)."""
    ticket_id, listing_id = ids
    proxy = ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id)},
        listings={
            listing_id: listing_state(listing_id, ticket_id, price_cents=12550)
        },
    )
    snapshot_id = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    resp = reconcile(client_for(proxy), snapshot_id)
    assert resp.status_code == 409
    assert resp.json()["code"] == "PRICE_MOVED"


def test_double_settlement_is_seat_taken_with_reason(migrated_db, ids):
    ticket_id, listing_id = ids
    mint_ref = _uid("mint")
    # A PRIOR snapshot with the same mintRef already settled
    # (chainTxRef recorded) under its own commitment.
    prior_snapshot_id = make_snapshot(
        ticket_ref=_uid("tkt"), listing_ref=_uid("lst"), mint_ref=mint_ref
    )
    session = db.session()
    try:
        prior = session.get(models.OfferSnapshot, prior_snapshot_id)
        candidate = session.get(models.TripCandidate, prior.trip_candidate_id)
        search = session.get(models.SearchSession, candidate.search_session_id)
        approval = models.ApprovalRequest(
            trip_profile_id=search.trip_profile_id,
            commitment_class=models.CommitmentClass.IRREVERSIBLE_ON_CHAIN,
            summary={},
            status="APPROVED",
        )
        session.add(approval)
        session.flush()
        session.add(
            models.Commitment(
                approval_request_id=approval.id,
                offer_snapshot_id=prior_snapshot_id,
                state="SETTLED",
                chain_tx_ref="sig-prior-settlement",
            )
        )
        session.commit()
    finally:
        session.close()

    proxy = ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id)},
        listings={listing_id: listing_state(listing_id, ticket_id)},
    )
    snapshot_id = make_snapshot(
        ticket_ref=ticket_id, listing_ref=listing_id, mint_ref=mint_ref
    )
    resp = reconcile(client_for(proxy), snapshot_id)
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "SEAT_TAKEN"
    assert body["reason"] == "DOUBLE_SETTLEMENT"
    rows = divergence_rows(snapshot_id)
    assert len(rows) == 1
    assert rows[0].payload["reason"] == "DOUBLE_SETTLEMENT"


# --- Absence and transport ----------------------------------------------------


def test_ticket_not_found_is_source_not_found(migrated_db, ids):
    ticket_id, listing_id = ids
    proxy = ListingReadProxy(
        tickets={},  # the referenced ticket does not exist upstream
        listings={listing_id: listing_state(listing_id, ticket_id)},
    )
    snapshot_id = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    resp = reconcile(client_for(proxy), snapshot_id)
    assert resp.status_code == 409
    assert resp.json()["code"] == "SOURCE_NOT_FOUND"


def test_listing_not_found_is_source_not_found(migrated_db, ids):
    ticket_id, listing_id = ids
    proxy = ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id)},
        listings={},  # the referenced listing does not exist upstream
    )
    snapshot_id = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    resp = reconcile(client_for(proxy), snapshot_id)
    assert resp.status_code == 409
    assert resp.json()["code"] == "SOURCE_NOT_FOUND"


def test_upstream_unavailable_blocks_without_killing(migrated_db, ids):
    ticket_id, listing_id = ids
    proxy = ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id)},
        listings={listing_id: listing_state(listing_id, ticket_id)},
        unavailable=True,
    )
    client = client_for(proxy)
    snapshot_id = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)

    resp = reconcile(client, snapshot_id)
    assert resp.status_code == 503
    body = resp.json()
    assert body["outcome"] == "BLOCKED"
    assert body["code"] == "UPSTREAM_UNAVAILABLE"
    assert body["killsSnapshot"] is False
    # Recorded, but the snapshot is NOT killed (no annotation).
    assert snapshot_row(snapshot_id).divergence_code is None
    rows = divergence_rows(snapshot_id)
    assert len(rows) == 1
    assert rows[0].payload["divergenceCode"] == "UPSTREAM_UNAVAILABLE"

    # Continuation is a fresh re-read once the source answers.
    proxy.unavailable = False
    resp2 = reconcile(client, snapshot_id)
    assert resp2.status_code == 200
    assert resp2.json()["outcome"] == "CLEAN"


# --- Idempotent surface over a dead snapshot -----------------------------------


def test_already_killed_snapshot_short_circuits(migrated_db, ids):
    ticket_id, listing_id = ids
    proxy = ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id, status="listed")},
        listings={listing_id: listing_state(listing_id, ticket_id, status="flagged")},
    )
    client = client_for(proxy)
    snapshot_id = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)

    first = reconcile(client, snapshot_id)
    assert first.status_code == 409
    reads_after_first = len(proxy.reads)

    second = reconcile(client, snapshot_id)
    assert second.status_code == 409
    body = second.json()
    assert body["code"] == "SEAT_TAKEN"
    assert body["reason"] == "MODERATION"
    # No new upstream reads, no duplicate records, no re-annotation.
    assert len(proxy.reads) == reads_after_first
    assert len(divergence_rows(snapshot_id)) == 1
    assert len(divergence_rows(snapshot_id, "SNAPSHOT_DIVERGED")) == 1


# --- Surface discipline ---------------------------------------------------------


def test_unknown_snapshot_is_404(migrated_db):
    client = client_for(ListingReadProxy())
    resp = reconcile(client, "no-such-snapshot")
    assert resp.status_code == 404


def test_non_ticket_kind_is_422(migrated_db):
    snapshot_id = make_snapshot(
        ticket_ref=_uid("tkt"), listing_ref=None, kind="stay"
    )
    client = client_for(ListingReadProxy())
    resp = reconcile(client, snapshot_id)
    assert resp.status_code == 422
