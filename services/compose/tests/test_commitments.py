"""Sprint 1 slice 4 — commitment recording, end to end.

Substrate and upstream stand-in as in slices 2–3: the REAL
migrated Postgres for approvals, snapshots, commitments,
EventLog and idempotency keys; the interim LISTING-READ PROXY
for the source of record. The recording rules (R4 §5, §6):

  - only an APPROVED approval records; PENDING / REJECTED /
    EXPIRED are refused and write nothing;
  - recording re-runs reconciliation ONE FINAL TIME — a snapshot
    that diverged (or expired) after approval refuses the record
    as the typed failure, and no commitment is written;
  - UPSTREAM_UNAVAILABLE blocks the record without killing
    anything, and the same idempotency key records on recovery;
  - replaying a key returns the SAME commitment — one row, one
    EventLog record — while a different key for an
    already-committed approval is refused, not silently served.

Every test seeds the state that MUST produce its outcome and
asserts the HTTP result AND the persisted rows — if recording
skipped the status check, skipped the final reconciliation,
duplicated on replay, or wrote its EventLog record in a
different outcome than its commitment row, these fail.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import approvals as approvals_module
import commitments as commitments_module
import db
import models
from app import create_app
from upstream import ListingReadProxy, ListingState, TicketState


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


def clean_proxy(ticket_id: str, listing_id: str) -> ListingReadProxy:
    return ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id)},
        listings={listing_id: listing_state(listing_id, ticket_id)},
    )


def make_snapshot(
    *,
    ticket_ref: str,
    listing_ref: str | None,
    mint_ref: str | None = None,
    expires_in: timedelta = timedelta(hours=1),
) -> tuple[str, str]:
    """Persist a snapshot chain and return (snapshot_id, trip_id)."""
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
        snapshot = models.OfferSnapshot(
            trip_candidate_id=candidate.id,
            rail=models.Rail.SOLANA_NFT,
            source_ref=listing_ref or ticket_ref,
            commitment_class=models.CommitmentClass.IRREVERSIBLE_ON_CHAIN,
            price={"amount": 120.50, "currency": "USDC", "taxesIncluded": True},
            terms={"feeCents": 250},
            payload=payload,
            expires_at=datetime.now(timezone.utc) + expires_in,
        )
        session.add(snapshot)
        session.commit()
        return snapshot.id, trip.id
    finally:
        session.close()


def client_for(proxy: ListingReadProxy) -> TestClient:
    app = create_app()
    app.dependency_overrides[approvals_module.get_reader] = lambda: proxy
    app.dependency_overrides[commitments_module.get_reader] = lambda: proxy
    return TestClient(app, raise_server_exceptions=False)


def create_approval(client: TestClient, snapshot_id: str) -> str:
    resp = client.post("/approvals", json={"offerSnapshotId": snapshot_id})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def approve(client: TestClient, approval_id: str) -> None:
    resp = client.post(
        f"/approvals/{approval_id}/decision",
        json={"decision": "APPROVE", "decidedBy": "ops-lead"},
    )
    assert resp.status_code == 200, resp.text


def record(
    client: TestClient,
    approval_id: str,
    key: str,
    chain_tx_ref: str | None = None,
    by: str = "settlement-runner",
):
    body = {"approvalId": approval_id, "idempotencyKey": key, "recordedBy": by}
    if chain_tx_ref is not None:
        body["chainTxRef"] = chain_tx_ref
    return client.post("/commitments", json=body)


def approved_approval(client: TestClient, snapshot_id: str) -> str:
    approval_id = create_approval(client, snapshot_id)
    approve(client, approval_id)
    return approval_id


def commitment_rows(approval_id: str) -> list[models.Commitment]:
    session = db.session()
    try:
        rows = (
            session.query(models.Commitment)
            .filter_by(approval_request_id=approval_id)
            .all()
        )
        session.expunge_all()
        return rows
    finally:
        session.close()


def commitment_events() -> list[models.EventLog]:
    session = db.session()
    try:
        rows = (
            session.query(models.EventLog)
            .filter_by(event_type="COMMITMENT_RECORDED")
            .all()
        )
        session.expunge_all()
        return rows
    finally:
        session.close()


def commitment_events_for(approval_id: str) -> list[models.EventLog]:
    """COMMITMENT_RECORDED records attributable to one approval
    (the substrate is session-shared, so 'wrote nothing' must be
    asserted per approval, never globally)."""
    return [
        e
        for e in commitment_events()
        if e.payload.get("approvalRequestId") == approval_id
    ]


def key_row(key: str) -> models.IdempotencyKey | None:
    session = db.session()
    try:
        row = session.get(models.IdempotencyKey, key)
        if row is not None:
            session.expunge(row)
        return row
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


# --- The happy path: record, linkage, records ------------------------------------


def test_record_from_approved_approval(migrated_db, ids):
    ticket_id, listing_id = ids
    snapshot_id, trip_id = make_snapshot(
        ticket_ref=ticket_id, listing_ref=listing_id
    )
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = approved_approval(client, snapshot_id)

    resp = record(client, approval_id, _uid("key"), chain_tx_ref="sig-abc-123")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    # The formal link: approval + snapshot + trip + class.
    assert body["approvalRequestId"] == approval_id
    assert body["offerSnapshotId"] == snapshot_id
    assert body["tripProfileId"] == trip_id
    assert body["commitmentClass"] == "IRREVERSIBLE_ON_CHAIN"
    assert body["state"] == "SETTLED"
    assert body["settledAt"] is not None
    assert body["chainTxRef"] == "sig-abc-123"
    # Price/currency flow from the FROZEN SNAPSHOT, never the caller.
    assert body["price"] == {
        "amount": 120.50,
        "currency": "USDC",
        "taxesIncluded": True,
    }
    assert body["sourceRef"] == listing_id

    rows = commitment_rows(approval_id)
    assert len(rows) == 1
    assert rows[0].id == body["id"]
    assert rows[0].offer_snapshot_id == snapshot_id
    assert rows[0].state == "SETTLED"
    assert rows[0].chain_tx_ref == "sig-abc-123"
    assert rows[0].settled_at is not None

    # Exactly one EventLog record, for THIS commitment, carrying
    # the settlement facts (incl. the snapshot's frozen price).
    events = [e for e in commitment_events() if e.aggregate_id == body["id"]]
    assert len(events) == 1
    assert events[0].aggregate_type == "Commitment"
    assert events[0].actor == "settlement-runner"
    assert events[0].payload["approvalRequestId"] == approval_id
    assert events[0].payload["offerSnapshotId"] == snapshot_id
    assert events[0].payload["chainTxRef"] == "sig-abc-123"
    assert events[0].payload["price"]["currency"] == "USDC"


def test_record_key_row_completed(migrated_db, ids):
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = approved_approval(client, snapshot_id)
    key = _uid("key")

    resp = record(client, approval_id, key)
    assert resp.status_code == 201, resp.text
    row = key_row(key)
    assert row is not None
    assert row.scope == "commitment-record"
    assert row.status == "COMPLETED"
    assert row.response_json["id"] == resp.json()["id"]


def test_record_without_chain_ref_is_null(migrated_db, ids):
    """Off-chain settlement (R4 §6.5): chainTxRef is null, the
    record still lands."""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = approved_approval(client, snapshot_id)

    resp = record(client, approval_id, _uid("key"))
    assert resp.status_code == 201, resp.text
    assert resp.json()["chainTxRef"] is None
    assert commitment_rows(approval_id)[0].chain_tx_ref is None


def test_get_commitment_view_and_404(migrated_db, ids):
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = approved_approval(client, snapshot_id)
    created = record(client, approval_id, _uid("key")).json()

    resp = client.get(f"/commitments/{created['id']}")
    assert resp.status_code == 200
    fetched = resp.json()
    # Same commitment, field for field. settledAt is compared as
    # an instant: the create response renders the in-memory UTC
    # value ('Z'), the read renders the value Postgres returns
    # (local offset) — one instant, two renderings.
    assert datetime.fromisoformat(
        fetched.pop("settledAt").replace("Z", "+00:00")
    ) == datetime.fromisoformat(created.pop("settledAt").replace("Z", "+00:00"))
    assert fetched == created
    assert client.get("/commitments/no-such-commitment").status_code == 404


# --- Only APPROVED records ---------------------------------------------------------


def test_record_pending_refused_writes_nothing_and_key_not_burned(
    migrated_db, ids
):
    """PENDING refuses; nothing is written — including no
    idempotency row, so the SAME key records once the approval
    lands. If refusals persisted the key, the retry would 409."""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = create_approval(client, snapshot_id)
    key = _uid("key")

    resp = record(client, approval_id, key)
    assert resp.status_code == 409
    body = resp.json()
    assert body["outcome"] == "REFUSED"
    assert body["code"] == "APPROVAL_NOT_APPROVED"
    assert body["approvalStatus"] == "PENDING"
    assert commitment_rows(approval_id) == []
    assert commitment_events_for(approval_id) == []
    assert key_row(key) is None

    approve(client, approval_id)
    resp2 = record(client, approval_id, key)
    assert resp2.status_code == 201, resp2.text
    assert len(commitment_rows(approval_id)) == 1


def test_record_rejected_refused(migrated_db, ids):
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = create_approval(client, snapshot_id)
    resp = client.post(
        f"/approvals/{approval_id}/decision",
        json={"decision": "REJECT", "decidedBy": "ops-lead"},
    )
    assert resp.status_code == 200

    resp = record(client, approval_id, _uid("key"))
    assert resp.status_code == 409
    assert resp.json()["code"] == "APPROVAL_NOT_APPROVED"
    assert resp.json()["approvalStatus"] == "REJECTED"
    assert commitment_rows(approval_id) == []
    assert commitment_events_for(approval_id) == []


def test_record_expired_approval_refused(migrated_db, ids):
    """An approval the gate resolved to EXPIRED (its snapshot
    died) can never record."""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(
        ticket_ref=ticket_id,
        listing_ref=listing_id,
        expires_in=timedelta(hours=-1),
    )
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = create_approval(client, snapshot_id)
    resp = client.post(
        f"/approvals/{approval_id}/decision",
        json={"decision": "APPROVE", "decidedBy": "ops-lead"},
    )
    assert resp.status_code == 409  # gate: TTL dominance resolves EXPIRED

    resp = record(client, approval_id, _uid("key"))
    assert resp.status_code == 409
    assert resp.json()["code"] == "APPROVAL_NOT_APPROVED"
    assert resp.json()["approvalStatus"] == "EXPIRED"
    assert commitment_rows(approval_id) == []


# --- The final reconciliation at record time ---------------------------------------


def test_record_diverged_since_approval_refused_with_reason(migrated_db, ids):
    """THE commit-time rule: the listing was clean when the human
    approved; moderation flags it afterwards. Approval does not
    freeze the world — recording re-runs reconciliation and
    refuses with the code AND the reason. No commitment exists."""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    proxy = clean_proxy(ticket_id, listing_id)
    client = client_for(proxy)
    approval_id = approved_approval(client, snapshot_id)

    proxy.listings[listing_id] = listing_state(
        listing_id, ticket_id, status="flagged"
    )
    resp = record(client, approval_id, _uid("key"))
    assert resp.status_code == 409
    body = resp.json()
    assert body["outcome"] == "REFUSED"
    assert body["code"] == "SEAT_TAKEN"
    assert body["reason"] == "MODERATION"
    assert "moderation" in body["reasonText"].lower()
    assert commitment_rows(approval_id) == []
    assert commitment_events_for(approval_id) == []
    # Slice 2's annotation path applied: the snapshot is dead.
    assert (
        snapshot_row(snapshot_id).divergence_code
        is models.DivergenceCode.SEAT_TAKEN
    )


def test_record_after_snapshot_expires_refused(migrated_db, ids):
    """TTL is enforced at COMMIT, not only at the gate: approved
    inside the window, recorded after it — SNAPSHOT_EXPIRED."""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(
        ticket_ref=ticket_id,
        listing_ref=listing_id,
        expires_in=timedelta(seconds=3),
    )
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = approved_approval(client, snapshot_id)

    time.sleep(3.3)
    resp = record(client, approval_id, _uid("key"))
    assert resp.status_code == 409
    assert resp.json()["code"] == "SNAPSHOT_EXPIRED"
    assert commitment_rows(approval_id) == []
    assert (
        snapshot_row(snapshot_id).divergence_code
        is models.DivergenceCode.SNAPSHOT_EXPIRED
    )


def test_record_blocked_by_upstream_then_recovers_same_key(migrated_db, ids):
    """Block without kill at commit: 503, nothing written, no key
    burned, the snapshot NOT annotated — and the same key records
    once the source answers."""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    proxy = clean_proxy(ticket_id, listing_id)
    client = client_for(proxy)
    approval_id = approved_approval(client, snapshot_id)
    key = _uid("key")

    proxy.unavailable = True
    resp = record(client, approval_id, key)
    assert resp.status_code == 503
    body = resp.json()
    assert body["outcome"] == "BLOCKED"
    assert body["code"] == "UPSTREAM_UNAVAILABLE"
    assert commitment_rows(approval_id) == []
    assert key_row(key) is None
    assert snapshot_row(snapshot_id).divergence_code is None

    proxy.unavailable = False
    resp2 = record(client, approval_id, key)
    assert resp2.status_code == 201, resp2.text
    assert len(commitment_rows(approval_id)) == 1


def test_double_settlement_at_record_time_refused(migrated_db, ids):
    """Both approvals were clean at the gate (no settlement
    existed). The first recording settles the mint; the second
    recording — not the gate — is where DOUBLE_SETTLEMENT fires.
    This is why reconciliation runs at commit, not only at
    approval."""
    ticket_id, listing_id = ids
    mint_ref = _uid("mint")
    proxy = clean_proxy(ticket_id, listing_id)
    client = client_for(proxy)

    snap_a, _ = make_snapshot(
        ticket_ref=ticket_id, listing_ref=listing_id, mint_ref=mint_ref
    )
    approval_a = approved_approval(client, snap_a)

    ticket_b, listing_b = _uid("tkt"), _uid("lst")
    proxy.tickets[ticket_b] = ticket_state(ticket_b)
    proxy.listings[listing_b] = listing_state(listing_b, ticket_b)
    snap_b, _ = make_snapshot(
        ticket_ref=ticket_b, listing_ref=listing_b, mint_ref=mint_ref
    )
    approval_b = approved_approval(client, snap_b)

    resp_a = record(client, approval_a, _uid("key"), chain_tx_ref="sig-first")
    assert resp_a.status_code == 201, resp_a.text

    resp_b = record(client, approval_b, _uid("key"))
    assert resp_b.status_code == 409
    body = resp_b.json()
    assert body["code"] == "SEAT_TAKEN"
    assert body["reason"] == "DOUBLE_SETTLEMENT"
    assert "already been settled" in body["reasonText"]
    assert commitment_rows(approval_b) == []
    assert (
        snapshot_row(snap_b).divergence_code
        is models.DivergenceCode.SEAT_TAKEN
    )


# --- Idempotency ---------------------------------------------------------------------


def test_replay_same_key_returns_same_commitment(migrated_db, ids):
    """Replay: SAME commitment id, no duplicate row, exactly one
    EventLog record, one key row. If replay re-executed, the
    counts would double and this fails."""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = approved_approval(client, snapshot_id)
    key = _uid("key")

    first = record(client, approval_id, key, chain_tx_ref="sig-replay")
    assert first.status_code == 201, first.text
    replay = record(client, approval_id, key, chain_tx_ref="sig-replay")
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert replay.json()["id"] == first.json()["id"]

    assert len(commitment_rows(approval_id)) == 1
    events = [
        e for e in commitment_events() if e.aggregate_id == first.json()["id"]
    ]
    assert len(events) == 1
    assert key_row(key).status == "COMPLETED"


def test_different_key_for_committed_approval_refused(migrated_db, ids):
    """Author's choice, pinned: a FRESH key asserts a new
    operation, so it is refused ALREADY_COMMITTED (carrying the
    existing id) rather than silently served the old commitment.
    Nothing new is written and the fresh key is not persisted."""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = approved_approval(client, snapshot_id)

    first = record(client, approval_id, _uid("key"))
    assert first.status_code == 201, first.text
    fresh_key = _uid("key")
    resp = record(client, approval_id, fresh_key)
    assert resp.status_code == 409
    body = resp.json()
    assert body["outcome"] == "REFUSED"
    assert body["code"] == "ALREADY_COMMITTED"
    assert body["existingCommitmentId"] == first.json()["id"]
    assert len(commitment_rows(approval_id)) == 1
    assert len(commitment_events_for(approval_id)) == 1
    assert key_row(fresh_key) is None


def test_key_reused_for_different_approval_refused(migrated_db, ids):
    """A key is bound to its request: the same key aimed at a
    different approval is a reuse, refused — and the second
    approval remains uncommitted."""
    ticket_id, listing_id = ids
    proxy = clean_proxy(ticket_id, listing_id)
    client = client_for(proxy)

    snap_a, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    approval_a = approved_approval(client, snap_a)

    ticket_b, listing_b = _uid("tkt"), _uid("lst")
    proxy.tickets[ticket_b] = ticket_state(ticket_b)
    proxy.listings[listing_b] = listing_state(listing_b, ticket_b)
    snap_b, _ = make_snapshot(ticket_ref=ticket_b, listing_ref=listing_b)
    approval_b = approved_approval(client, snap_b)

    key = _uid("key")
    assert record(client, approval_a, key).status_code == 201
    resp = record(client, approval_b, key)
    assert resp.status_code == 409
    assert resp.json()["code"] == "IDEMPOTENCY_KEY_REUSED"
    assert commitment_rows(approval_b) == []


# --- Surface discipline ----------------------------------------------------------------


def test_record_unknown_approval_404(migrated_db):
    client = client_for(ListingReadProxy())
    resp = record(client, "no-such-approval", _uid("key"))
    assert resp.status_code == 404


def test_record_anchorless_approved_approval_422(migrated_db):
    """An APPROVED approval created outside the gate has no
    subject snapshot to reconcile against; recording refuses
    rather than committing blind."""
    session = db.session()
    try:
        trip = models.TripProfile(
            buyer_id="buyer-1",
            modules=[models.ModuleType.TICKETS],
            authorization={},
        )
        session.add(trip)
        session.flush()
        row = models.ApprovalRequest(
            trip_profile_id=trip.id,
            commitment_class=models.CommitmentClass.IRREVERSIBLE_ON_CHAIN,
            summary={},
            status="APPROVED",
        )
        session.add(row)
        session.commit()
        approval_id = row.id
    finally:
        session.close()

    client = client_for(ListingReadProxy())
    resp = record(client, approval_id, _uid("key"))
    assert resp.status_code == 422
    assert commitment_rows(approval_id) == []
