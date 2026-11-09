"""ASSURATIES router — the claim > judge > resolved surface
(docs/specifications/07-ASSURATIES-CLAIM-RESOLUTION-EXTENSION.md).

  POST /api/v1/claims                     issue a claim (201, ISSUED)
  GET  /api/v1/claims/{id}                the claim
  POST /api/v1/claims/{id}/challenge      bond a challenge (ISSUED only)
  POST /api/v1/claims/{id}/judge          run the attested juror
  POST /api/v1/claims/{id}/finalize       RESOLVED_TRUE -> ASSURATIZED
  GET  /api/v1/reliance/claims            the Reliance API (x401-gated)
  GET  /api/v1/jurors                     juror scorecards (public)
  GET  /api/v1/learning/recent            the learning feed (public)

The juror is a team surface (spec 08): judging is precedent-
aware — before the juror runs, Assuratized claims in the claim's
micro-region are selected and rendered into its prompt as
precedents, and every juror accumulates a public scorecard from
finalized outcomes. The two public reads are projections derived
from the claim rows and the EventLog; nothing is stored for them
and nothing in them is invented.

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
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

import juror
import metering
import models
import sanitize
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
    # Untrusted-input sanitization (spec 08 §8): the statement
    # and the claimed value's string leaves are stripped of
    # invisible Unicode BEFORE they become the claim of record.
    # The sanitized form is what is stored, judged, and later
    # rendered as precedent — there is no unsanitized copy.
    statement = sanitize.strip_invisible(body.statement)
    if not statement:
        raise HTTPException(
            status_code=422,
            detail=(
                "statement carries no visible content once "
                "invisible characters are stripped"
            ),
        )
    claim = models.Claim(
        intent_id=body.intentId,
        claim_class=body.claimClass,
        period_kind=body.periodKind,
        statement=statement,
        claimed_value=sanitize.sanitize_value(body.claimedValue),
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


def _select_precedents(
    db: Session, claim: models.Claim
) -> tuple[list[dict[str, Any]], int]:
    """Precedent selection (spec 08 §2): Assuratized claims whose
    Intent sits in the same micro-region as this claim's Intent —
    the system's settled record for that market — most recent
    resolution first (claim id breaks ties, deterministically),
    capped at 3, the claim itself excluded. Rendered into the
    juror prompt by juror.py; the ids land on the juror report as
    precedentsUsed.

    Self-dealing exclusion (spec 08 §2, DeepSeek Q2(a)): two
    candidate classes are excluded BEFORE the cap, and counted:

      - precedents claimed by the SAME claimantEntityId as the
        claim under judgment — a claimant's own resolved record
        never informs judgments on their own claims;
      - precedents on the SAME Intent — a claim's siblings on the
        same asset, whoever claimed them.

    The roles that check each other must be separate: the field's
    demonstrated failure mode is one operator acting as writer,
    moderator, and juror at once. The returned excluded count
    lands on the juror report as precedentsExcludedSelfDealing —
    the exclusion is itself part of the judgment's record."""
    intent = db.get(models.Intent, claim.intent_id)
    if intent is None:
        return [], 0
    candidates = (
        db.query(models.Claim)
        .join(models.Intent, models.Claim.intent_id == models.Intent.id)
        .filter(
            models.Claim.status == models.ClaimStatus.ASSURATIZED,
            models.Intent.micro_region_id == intent.micro_region_id,
            models.Claim.id != claim.id,
        )
        .order_by(models.Claim.resolved_at.desc(), models.Claim.id)
        .all()
    )
    eligible: list[models.Claim] = []
    excluded = 0
    for row in candidates:
        if (
            row.claimant_entity_id == claim.claimant_entity_id
            or row.intent_id == claim.intent_id
        ):
            excluded += 1
        else:
            eligible.append(row)
    return [
        {
            "id": row.id,
            "statement": row.statement,
            "claimedValue": row.claimed_value,
            "outcome": "ASSURATIZED",
            "withstood": bool(
                row.challenge and row.challenge.get("withstood")
            ),
        }
        for row in eligible[:3]
    ], excluded


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
    precedents, precedents_excluded = _select_precedents(db, claim)
    precedent_ids = [p["id"] for p in precedents]
    claim_dict = _claim_view(claim).model_dump()
    claim_dict["precedents"] = precedents
    report = juror.judge_claim(claim_dict)
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
                "juror",
                "completionId",
                "verification",
                "transport",
                "transportNote",
                "requestedModel",
                "modelFallback",
                "precedentsUsed",
                "canaryId",
                "canaryTripped",
            )
            if report.get(key) is not None
        }
        # The selection of record is this endpoint's: what was
        # actually rendered into the prompt, whoever judged —
        # and how much of the settled record the self-dealing
        # exclusion held back from it.
        claim.juror_report["precedentsUsed"] = precedent_ids
        claim.juror_report["precedentsExcludedSelfDealing"] = (
            precedents_excluded
        )
        if report.get("juror") or report.get("model"):
            claim.juror_report["juror"] = (
                report.get("juror") or report.get("model")
            )
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
            "juror": report.get("juror") or report.get("model"),
            "precedentsUsed": precedent_ids,
            "precedentsExcludedSelfDealing": precedents_excluded,
            "attemptedAt": attempted_at,
        }
        # The canary record (spec 08 §8) rides on attempted
        # judgments — ok or error — whenever the juror ran.
        for key in ("canaryId", "canaryTripped"):
            if report.get(key) is not None:
                claim.juror_report[key] = report[key]
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
            "juror": report.get("juror") or report.get("model"),
            "precedentsUsed": precedent_ids,
            "precedentsExcludedSelfDealing": precedents_excluded,
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


