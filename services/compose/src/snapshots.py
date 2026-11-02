"""Snapshots router — the R4 read-through surface (Sprint 1, slice 2).

POST /snapshots/{snapshot_id}/reconcile
    Run commit-path reconciliation (§6) for one ticket-kind
    OfferSnapshot NOW, at request time: TTL check, live re-read
    through the reconciliation reader, typed divergence evaluation,
    EventLog recording, and the divergence annotation for killing
    codes. This is the evaluation the approval gate and the commit
    path both consume; settlement itself (commitment recording) is
    the NEXT Sprint 1 slice and is deliberately not here.

Responses — the identical field set on the agent API and the human
UI (R4 §2.3 surface parity; there is one surface here by design):
  200  outcome CLEAN — no divergence; the snapshot may proceed.
  409  outcome DIVERGED — a killing code fired; the snapshot is
       dead for commit purposes. Body carries the code and, for
       SEAT_TAKEN, the reason (MODERATION | DOUBLE_SETTLEMENT).
  503  outcome BLOCKED — UPSTREAM_UNAVAILABLE; the snapshot is NOT
       killed and the call is retryable once the source answers.
  404  no such snapshot.  422  the snapshot is not ticket-kind
       (Sprint 1 reconciles the ticket rail only).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

import models
import readthrough
import upstream
from db import get_session

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


class ReconcileView(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshotId: str
    outcome: str  # CLEAN | DIVERGED | BLOCKED
    code: str | None
    reason: str | None
    killsSnapshot: bool
    observed: dict | None
    evaluatedAt: datetime


def get_reader() -> upstream.ReconciliationReader:
    """FastAPI dependency: the reconciliation reader for this
    process (upstream.build_reader — direct reader when a base URL
    is configured, the honest unavailable reader otherwise). Tests
    override this dependency with the interim listing-read proxy."""
    return upstream.build_reader()


@router.post("/{snapshot_id}/reconcile", response_model=ReconcileView)
def reconcile_snapshot(
    snapshot_id: str,
    session: Session = Depends(get_session),
    reader: upstream.ReconciliationReader = Depends(get_reader),
):
    snapshot = session.get(models.OfferSnapshot, snapshot_id)
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
                    "Read-through reconciliation is implemented for the "
                    f"ticket kind only (Sprint 1); this snapshot is {kind!r}"
                )
            },
        )

    evaluation = readthrough.reconcile(session, snapshot, reader)
    if evaluation.clean:
        outcome, status_code = "CLEAN", 200
    elif evaluation.code is models.DivergenceCode.UPSTREAM_UNAVAILABLE:
        outcome, status_code = "BLOCKED", 503
    else:
        outcome, status_code = "DIVERGED", 409

    view = ReconcileView(
        snapshotId=snapshot.id,
        outcome=outcome,
        code=evaluation.code.value if evaluation.code else None,
        reason=evaluation.reason,
        killsSnapshot=evaluation.kills_snapshot,
        observed=evaluation.observed,
        evaluatedAt=datetime.now(timezone.utc),
    )
    return JSONResponse(status_code=status_code, content=view.model_dump(mode="json"))
