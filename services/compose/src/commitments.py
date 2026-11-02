"""Commitments router — commitment recording (Sprint 1, slice 4).

POST /commitments                 record a Commitment from an
                                  APPROVED approval, after one
                                  final commit-time reconciliation
GET  /commitments/{commitment_id} the recorded commitment

This is the settlement half of the commit path, and the formal
approval<->snapshot link the gate's filing named: a Commitment row
joins the ApprovalRequest, the OfferSnapshot it settles, the trip
(via the approval) and the commitment class (via approval +
snapshot, which agree by construction — the gate derives both
from the snapshot).

The rules (R4 §5, §6 — commit-time reconciliation ONLY):

- Only an APPROVED approval can produce a commitment. PENDING /
  REJECTED / EXPIRED approvals are refused (409, typed) and no
  commitment is written. An APPROVED approval settles nothing by
  itself (slice 3's filing); recording is the act that settles.
- Recording runs slice 2's reconciliation ONE FINAL TIME at
  record time. There is no continuous re-checking afterwards and
  none is needed: a commitment, once recorded, is the settlement
  of record. If the snapshot has diverged since approval, the
  recording is refused as the typed failure reconcile() raises —
  code, and for SEAT_TAKEN the reason + plain-language form —
  with slice 2's recording + annotation path applying unchanged.
  UPSTREAM_UNAVAILABLE blocks (503) without killing anything:
  the approval stays APPROVED and the recording is retryable.
- Idempotency (the schema's IdempotencyKey, Postgres-backed):
  the caller supplies a key. The success path writes the key row
  IN THE SAME TRANSACTION as the Commitment row and its EventLog
  record (marker IN_FLIGHT -> COMPLETED inside the transaction,
  the stored response being the commitment view), so a recorded
  commitment and its idempotency record land atomically or not
  at all. REPLAYING the same key for the same request returns the
  SAME commitment (200, the stored response) — no duplicate row,
  no second EventLog record. A DIFFERENT key for an
  already-committed approval is REFUSED (409 ALREADY_COMMITTED,
  carrying the existing commitment's id): a fresh key asserts a
  new operation, and silently returning the existing commitment
  would let a caller believe its new operation settled when it
  did nothing — the contract's no-silent-substitution discipline
  (R4 §5(e)) applied to this surface (author's choice, filed in
  SCHEMA-NOTES). A key replayed against a DIFFERENT request is
  refused (409 IDEMPOTENCY_KEY_REUSED). Refusals and blocks
  persist NO key row: a refused recording may be retried under
  the same key once its cause is addressed (a divergence refusal
  re-fires deterministically from recorded state; a block
  proceeds when the source answers).
- The Commitment row and its EventLog record
  (COMMITMENT_RECORDED, aggregate the commitment) are written in
  ONE transaction. Price and currency in the view and the record
  flow from the frozen snapshot — never from caller input (the
  USDC-only invariant is enforced at the Price type, slice 2's
  filing; it is not re-implemented here).
- State (author's choice, filed): the recorded commitment's
  state is SETTLED and settledAt is the record time. Recording
  IS the settlement of record in this layer (R4 §6.5): any chain
  action is the caller's, evidenced by the optional chainTxRef
  (the Solana transaction signature; null for off-chain
  settlement). The filed schema's state vocabulary has exactly
  one value in use — the codebase's own prior records write
  SETTLED — and no settling state machine was filed.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import approvals as gate
import models
import readthrough
import upstream
from db import get_session
from models import DivergenceCode

router = APIRouter(prefix="/commitments", tags=["commitments"])

EVENT_TYPE_COMMITMENT = "COMMITMENT_RECORDED"
IDEMPOTENCY_SCOPE = "commitment-record"

# This surface's own refusal codes (the R4 §5 divergence codes
# pass through from the evaluation unchanged; these name the
# recording preconditions, which are not divergences).
CODE_NOT_APPROVED = "APPROVAL_NOT_APPROVED"
CODE_ALREADY_COMMITTED = "ALREADY_COMMITTED"
CODE_KEY_REUSED = "IDEMPOTENCY_KEY_REUSED"
CODE_IN_FLIGHT = "REQUEST_IN_FLIGHT"

STATUS_COMPLETED = "COMPLETED"
STATUS_IN_FLIGHT = "IN_FLIGHT"


class CommitIn(BaseModel):
    approvalId: str
    idempotencyKey: str
    recordedBy: str
    chainTxRef: str | None = None


class CommitmentView(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    approvalRequestId: str
    offerSnapshotId: str
    tripProfileId: str
    commitmentClass: str
    state: str
    settledAt: datetime | None
    chainTxRef: str | None
    price: dict[str, Any]
    sourceRef: str


class CommitmentRefusal(BaseModel):
    """A recording refusal — the gate's discipline: a typed
    outcome, the code, and for SEAT_TAKEN the reason in machine
    and plain-language form."""

    model_config = ConfigDict(frozen=True)

    approvalId: str
    outcome: str  # REFUSED | BLOCKED
    code: str
    reason: str | None
    reasonText: str | None
    approvalStatus: str | None
    existingCommitmentId: str | None
    evaluatedAt: datetime


def get_reader() -> upstream.ReconciliationReader:
    """FastAPI dependency: the reconciliation reader for this
    process (same wiring as the other routers; tests override it
    with the interim listing-read proxy)."""
    return upstream.build_reader()


def _request_hash(body: CommitIn) -> str:
    """The idempotent request's identity: the approval it settles
    and the chain reference it records. recordedBy is metadata —
    a replay by a different operator returns the original record,
    it does not re-record it."""
    canonical = json.dumps(
        {"approvalId": body.approvalId, "chainTxRef": body.chainTxRef},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _view(session: Session, row: models.Commitment) -> CommitmentView:
    approval = row.approval_request
    snapshot = row.offer_snapshot
    return CommitmentView(
        id=row.id,
        approvalRequestId=row.approval_request_id,
        offerSnapshotId=row.offer_snapshot_id,
        tripProfileId=approval.trip_profile_id,
        commitmentClass=approval.commitment_class.value,
        state=row.state,
        settledAt=row.settled_at,
        chainTxRef=row.chain_tx_ref,
        price=snapshot.price,
        sourceRef=snapshot.source_ref,
    )


def _refusal(
    body: CommitIn,
    *,
    outcome: str,
    code: str,
    approval_status: str | None,
    now: datetime,
    reason: str | None = None,
    existing_commitment_id: str | None = None,
) -> CommitmentRefusal:
    return CommitmentRefusal(
        approvalId=body.approvalId,
        outcome=outcome,
        code=code,
        reason=reason,
        reasonText=gate.REASON_TEXT.get(reason),
        approvalStatus=approval_status,
        existingCommitmentId=existing_commitment_id,
        evaluatedAt=now,
    )


@router.post("")
def record_commitment(
    body: CommitIn,
    session: Session = Depends(get_session),
    reader: upstream.ReconciliationReader = Depends(get_reader),
):
    now = datetime.now(timezone.utc)
    approval = session.get(models.ApprovalRequest, body.approvalId)
    if approval is None:
        return JSONResponse(
            status_code=404, content={"detail": "ApprovalRequest not found"}
        )

    request_hash = _request_hash(body)
    key_row = session.get(models.IdempotencyKey, body.idempotencyKey)
    if key_row is not None:
        if key_row.request_hash != request_hash:
            # The key names a different operation than this one.
            refusal = _refusal(
                body,
                outcome="REFUSED",
                code=CODE_KEY_REUSED,
                approval_status=approval.status,
                now=now,
            )
            return JSONResponse(
                status_code=409, content=refusal.model_dump(mode="json")
            )
        if key_row.status == STATUS_COMPLETED and key_row.response_json is not None:
            # Replay: the SAME commitment, from the stored
            # response. No new row, no second EventLog record.
            return JSONResponse(status_code=200, content=key_row.response_json)
        # Same request, still in flight (a concurrent writer, or a
        # marker a crashed two-phase writer left): retryable.
        refusal = _refusal(
            body,
            outcome="BLOCKED",
            code=CODE_IN_FLIGHT,
            approval_status=approval.status,
            now=now,
        )
        return JSONResponse(
            status_code=409, content=refusal.model_dump(mode="json")
        )

    if approval.status != gate.APPROVED:
        refusal = _refusal(
            body,
            outcome="REFUSED",
            code=CODE_NOT_APPROVED,
            approval_status=approval.status,
            now=now,
        )
        return JSONResponse(
            status_code=409, content=refusal.model_dump(mode="json")
        )

    snapshot = gate._subject_snapshot(session, approval)
    if snapshot is None:
        return JSONResponse(
            status_code=422,
            content={
                "detail": (
                    "This approval has no subject OfferSnapshot; "
                    "there is nothing the commit path can reconcile "
                    "or record against"
                )
            },
        )
    kind = (snapshot.payload or {}).get("kind")
    if kind != models.OfferKind.TICKET.value:
        return JSONResponse(
            status_code=422,
            content={
                "detail": (
                    "Commitment recording is implemented for the "
                    f"ticket kind only (Sprint 1); this snapshot is {kind!r}"
                )
            },
        )

    existing = (
        session.query(models.Commitment)
        .filter_by(approval_request_id=approval.id)
        .first()
    )
    if existing is not None:
        refusal = _refusal(
            body,
            outcome="REFUSED",
            code=CODE_ALREADY_COMMITTED,
            approval_status=approval.status,
            now=now,
            existing_commitment_id=existing.id,
        )
        return JSONResponse(
            status_code=409, content=refusal.model_dump(mode="json")
        )

    # The final reconciliation (R4 §6): at record time, and only
    # at record time. Divergence = typed failure; the recording +
    # annotation path is slice 2's, unchanged.
    evaluation = readthrough.reconcile(session, snapshot, reader, now=now)
    if evaluation.code is DivergenceCode.UPSTREAM_UNAVAILABLE:
        refusal = _refusal(
            body,
            outcome="BLOCKED",
            code=evaluation.code.value,
            approval_status=approval.status,
            now=now,
        )
        return JSONResponse(
            status_code=503, content=refusal.model_dump(mode="json")
        )
    if evaluation.code is not None:
        refusal = _refusal(
            body,
            outcome="REFUSED",
            code=evaluation.code.value,
            approval_status=approval.status,
            now=now,
            reason=evaluation.reason,
        )
        return JSONResponse(
            status_code=409, content=refusal.model_dump(mode="json")
        )

    # Clean. ONE transaction: the idempotency record, the
    # Commitment row, and its EventLog record land together or
    # not at all.
    commitment = models.Commitment(
        approval_request_id=approval.id,
        offer_snapshot_id=snapshot.id,
        state="SETTLED",
        settled_at=now,
        chain_tx_ref=body.chainTxRef,
    )
    session.add(commitment)
    session.flush()
    view = _view(session, commitment)
    view_json = view.model_dump(mode="json")
    key = models.IdempotencyKey(
        key=body.idempotencyKey,
        scope=IDEMPOTENCY_SCOPE,
        request_hash=request_hash,
        status=STATUS_IN_FLIGHT,
    )
    session.add(key)
    session.flush()
    key.status = STATUS_COMPLETED
    key.response_json = view_json
    session.add(
        models.EventLog(
            aggregate_type="Commitment",
            aggregate_id=commitment.id,
            event_type=EVENT_TYPE_COMMITMENT,
            actor=body.recordedBy,
            payload={
                "commitmentId": commitment.id,
                "approvalRequestId": approval.id,
                "offerSnapshotId": snapshot.id,
                "tripProfileId": approval.trip_profile_id,
                "commitmentClass": approval.commitment_class.value,
                "state": commitment.state,
                "chainTxRef": body.chainTxRef,
                "sourceRef": snapshot.source_ref,
                "price": snapshot.price,
            },
        )
    )
    try:
        session.commit()
    except IntegrityError:
        # A concurrent writer with the same key committed first.
        # Resolve exactly as the pre-check would have.
        session.rollback()
        winner = session.get(models.IdempotencyKey, body.idempotencyKey)
        if (
            winner is not None
            and winner.request_hash == request_hash
            and winner.status == STATUS_COMPLETED
            and winner.response_json is not None
        ):
            return JSONResponse(status_code=200, content=winner.response_json)
        refusal = _refusal(
            body,
            outcome="BLOCKED",
            code=CODE_IN_FLIGHT,
            approval_status=approval.status,
            now=now,
        )
        return JSONResponse(
            status_code=409, content=refusal.model_dump(mode="json")
        )
    return JSONResponse(status_code=201, content=view_json)


@router.get("/{commitment_id}")
def get_commitment(
    commitment_id: str, session: Session = Depends(get_session)
):
    row = session.get(models.Commitment, commitment_id)
    if row is None:
        return JSONResponse(
            status_code=404, content={"detail": "Commitment not found"}
        )
    return JSONResponse(
        status_code=200, content=_view(session, row).model_dump(mode="json")
    )
