"""Approvals router — the human approval gate (Sprint 1, slice 3).

POST /approvals                     create a PENDING approval request
                                    for one ticket-kind OfferSnapshot
GET  /approvals/{approval_id}       the approval, read READ-THROUGH:
                                    its snapshot is reconciled at
                                    request time (R4 §2.2) and the
                                    response carries the snapshot's
                                    freshness state for the approver
POST /approvals/{approval_id}/decision
                                    record APPROVE | REJECT, gated by
                                    a fresh reconciliation (below)

The gate's rules (R4 §2.2, §3, §5; the contract is the authority):

- Approval reads are ALWAYS read-through at request time. No gate
  read or decision acts on a cached or previously fetched copy of
  catalog state: the read and the decision both run slice 2's
  reconciliation for the approval's snapshot first.
- A diverged snapshot CANNOT be approved. An APPROVE decision
  against one is refused (409) with the divergence code surfaced —
  and, for SEAT_TAKEN, the reason (MODERATION | DOUBLE_SETTLEMENT)
  plus its plain-language rendering, per R4 §5's reason precision.
- An expired snapshot is refused as SNAPSHOT_EXPIRED (TTL
  dominance): the decision is refused (409) and the approval
  resolves to EXPIRED — expiry is a property of the snapshot, and
  no decision in either direction is recorded against a dead one.
- UPSTREAM_UNAVAILABLE blocks the decision (503) WITHOUT killing
  the approval: it stays PENDING and the decision is retryable once
  the source answers, mirroring slice 2's block-without-kill.
- A REJECT decision asserts nothing about the snapshot, so against
  a diverged-but-unexpired snapshot it is still recordable — the
  human closes the dead request rather than leaving it PENDING
  forever. (Author's choice in this slice; the contract binds
  approval, not rejection.)

The approval's subject: ApprovalRequest (Sprint 0 schema) keys to
a TripProfile + CommitmentClass and has no snapshot column; the
Commitment table that will formally link approval <-> snapshot
belongs to the NEXT slice (commitment recording). This slice
therefore records the subject snapshot id in the request's
`summary` JSON under `offerSnapshotId` — written by the server at
creation (a caller-supplied value under that key is overwritten),
and read back as the anchor for every reconciliation. The trip and
the commitment class are derived from the snapshot itself
(snapshot -> candidate -> session -> trip; snapshot.commitmentClass),
never from caller input: the approver approves a concrete quote.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

import models
import readthrough
import upstream
from db import get_session
from models import DivergenceCode

router = APIRouter(prefix="/approvals", tags=["approvals"])

# ApprovalRequest.status vocabulary (Sprint 0, Author's Choice 4 —
# a string column, named here once rather than scattered).
PENDING = "PENDING"
APPROVED = "APPROVED"
REJECTED = "REJECTED"
EXPIRED = "EXPIRED"

# R4 §5: the gate surfaces the SEAT_TAKEN reason in plain language.
REASON_TEXT = {
    readthrough.REASON_MODERATION: (
        "This listing was removed by moderation, so the seat can "
        "no longer be fulfilled as quoted."
    ),
    readthrough.REASON_DOUBLE_SETTLEMENT: (
        "This seat has already been settled under another commitment."
    ),
}


class ApprovalCreate(BaseModel):
    offerSnapshotId: str
    summary: dict[str, Any] = {}


class DecisionIn(BaseModel):
    decision: str  # APPROVE | REJECT
    decidedBy: str


class FreshnessView(BaseModel):
    """The snapshot's freshness, computed at request time — the
    staleness display. `reconciled` says whether a live §6
    reconciliation ran for this view (reads and decisions) or the
    state is the clock/annotation projection only (creation)."""

    model_config = ConfigDict(frozen=True)

    snapshotId: str
    snapshotCreatedAt: datetime
    snapshotExpiresAt: datetime
    ageSeconds: int
    ttlSeconds: int
    remainingSeconds: int
    state: str  # FRESH | STALE | EXPIRED | UNKNOWN
    reconciled: bool
    divergenceCode: str | None
    divergenceReason: str | None
    evaluatedAt: datetime


class ApprovalView(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    offerSnapshotId: str | None
    tripProfileId: str
    commitmentClass: str
    summary: dict[str, Any]
    status: str
    signedBy: str | None
    resolvedAt: datetime | None
    freshness: FreshnessView | None


class DecisionRefusal(BaseModel):
    """A gate refusal — the same discipline as slice 2's reconcile
    surface: a typed outcome, the code, and for SEAT_TAKEN the
    reason in both machine and plain-language form."""

    model_config = ConfigDict(frozen=True)

    approvalId: str
    outcome: str  # REFUSED | BLOCKED
    code: str
    reason: str | None
    reasonText: str | None
    approvalStatus: str
    evaluatedAt: datetime


def get_reader() -> upstream.ReconciliationReader:
    """FastAPI dependency: the reconciliation reader for this
    process (see snapshots.get_reader — same wiring, router-local
    by the codebase's convention; tests override it with the
    interim listing-read proxy)."""
    return upstream.build_reader()


def _freshness(
    snapshot: models.OfferSnapshot,
    evaluation: readthrough.Evaluation | None,
    *,
    reconciled: bool,
    now: datetime,
) -> FreshnessView:
    """Freshness state, in the contract's terms: FRESH inside the
    window with live state in agreement; STALE when the frozen
    state is known to disagree (a divergence is recorded); EXPIRED
    at/after expiresAt (TTL dominance — the clock governs first);
    UNKNOWN when the source could not be observed at all (the
    snapshot's truth is unknown, not falsified)."""
    if now >= snapshot.expires_at:
        state = "EXPIRED"
    elif evaluation is not None and evaluation.code is DivergenceCode.UPSTREAM_UNAVAILABLE:
        state = "UNKNOWN"
    elif (evaluation is not None and evaluation.code is not None) or (
        snapshot.divergence_code is not None
    ):
        state = "STALE"
    else:
        state = "FRESH"

    if evaluation is not None:
        code = evaluation.code.value if evaluation.code else None
        reason = evaluation.reason
    else:
        code = snapshot.divergence_code.value if snapshot.divergence_code else None
        reason = None

    return FreshnessView(
        snapshotId=snapshot.id,
        snapshotCreatedAt=snapshot.created_at,
        snapshotExpiresAt=snapshot.expires_at,
        ageSeconds=int((now - snapshot.created_at).total_seconds()),
        ttlSeconds=int((snapshot.expires_at - snapshot.created_at).total_seconds()),
        remainingSeconds=int((snapshot.expires_at - now).total_seconds()),
        state=state,
        reconciled=reconciled,
        divergenceCode=code,
        divergenceReason=reason,
        evaluatedAt=now,
    )


def _view(
    row: models.ApprovalRequest,
    freshness: FreshnessView | None,
) -> ApprovalView:
    return ApprovalView(
        id=row.id,
        offerSnapshotId=(row.summary or {}).get("offerSnapshotId"),
        tripProfileId=row.trip_profile_id,
        commitmentClass=row.commitment_class.value,
        summary=row.summary,
        status=row.status,
        signedBy=row.signed_by,
        resolvedAt=row.resolved_at,
        freshness=freshness,
    )


def _subject_snapshot(
    session: Session, row: models.ApprovalRequest
) -> models.OfferSnapshot | None:
    """The approval's subject snapshot, via the server-written
    summary anchor. Anchorless rows (created outside this gate)
    have no subject the gate can reconcile."""
    anchor = (row.summary or {}).get("offerSnapshotId")
    if not isinstance(anchor, str):
        return None
    return session.get(models.OfferSnapshot, anchor)


def _get_approval(session: Session, approval_id: str) -> models.ApprovalRequest | None:
    return session.get(models.ApprovalRequest, approval_id)


@router.post("", status_code=201)
def create_approval(
    body: ApprovalCreate, session: Session = Depends(get_session)
):
    snapshot = session.get(models.OfferSnapshot, body.offerSnapshotId)
    if snapshot is None:
        return JSONResponse(
            status_code=404, content={"detail": "OfferSnapshot not found"}
        )
    kind = (snapshot.payload or {}).get("kind")
    if kind != models.OfferKind.TICKET.value:
        return JSONResponse(
            status_code=422,
            content={
                "detail": (
                    "The approval gate is implemented for the ticket "
                    f"kind only (Sprint 1); this snapshot is {kind!r}"
                )
            },
        )
    summary = {**body.summary, "offerSnapshotId": snapshot.id}
    row = models.ApprovalRequest(
        trip_profile_id=snapshot.trip_candidate.search_session.trip_profile_id,
        commitment_class=snapshot.commitment_class,
        summary=summary,
        status=PENDING,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    freshness = _freshness(
        snapshot, None, reconciled=False, now=datetime.now(timezone.utc)
    )
    return JSONResponse(
        status_code=201, content=_view(row, freshness).model_dump(mode="json")
    )


@router.get("/{approval_id}")
def get_approval(
    approval_id: str,
    session: Session = Depends(get_session),
    reader: upstream.ReconciliationReader = Depends(get_reader),
):
    row = _get_approval(session, approval_id)
    if row is None:
        return JSONResponse(
            status_code=404, content={"detail": "ApprovalRequest not found"}
        )
    snapshot = _subject_snapshot(session, row)
    if snapshot is None:
        return JSONResponse(
            status_code=200, content=_view(row, None).model_dump(mode="json")
        )
    now = datetime.now(timezone.utc)
    evaluation = readthrough.reconcile(session, snapshot, reader, now=now)
    session.refresh(row)
    freshness = _freshness(snapshot, evaluation, reconciled=True, now=now)
    return JSONResponse(
        status_code=200, content=_view(row, freshness).model_dump(mode="json")
    )


@router.post("/{approval_id}/decision")
def decide_approval(
    approval_id: str,
    body: DecisionIn,
    session: Session = Depends(get_session),
    reader: upstream.ReconciliationReader = Depends(get_reader),
):
    if body.decision not in ("APPROVE", "REJECT"):
        return JSONResponse(
            status_code=422,
            content={
                "detail": f"decision must be APPROVE or REJECT, got {body.decision!r}"
            },
        )
    row = _get_approval(session, approval_id)
    if row is None:
        return JSONResponse(
            status_code=404, content={"detail": "ApprovalRequest not found"}
        )
    if row.status != PENDING:
        return JSONResponse(
            status_code=409,
            content={
                "detail": (
                    f"Approval already resolved with status {row.status}; "
                    "a resolved approval takes no further decision"
                )
            },
        )
    snapshot = _subject_snapshot(session, row)
    if snapshot is None:
        return JSONResponse(
            status_code=422,
            content={
                "detail": (
                    "This approval has no subject OfferSnapshot; the "
                    "gate cannot reconcile it, so it cannot be decided here"
                )
            },
        )

    now = datetime.now(timezone.utc)
    evaluation = readthrough.reconcile(session, snapshot, reader, now=now)
    session.refresh(row)

    if evaluation.code is DivergenceCode.UPSTREAM_UNAVAILABLE:
        # Blocks without killing: the approval stays PENDING and
        # the decision is retryable once the source answers.
        refusal = DecisionRefusal(
            approvalId=row.id,
            outcome="BLOCKED",
            code=evaluation.code.value,
            reason=None,
            reasonText=None,
            approvalStatus=row.status,
            evaluatedAt=now,
        )
        return JSONResponse(
            status_code=503, content=refusal.model_dump(mode="json")
        )

    if evaluation.code is DivergenceCode.SNAPSHOT_EXPIRED:
        # TTL dominance: no decision is recorded against an expired
        # snapshot, in either direction; the approval resolves to
        # EXPIRED (the status vocabulary's named use for this).
        row.status = EXPIRED
        row.resolved_at = now
        session.commit()
        refusal = DecisionRefusal(
            approvalId=row.id,
            outcome="REFUSED",
            code=evaluation.code.value,
            reason=None,
            reasonText=None,
            approvalStatus=row.status,
            evaluatedAt=now,
        )
        return JSONResponse(
            status_code=409, content=refusal.model_dump(mode="json")
        )

    if evaluation.code is not None and body.decision == "APPROVE":
        # A diverged snapshot cannot be approved. The refusal
        # surfaces the code — and for SEAT_TAKEN the reason, in
        # machine and plain-language form (R4 §5).
        refusal = DecisionRefusal(
            approvalId=row.id,
            outcome="REFUSED",
            code=evaluation.code.value,
            reason=evaluation.reason,
            reasonText=REASON_TEXT.get(evaluation.reason),
            approvalStatus=row.status,
            evaluatedAt=now,
        )
        return JSONResponse(
            status_code=409, content=refusal.model_dump(mode="json")
        )

    # Clean — or a REJECT against a diverged snapshot, which asserts
    # nothing about the snapshot and closes the request.
    row.status = APPROVED if body.decision == "APPROVE" else REJECTED
    row.signed_by = body.decidedBy
    row.resolved_at = now
    session.commit()
    freshness = _freshness(snapshot, evaluation, reconciled=True, now=now)
    return JSONResponse(
        status_code=200, content=_view(row, freshness).model_dump(mode="json")
    )