# ---------------------------------------------------------------------
# The juror team surfaces (spec 08) — public, read-only projections.
# No auth: these are the system's reputation and memory, published
# the way the Day 6 reads publish market state. Both are DERIVED
# from the claim rows and the EventLog on every call — no counters
# are stored anywhere, so nothing here can drift from the record.
# ---------------------------------------------------------------------


def _juror_identity(report: dict[str, Any] | None) -> str | None:
    """A juror report's stable identity: the "juror" key (the
    model actually used), falling back to "model" for reports
    recorded before the identity was made explicit."""
    if not report:
        return None
    return report.get("juror") or report.get("model")


def _empty_card(identity: str) -> dict[str, Any]:
    return {
        "juror": identity,
        "judgedCount": 0,
        "upheldCount": 0,
        "refutedCount": 0,
        "withstoodCount": 0,
        "unavailableCount": 0,
        "attemptCount": 0,
        "panelDissents": 0,
    }


@router.get("/jurors")
def juror_scorecards(db: Session = Depends(get_session)):
    """One scorecard per juror identity, EVENT-SOURCED from the
    append-only EventLog (spec 08 §3, DeepSeek Q4 fix):

      attempts        EVERY claim.judged event is an attempt by
                      its recorded juror with its recorded outcome
                      (payload juror / jurorOutcome, written by
                      the judge endpoint since the claims build;
                      panel events carry per-seat panelAttempts,
                      each one a seat attempt). attemptCount is
                      the total; unavailableCount is the attempts
                      whose outcome was unavailable or error —
                      INCLUDING attempts a later judgment
                      superseded. (The pre-fix derivation read
                      each claim's CURRENT jurorReport, so a
                      superseded attempt vanished from the
                      record; the log does not forget.)
      terminal credit a claim's DECIDING judgment is its last
                      claim.judged event with jurorOutcome "ok".
                      ASSURATIZED credits upheld (+withstood when
                      the claim's challenge was withstood);
                      RESOLVED_FALSE credits refuted. A single
                      juror is credited directly. A panel credits
                      the seats whose verdict matched the panel
                      verdict; a seat whose parsed verdict
                      differed is recorded as a dissent
                      (panelDissents); abstaining seats are
                      credited with neither.
      judgedCount     terminal claims credited to this juror
                      (upheld + refuted).

    Events whose payload carries no juror identity are skipped —
    never attributed by guess. Only jurors with at least one
    judged (terminal, credited) claim appear. Ordering is
    deterministic: juror identity ascending."""
    cards: dict[str, dict[str, Any]] = {}

    def card_for(identity: str) -> dict[str, Any]:
        return cards.setdefault(identity, _empty_card(identity))

    events = (
        db.query(models.EventLog)
        .filter(
            models.EventLog.aggregate_type == "claim",
            models.EventLog.event_type == "claim.judged",
        )
        .order_by(models.EventLog.id)
        .all()
    )
    deciding: dict[str, dict[str, Any]] = {}
    for event in events:
        payload = event.payload or {}
        panel_attempts = payload.get("panelAttempts")
        if panel_attempts:
            for attempt in panel_attempts:
                identity = attempt.get("juror")
                if identity is None:
                    continue
                card = card_for(identity)
                card["attemptCount"] += 1
                if attempt.get("outcome") in ("unavailable", "error"):
                    card["unavailableCount"] += 1
            if payload.get("jurorOutcome") == "ok":
                deciding[event.aggregate_id] = {
                    "kind": "panel",
                    "verdict": payload.get("verdict"),
                    "seats": {
                        a.get("juror"): a.get("verdict")
                        for a in panel_attempts
                        if a.get("outcome") == "ok"
                        and a.get("juror") is not None
                    },
                }
            continue
        identity = payload.get("juror")
        if identity is None:
            continue
        card = card_for(identity)
        card["attemptCount"] += 1
        if payload.get("jurorOutcome") in ("unavailable", "error"):
            card["unavailableCount"] += 1
        if payload.get("jurorOutcome") == "ok":
            deciding[event.aggregate_id] = {
                "kind": "single",
                "verdict": payload.get("verdict"),
                "juror": identity,
            }

    terminal_claims = (
        db.query(models.Claim)
        .filter(
            models.Claim.status.in_(
                [
                    models.ClaimStatus.ASSURATIZED,
                    models.ClaimStatus.RESOLVED_FALSE,
                ]
            )
        )
        .all()
    )
    for claim in terminal_claims:
        attribution = deciding.get(claim.id)
        if attribution is None:
            continue
        upheld = claim.status is models.ClaimStatus.ASSURATIZED
        withstood = bool(
            upheld and claim.challenge and claim.challenge.get("withstood")
        )
        if attribution["kind"] == "single":
            credited = [attribution["juror"]]
            dissenters: list[str] = []
        else:
            panel_verdict = attribution["verdict"]
            credited = [
                identity
                for identity, verdict in attribution["seats"].items()
                if verdict == panel_verdict
            ]
            dissenters = [
                identity
                for identity, verdict in attribution["seats"].items()
                if verdict in juror.VERDICTS and verdict != panel_verdict
            ]
        for identity in credited:
            card = card_for(identity)
            card["judgedCount"] += 1
            if upheld:
                card["upheldCount"] += 1
                if withstood:
                    card["withstoodCount"] += 1
            else:
                card["refutedCount"] += 1
        for identity in dissenters:
            card_for(identity)["panelDissents"] += 1

    jurors = [c for c in cards.values() if c["judgedCount"] >= 1]
    jurors.sort(key=lambda c: c["juror"])
    return {"surface": "juror-scorecards", "jurors": jurors}


