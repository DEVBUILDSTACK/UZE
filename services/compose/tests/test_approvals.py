"""Sprint 1 slice 3 — the human approval gate, end to end.

Substrate and upstream stand-in as in slice 2's suite: the REAL
migrated Postgres for approvals, snapshots, EventLog and
commitments; the interim LISTING-READ PROXY for the source of
record. The gate's contract (R4 §2.2, §3, §5):

  - reads and decisions are READ-THROUGH at request time — each
    runs slice 2's reconciliation for the approval's snapshot;
  - a diverged snapshot cannot be approved (409, code surfaced;
    SEAT_TAKEN carries its reason in the body);
  - an expired snapshot is refused as SNAPSHOT_EXPIRED under TTL
    dominance and resolves the approval to EXPIRED;
  - UPSTREAM_UNAVAILABLE blocks a decision (503) without killing
    the approval, which stays PENDING and decidable on recovery;
  - the read carries the snapshot's freshness, computed at
    request time, so staleness is visible before any decision.

Every test seeds the state that MUST produce its outcome and
asserts the HTTP result AND the persisted approval/snapshot rows —
if the gate skipped reconciliation, skipped the TTL check, or
recorded a decision it should have refused, these fail.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import approvals as approvals_module
import db
import models
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


def clean_proxy(ticket_id: str, listing_id: str) -> ListingReadProxy:
    return ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id)},
        listings={listing_id: listing_state(listing_id, ticket_id)},
    )


def moderated_proxy(ticket_id: str, listing_id: str) -> ListingReadProxy:
    return ListingReadProxy(
        tickets={ticket_id: ticket_state(ticket_id, status="listed")},
        listings={listing_id: listing_state(listing_id, ticket_id, status="flagged")},
    )


def make_snapshot(
    *,
    ticket_ref: str,
    listing_ref: str | None,
    mint_ref: str | None = None,
    expired: bool = False,
    kind: str = "ticket",
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
            price={"amount": 120.50, "currency": "USDC", "taxesIncluded": True},
            terms={"feeCents": 250},
            payload=payload,
            expires_at=NOW - timedelta(hours=1)
            if expired
            else NOW + timedelta(hours=1),
        )
        session.add(snapshot)
        session.commit()
        return snapshot.id, trip.id
    finally:
        session.close()


def client_for(proxy: ListingReadProxy) -> TestClient:
    app = create_app()
    app.dependency_overrides[approvals_module.get_reader] = lambda: proxy
    return TestClient(app, raise_server_exceptions=False)


def create_approval(client: TestClient, snapshot_id: str, summary=None):
    body = {"offerSnapshotId": snapshot_id}
    if summary is not None:
        body["summary"] = summary
    return client.post("/approvals", json=body)


def decide(client: TestClient, approval_id: str, decision: str, by: str = "ops-lead"):
    return client.post(
        f"/approvals/{approval_id}/decision",
        json={"decision": decision, "decidedBy": by},
    )


def approval_row(approval_id: str) -> models.ApprovalRequest:
    session = db.session()
    try:
        row = session.get(models.ApprovalRequest, approval_id)
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


# --- Creation -----------------------------------------------------------------


def test_create_approval_for_snapshot(migrated_db, ids):
    ticket_id, listing_id = ids
    snapshot_id, trip_id = make_snapshot(
        ticket_ref=ticket_id, listing_ref=listing_id
    )
    client = client_for(clean_proxy(ticket_id, listing_id))
    resp = create_approval(client, snapshot_id, summary={"humanNote": "anniversary trip"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "PENDING"
    assert body["offerSnapshotId"] == snapshot_id
    # Trip and commitment class are derived from the snapshot,
    # never from caller input.
    assert body["tripProfileId"] == trip_id
    assert body["commitmentClass"] == "IRREVERSIBLE_ON_CHAIN"
    # The server-written subject anchor is in the stored summary,
    # alongside the caller's own summary fields.
    assert body["summary"]["offerSnapshotId"] == snapshot_id
    assert body["summary"]["humanNote"] == "anniversary trip"
    assert body["signedBy"] is None
    assert body["resolvedAt"] is None
    # Creation carries the clock projection of freshness (no
    # reconciliation has run yet, and the view says so).
    freshness = body["freshness"]
    assert freshness["snapshotId"] == snapshot_id
    assert freshness["state"] == "FRESH"
    assert freshness["reconciled"] is False
    row = approval_row(body["id"])
    assert row.status == "PENDING"
    assert row.summary["offerSnapshotId"] == snapshot_id


def test_create_unknown_snapshot_is_404(migrated_db):
    client = client_for(ListingReadProxy())
    resp = create_approval(client, "no-such-snapshot")
    assert resp.status_code == 404


def test_create_non_ticket_snapshot_is_422(migrated_db):
    snapshot_id, _ = make_snapshot(
        ticket_ref=_uid("tkt"), listing_ref=None, kind="stay"
    )
    client = client_for(ListingReadProxy())
    resp = create_approval(client, snapshot_id)
    assert resp.status_code == 422


# --- Read-through reads + the staleness display --------------------------------


def test_read_clean_shows_fresh(migrated_db, ids):
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = create_approval(client, snapshot_id).json()["id"]

    resp = client.get(f"/approvals/{approval_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "PENDING"
    freshness = body["freshness"]
    # The read RAN reconciliation at request time...
    assert freshness["reconciled"] is True
    assert freshness["state"] == "FRESH"
    assert freshness["divergenceCode"] is None
    assert freshness["divergenceReason"] is None
    # ...and the staleness arithmetic is the snapshot's own window.
    assert 3500 < freshness["ttlSeconds"] <= 3600
    assert 0 <= freshness["ageSeconds"] < 120
    assert 0 < freshness["remainingSeconds"] <= freshness["ttlSeconds"]
    assert snapshot_row(snapshot_id).divergence_code is None


def test_read_moderated_listing_shows_stale_with_reason(migrated_db, ids):
    """The approver sees the kill BEFORE deciding: the read's own
    reconciliation annotates the snapshot and the freshness block
    carries code + reason. Without read-through this state would
    read FRESH and the annotation would not exist."""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(moderated_proxy(ticket_id, listing_id))
    approval_id = create_approval(client, snapshot_id).json()["id"]

    resp = client.get(f"/approvals/{approval_id}")
    assert resp.status_code == 200
    freshness = resp.json()["freshness"]
    assert freshness["state"] == "STALE"
    assert freshness["divergenceCode"] == "SEAT_TAKEN"
    assert freshness["divergenceReason"] == "MODERATION"
    assert snapshot_row(snapshot_id).divergence_code is models.DivergenceCode.SEAT_TAKEN


def test_read_upstream_unavailable_shows_unknown_without_killing(migrated_db, ids):
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    proxy = clean_proxy(ticket_id, listing_id)
    proxy.unavailable = True
    client = client_for(proxy)
    approval_id = create_approval(client, snapshot_id).json()["id"]

    resp = client.get(f"/approvals/{approval_id}")
    # A display read does not fail because the truth is unobservable;
    # it SAYS the truth is unobservable.
    assert resp.status_code == 200
    freshness = resp.json()["freshness"]
    assert freshness["state"] == "UNKNOWN"
    assert freshness["divergenceCode"] == "UPSTREAM_UNAVAILABLE"
    assert snapshot_row(snapshot_id).divergence_code is None


def test_read_unknown_approval_is_404(migrated_db):
    client = client_for(ListingReadProxy())
    assert client.get("/approvals/no-such-approval").status_code == 404


# --- Decisions: the gate's refusals ---------------------------------------------


def test_approve_moderated_listing_refused_with_code_and_reason(migrated_db, ids):
    """THE gate rule: a diverged snapshot cannot be approved. The
    refusal surfaces SEAT_TAKEN + MODERATION (and its plain-language
    form) in the body, and no decision is recorded."""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(moderated_proxy(ticket_id, listing_id))
    approval_id = create_approval(client, snapshot_id).json()["id"]

    resp = decide(client, approval_id, "APPROVE")
    assert resp.status_code == 409
    body = resp.json()
    assert body["outcome"] == "REFUSED"
    assert body["code"] == "SEAT_TAKEN"
    assert body["reason"] == "MODERATION"
    assert "moderation" in body["reasonText"].lower()
    assert body["approvalStatus"] == "PENDING"

    row = approval_row(approval_id)
    assert row.status == "PENDING"
    assert row.signed_by is None
    assert row.resolved_at is None


def test_approve_double_settled_refused_with_reason(migrated_db, ids):
    ticket_id, listing_id = ids
    mint_ref = _uid("mint")
    prior_snapshot_id, prior_trip_id = make_snapshot(
        ticket_ref=_uid("tkt"), listing_ref=_uid("lst"), mint_ref=mint_ref
    )
    session = db.session()
    try:
        approval = models.ApprovalRequest(
            trip_profile_id=prior_trip_id,
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

    snapshot_id, _ = make_snapshot(
        ticket_ref=ticket_id, listing_ref=listing_id, mint_ref=mint_ref
    )
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = create_approval(client, snapshot_id).json()["id"]

    resp = decide(client, approval_id, "APPROVE")
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "SEAT_TAKEN"
    assert body["reason"] == "DOUBLE_SETTLEMENT"
    assert "already been settled" in body["reasonText"]
    assert approval_row(approval_id).status == "PENDING"


def test_expired_snapshot_decision_refused_and_approval_expires(migrated_db, ids):
    """TTL dominance AT THE GATE: the proxy would fail every read,
    yet the refusal is SNAPSHOT_EXPIRED — and no upstream read is
    even attempted. The approval resolves to EXPIRED."""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(
        ticket_ref=ticket_id, listing_ref=listing_id, expired=True
    )
    proxy = ListingReadProxy(unavailable=True)
    client = client_for(proxy)
    created = create_approval(client, snapshot_id)
    assert created.status_code == 201
    assert created.json()["freshness"]["state"] == "EXPIRED"
    approval_id = created.json()["id"]

    resp = decide(client, approval_id, "APPROVE")
    assert resp.status_code == 409
    body = resp.json()
    assert body["outcome"] == "REFUSED"
    assert body["code"] == "SNAPSHOT_EXPIRED"
    assert body["approvalStatus"] == "EXPIRED"
    assert proxy.reads == []

    row = approval_row(approval_id)
    assert row.status == "EXPIRED"
    assert row.signed_by is None
    assert row.resolved_at is not None


def test_upstream_unavailable_blocks_decision_then_recovers(migrated_db, ids):
    """Block without kill, at the approval level: the decision is
    refused 503, the approval stays PENDING and unsigned, and the
    SAME approval is decidable once the source answers."""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    proxy = clean_proxy(ticket_id, listing_id)
    proxy.unavailable = True
    client = client_for(proxy)
    approval_id = create_approval(client, snapshot_id).json()["id"]

    resp = decide(client, approval_id, "APPROVE")
    assert resp.status_code == 503
    body = resp.json()
    assert body["outcome"] == "BLOCKED"
    assert body["code"] == "UPSTREAM_UNAVAILABLE"
    assert body["approvalStatus"] == "PENDING"
    row = approval_row(approval_id)
    assert row.status == "PENDING"
    assert row.signed_by is None
    assert snapshot_row(snapshot_id).divergence_code is None

    proxy.unavailable = False
    resp2 = decide(client, approval_id, "APPROVE")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "APPROVED"


# --- Decisions: the gate's acceptances -------------------------------------------


def test_approve_clean_succeeds(migrated_db, ids):
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = create_approval(client, snapshot_id).json()["id"]

    resp = decide(client, approval_id, "APPROVE", by="ops-lead")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "APPROVED"
    assert body["signedBy"] == "ops-lead"
    assert body["resolvedAt"] is not None
    assert body["freshness"]["state"] == "FRESH"
    assert body["freshness"]["reconciled"] is True

    row = approval_row(approval_id)
    assert row.status == "APPROVED"
    assert row.signed_by == "ops-lead"
    assert row.resolved_at is not None


def test_reject_clean_succeeds(migrated_db, ids):
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = create_approval(client, snapshot_id).json()["id"]

    resp = decide(client, approval_id, "REJECT", by="ops-lead")
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED"
    assert approval_row(approval_id).status == "REJECTED"


def test_reject_diverged_snapshot_closes_request(migrated_db, ids):
    """Author's choice, pinned: REJECT asserts nothing about the
    snapshot, so a human can close a dead request instead of
    leaving it PENDING forever. (APPROVE against the same state
    is refused — see the moderated-listing test above.)"""
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(moderated_proxy(ticket_id, listing_id))
    approval_id = create_approval(client, snapshot_id).json()["id"]

    resp = decide(client, approval_id, "REJECT", by="ops-lead")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "REJECTED"
    assert body["freshness"]["state"] == "STALE"
    assert approval_row(approval_id).status == "REJECTED"


def test_second_decision_conflicts(migrated_db, ids):
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = create_approval(client, snapshot_id).json()["id"]

    assert decide(client, approval_id, "APPROVE").status_code == 200
    resp = decide(client, approval_id, "REJECT")
    assert resp.status_code == 409
    assert "APPROVED" in resp.json()["detail"]
    assert approval_row(approval_id).status == "APPROVED"


# --- Surface discipline ------------------------------------------------------------


def test_decision_unknown_approval_is_404(migrated_db):
    client = client_for(ListingReadProxy())
    resp = decide(client, "no-such-approval", "APPROVE")
    assert resp.status_code == 404


def test_decision_value_is_validated(migrated_db, ids):
    ticket_id, listing_id = ids
    snapshot_id, _ = make_snapshot(ticket_ref=ticket_id, listing_ref=listing_id)
    client = client_for(clean_proxy(ticket_id, listing_id))
    approval_id = create_approval(client, snapshot_id).json()["id"]
    resp = decide(client, approval_id, "SHRUG")
    assert resp.status_code == 422
    assert approval_row(approval_id).status == "PENDING"


def test_anchorless_approval_reads_without_freshness_and_cannot_be_decided(
    migrated_db,
):
    """ApprovalRequests created outside this gate (no subject
    anchor in summary) remain readable, carry no freshness, and
    cannot be decided here — the gate never decides blind."""
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
            status="PENDING",
        )
        session.add(row)
        session.commit()
        approval_id = row.id
    finally:
        session.close()

    client = client_for(ListingReadProxy())
    resp = client.get(f"/approvals/{approval_id}")
    assert resp.status_code == 200
    assert resp.json()["freshness"] is None
    assert resp.json()["offerSnapshotId"] is None

    resp = decide(client, approval_id, "APPROVE")
    assert resp.status_code == 422
    assert approval_row(approval_id).status == "PENDING"
