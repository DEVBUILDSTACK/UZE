"""ASSURATIES router — the claim > judge > resolved surface
(docs/specifications/07-ASSURATIES-CLAIM-RESOLUTION-EXTENSION.md).

  POST /api/v1/claims                     issue a claim (201, ISSUED)
  GET  /api/v1/claims/{id}                the claim
  POST /api/v1/claims/{id}/challenge      bond a challenge (ISSUED only)
  POST /api/v1/claims/{id}/judge          run the attested juror
  POST /api/v1/claims/{id}/finalize       RESOLVED_TRUE -> ASSURATIZED
  GET  /api/v1/reliance/claims            the Reliance API (x401-gated)

State discipline is the evidence-gated architecture's: single-step
transitions only, each guarded — a wrong state is a 409, never a
silent jump — and finalize additionally requires an explicit
authorization reference (missing -> 422), the agtech workflow
guard's pattern. Every transition writes an append-only EventLog
row (claim.issued / claim.challenged / claim.judged /
claim.finalized); the EventLog is the resolution trail the
Reliance API serves.

Iron Rule (spec 07 §7): no transition here executes a financial
transaction. bondAmount values are mock units recorded on the
claim. Settlement stays USDC on Solana, in the settle flow.

The ARCIUM confidential tier is a data flag in this build:
confidentialTier=ARCIUM claims are accepted, flagged, judged on
the standard juror path, and — once ASSURATIZED — carry the
"ASSURATIZED @ARCIUM" resolution mark. No Arcium calls are made;
the MPC plug-in is Sprint 2 work behind the parleyswap scaffold
interface (spec 07 §6).
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

import juror
import metering
import models
from db import get_session

router = APIRouter(prefix="/api/v1", tags=["assuraties"])

_JUDGEABLE = frozenset(
    {
        models.ClaimStatus.ISSUED,
        models.ClaimStatus.CHALLENGED,
        models.ClaimStatus.UNDER_RESOLUTION,
    }
)


class ClaimIn(BaseModel):
    intentId: str
    claimClass: models.ClaimClass
    periodKind: models.ClaimPeriodKind | None = None
    statement: str = Field(min_length=1)
    claimedValue: Any
    claimantEntityId: str = Field(min_length=1)
    bondAmount: int = Field(default=0, ge=0)
    confidentialTier: models.ConfidentialTier = models.ConfidentialTier.STANDARD


class ChallengeIn(BaseModel):
    challengerEntityId: str = Field(min_length=1)
    bondAmount: int = Field(gt=0)


class FinalizeIn(BaseModel):
    authorizationReference: str = Field(min_length=1)
    actor: str | None = None


class ClaimView(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    intentId: str
    claimClass: str
    periodKind: str | None
    statement: str
    claimedValue: Any
    claimantEntityId: str
    bondAmount: int
    status: str
    confidentialTier: str
    jurorReport: dict[str, Any] | None
    challenge: dict[str, Any] | None
    withstood: bool
    resolutionMark: str | None
    createdAt: int
    resolvedAt: int | None


def _claim_view(claim: models.Claim) -> ClaimView:
    status = claim.status
    mark = None
    if status is models.ClaimStatus.ASSURATIZED:
        mark = (
            "ASSURATIZED @ARCIUM"
            if claim.confidential_tier is models.ConfidentialTier.ARCIUM
            else "ASSURATIZED"
        )
    return ClaimView(
        id=claim.id,
        intentId=claim.intent_id,
        claimClass=claim.claim_class.value,
        periodKind=claim.period_kind.value if claim.period_kind else None,
        statement=claim.statement,
        claimedValue=claim.claimed_value,
        claimantEntityId=claim.claimant_entity_id,
        bondAmount=claim.bond_amount,
        status=status.value,
        confidentialTier=claim.confidential_tier.value,
        jurorReport=claim.juror_report,
        challenge=claim.challenge,
        withstood=bool(claim.challenge and claim.challenge.get("withstood")),
        resolutionMark=mark,
        createdAt=claim.created_at,
        resolvedAt=claim.resolved_at,
    )


def _log(
    db: Session,
    claim: models.Claim,
    event_type: str,
    actor: str,
    payload: dict[str, Any],
) -> None:
    db.add(
        models.EventLog(
            aggregate_type="claim",
            aggregate_id=claim.id,
            event_type=event_type,
            actor=actor,
            payload=payload,
        )
    )


def _get_claim(db: Session, claim_id: str) -> models.Claim:
    claim = db.get(models.Claim, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="claim not found")
    return claim


@router.post("/claims", status_code=201)
def issue_claim(body: ClaimIn, db: Session = Depends(get_session)):
    intent = db.get(models.Intent, body.intentId)
    if intent is None:
        raise HTTPException(status_code=404, detail="intent not found")
    if body.claimClass is models.ClaimClass.HICRE_PERIOD:
        if body.periodKind is None:
            raise HTTPException(
                status_code=422,
                detail="HICRE_PERIOD claims require periodKind",
            )
    elif body.periodKind is not None:
        raise HTTPException(
            status_code=422,
            detail="periodKind is only valid on HICRE_PERIOD claims",
        )
    claim = models.Claim(
        intent_id=body.intentId,
        claim_class=body.claimClass,
        period_kind=body.periodKind,
        statement=body.statement,
        claimed_value=body.claimedValue,
        claimant_entity_id=body.claimantEntityId,
        bond_amount=body.bondAmount,
        status=models.ClaimStatus.ISSUED,
        confidential_tier=body.confidentialTier,
        created_at=int(time.time()),
    )
    db.add(claim)
    db.flush()  # the EventLog row references the claim's id
    _log(
        db,
        claim,
        "claim.issued",
        actor=f"entity:{claim.claimant_entity_id}",
        payload={
            "claimClass": claim.claim_class.value,
            "periodKind": claim.period_kind.value if claim.period_kind else None,
            "bondAmount": claim.bond_amount,
            "confidentialTier": claim.confidential_tier.value,
        },
    )
    db.commit()
    return _claim_view(claim)


@router.get("/claims/{claim_id}")
def get_claim(claim_id: str, db: Session = Depends(get_session)):
    return _claim_view(_get_claim(db, claim_id))


@router.post("/claims/{claim_id}/challenge")
def challenge_claim(
    claim_id: str, body: ChallengeIn, db: Session = Depends(get_session)
):
    claim = _get_claim(db, claim_id)
    if claim.status is not models.ClaimStatus.ISSUED:
        raise HTTPException(
            status_code=409,
            detail=(
                f"a claim in state {claim.status.value} cannot be "
                "challenged; challenges are lawful only from ISSUED"
            ),
        )
    claim.challenge = {
        "challengerEntityId": body.challengerEntityId,
        "bondAmount": body.bondAmount,
        "challengedAt": int(time.time()),
    }
    claim.status = models.ClaimStatus.CHALLENGED
    _log(
        db,
        claim,
        "claim.challenged",
        actor=f"entity:{body.challengerEntityId}",
        payload={
            "challengerEntityId": body.challengerEntityId,
            "bondAmount": body.bondAmount,
        },
    )
    db.commit()
    return _claim_view(claim)


@router.post("/claims/{claim_id}/judge")
def judge_claim_endpoint(claim_id: str, db: Session = Depends(get_session)):
    claim = _get_claim(db, claim_id)
    if claim.status not in _JUDGEABLE:
        raise HTTPException(
            status_code=409,
            detail=(
                f"a claim in state {claim.status.value} cannot be "
                "judged; judging is lawful from ISSUED, CHALLENGED, "
                "or UNDER_RESOLUTION"
            ),
        )
    from_status = claim.status
    claim.status = models.ClaimStatus.UNDER_RESOLUTION
    report = juror.judge_claim(_claim_view(claim).model_dump())
    attempted_at = int(time.time())
    if report.get("status") == "ok":
        claim.juror_report = {
            key: report[key]
            for key in (
                "status",
                "verdict",
                "rationale",
                "confidence",
                "model",
                "completionId",
                "verification",
                "transport",
                "transportNote",
                "requestedModel",
                "modelFallback",
            )
            if report.get(key) is not None
        }
        claim.status = (
            models.ClaimStatus.RESOLVED_TRUE
            if report["verdict"] == "UPHELD"
            else models.ClaimStatus.RESOLVED_FALSE
        )
        claim.resolved_at = attempted_at
    else:
        # The juror could not run: the reason is recorded and the
        # claim rests at UNDER_RESOLUTION. No verdict is fabricated.
        claim.juror_report = {
            "status": report.get("status"),
            "reason": report.get("reason"),
            "model": report.get("model"),
            "attemptedAt": attempted_at,
        }
    _log(
        db,
        claim,
        "claim.judged",
        actor="agent:JUROR",
        payload={
            "fromStatus": from_status.value,
            "toStatus": claim.status.value,
            "jurorOutcome": report.get("status"),
            "verdict": report.get("verdict"),
        },
    )
    db.commit()
    return _claim_view(claim)


@router.post("/claims/{claim_id}/finalize")
def finalize_claim(
    claim_id: str, body: FinalizeIn, db: Session = Depends(get_session)
):
    claim = _get_claim(db, claim_id)
    if claim.status is not models.ClaimStatus.RESOLVED_TRUE:
        raise HTTPException(
            status_code=409,
            detail=(
                f"a claim in state {claim.status.value} cannot be "
                "finalized; only RESOLVED_TRUE finalizes to "
                "ASSURATIZED (RESOLVED_FALSE never does)"
            ),
        )
    withstood = claim.challenge is not None
    if withstood:
        claim.challenge = {**claim.challenge, "withstood": True}
    claim.status = models.ClaimStatus.ASSURATIZED
    _log(
        db,
        claim,
        "claim.finalized",
        actor=body.actor or "system:assuraties",
        payload={
            "fromStatus": models.ClaimStatus.RESOLVED_TRUE.value,
            "toStatus": models.ClaimStatus.ASSURATIZED.value,
            "withstood": withstood,
            "authorizationReferencePresent": True,
            "confidentialTier": claim.confidential_tier.value,
        },
    )
    db.commit()
    return _claim_view(claim)


# ---------------------------------------------------------------------
# The Reliance API — the financing-partner read surface (spec 07 §8).
# x401-gated exactly like the agent surface (metering's identity
# stub; no X-IDENTITY -> 401). Returns ONLY ASSURATIZED claims:
# open, challenged, under-resolution, and resolved-false claims are
# not reliance material and are excluded by construction.
# ---------------------------------------------------------------------


def _juror_summary(report: dict[str, Any] | None) -> dict[str, Any] | None:
    if not report:
        return None
    return {
        key: report.get(key)
        for key in (
            "status",
            "verdict",
            "rationale",
            "confidence",
            "model",
            "completionId",
            "verification",
        )
    }


@router.get("/reliance/claims")
def reliance_claims(
    request: Request,
    intentId: str | None = None,
    db: Session = Depends(get_session),
):
    identity_header = request.headers.get("X-IDENTITY")
    if not identity_header:
        return JSONResponse(
            status_code=401,
            content={
                "error": "X-IDENTITY header is required (x401)",
                "mock": True,
            },
        )
    ok, identity = metering.verify_identity_payload(
        metering._decode_header(identity_header)
    )
    if not ok:
        return JSONResponse(
            status_code=401,
            content={
                "error": identity.get(
                    "error", "identity verification failed"
                ),
                "mock": True,
            },
        )

    query = db.query(models.Claim).filter(
        models.Claim.status == models.ClaimStatus.ASSURATIZED
    )
    if intentId is not None:
        query = query.filter(models.Claim.intent_id == intentId)
    claims = query.order_by(models.Claim.created_at).all()

    items = []
    for claim in claims:
        view = _claim_view(claim)
        events = (
            db.query(models.EventLog)
            .filter(
                models.EventLog.aggregate_type == "claim",
                models.EventLog.aggregate_id == claim.id,
            )
            .order_by(models.EventLog.id)
            .all()
        )
        items.append(
            {
                **view.model_dump(),
                "bond": {
                    "claimantBond": claim.bond_amount,
                    "challengeBond": (
                        claim.challenge.get("bondAmount")
                        if claim.challenge
                        else None
                    ),
                },
                "jurorReportSummary": _juror_summary(claim.juror_report),
                "resolutionTrail": [
                    {
                        "eventType": e.event_type,
                        "actor": e.actor,
                        "ts": e.ts.isoformat() if e.ts else None,
                        "payload": e.payload,
                    }
                    for e in events
                ],
            }
        )
    return {
        "surface": "reliance",
        "identity": {
            "subject": identity.get("subject"),
            "verified": True,
            "mock": True,
        },
        "claims": items,
    }