@router.get("/learning/recent")
def learning_recent(
    limit: int = 20, db: Session = Depends(get_session)
):
    """The learning feed: the system's terminal learning events,
    newest first. Two event kinds are terminal for a claim —
    claim.finalized (the claim became ASSURATIZED and entered the
    comparable ledger) and a claim.judged event whose outcome was
    RESOLVED_FALSE (the refutation is terminal; finalize is
    refused for it). Every entry is joined back to its claim row;
    no field is invented. limit defaults to 20, capped at 50."""
    limit = min(max(limit, 1), 50)
    terminal = or_(
        models.EventLog.event_type == "claim.finalized",
        and_(
            models.EventLog.event_type == "claim.judged",
            models.EventLog.payload["toStatus"].as_string()
            == "RESOLVED_FALSE",
        ),
    )
    rows = (
        db.query(models.EventLog, models.Claim)
        .join(
            models.Claim,
            models.EventLog.aggregate_id == models.Claim.id,
        )
        .filter(
            models.EventLog.aggregate_type == "claim",
            terminal,
        )
        .order_by(models.EventLog.id.desc())
        .limit(limit)
        .all()
    )
    entries = []
    for event, claim in rows:
        outcome = (
            "ASSURATIZED"
            if event.event_type == "claim.finalized"
            else "RESOLVED_FALSE"
        )
        report = claim.juror_report or {}
        entries.append(
            {
                "claimId": claim.id,
                "outcome": outcome,
                "juror": _juror_identity(report),
                "precedentsUsedCount": len(
                    report.get("precedentsUsed") or []
                ),
                "comparableAdded": outcome == "ASSURATIZED",
                "claimantEntityId": claim.claimant_entity_id,
                "resolvedAt": claim.resolved_at,
            }
        )
    return {"surface": "learning-feed", "entries": entries}
