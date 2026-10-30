"""Intakes router — the intake/classify slice's write and read path.

POST /intakes              create a draft from raw answers, classify,
                           persist the draft + its classification
GET  /intakes/{id}         the draft, with its classification recomputed
                           (classify() is deterministic, so a recompute
                           IS the stored state's classification — the
                           persisted missingSlots/invalidSlots columns
                           are the at-write record)
POST /intakes/{id}/answers merge more answers in, re-classify, persist

Semantics, stated once here:
  - The ACTIVE manifest governs every classification: the active
    QuestionManifest with the highest version (ties broken by key).
    If none is active, creation and reads fail with 409 — the slice
    classifies against authored data or not at all.
  - A null answer is no answer: null-valued keys are dropped from
    stored answers, and in an /answers merge a null value DELETES
    that answer (the way to correct a wrong one).
  - Drafts expire 72h after creation (the IntakeDraft lifetime the
    schema's docstring names); answering an expired draft is 410.
  - Classification on read uses the CURRENT active manifest, as on
    write. Manifests are versioned authored data; if the active
    manifest changes between writes, the draft's classification
    follows the current one — stated, not hidden.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

import models
from classify import ClassifyResult, classify
from db import get_session
from questionmanifest_pydantic import QuestionManifest as ManifestModel

router = APIRouter(prefix="/intakes", tags=["intakes"])

DRAFT_TTL = timedelta(hours=72)


class IntakeCreate(BaseModel):
    answers: dict[str, Any] = {}
    token: str | None = None


class AnswersIn(BaseModel):
    answers: dict[str, Any]


class IntakeView(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    token: str
    answers: dict[str, Any]
    satisfiedSlots: list[str]
    missingSlots: list[str]
    deferredSlots: list[str]
    invalidSlots: dict[str, str]
    notApplicableSlots: list[str]
    optionalSlots: list[str]
    modules: list[str]
    moduleReadiness: dict[str, str]
    expiresAt: datetime
    createdAt: datetime


def _active_manifest(session: Session) -> ManifestModel:
    row = (
        session.query(models.QuestionManifest)
        .filter_by(active=True)
        .order_by(models.QuestionManifest.version.desc(),
                  models.QuestionManifest.key.asc())
        .first()
    )
    if row is None:
        raise HTTPException(status_code=409, detail="No active QuestionManifest")
    return ManifestModel.model_validate(
        {
            "id": row.id,
            "key": row.key,
            "version": row.version,
            "title": row.title,
            "questions": row.questions,
            "active": row.active,
            "createdAt": row.created_at,
        }
    )


def _view(row: models.IntakeDraft, result: ClassifyResult) -> IntakeView:
    return IntakeView(
        id=row.id,
        token=row.token,
        answers=row.answers,
        satisfiedSlots=result.satisfied,
        missingSlots=result.missing,
        deferredSlots=result.deferred,
        invalidSlots=result.invalid,
        notApplicableSlots=result.notApplicable,
        optionalSlots=result.optional,
        modules=result.modules,
        moduleReadiness=result.moduleReadiness,
        expiresAt=row.expires_at,
        createdAt=row.created_at,
    )


def _clean(answers: dict[str, Any]) -> dict[str, Any]:
    """Null is no answer — drop null-valued keys."""
    return {k: v for k, v in answers.items() if v is not None}


def _get_draft(session: Session, intake_id: str) -> models.IntakeDraft:
    row = session.get(models.IntakeDraft, intake_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Intake not found")
    return row


@router.post("", response_model=IntakeView, status_code=201)
def create_intake(body: IntakeCreate, session: Session = Depends(get_session)):
    manifest = _active_manifest(session)
    answers = _clean(body.answers)
    result = classify(answers, manifest)
    token = body.token or str(uuid.uuid4())
    if session.query(models.IntakeDraft).filter_by(token=token).first():
        raise HTTPException(status_code=409, detail="Token already in use")
    row = models.IntakeDraft(
        token=token,
        answers=answers,
        missing_slots=result.missing,
        invalid_slots=result.invalid,
        expires_at=datetime.now(timezone.utc) + DRAFT_TTL,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _view(row, result)


@router.get("/{intake_id}", response_model=IntakeView)
def get_intake(intake_id: str, session: Session = Depends(get_session)):
    row = _get_draft(session, intake_id)
    result = classify(row.answers, _active_manifest(session))
    return _view(row, result)


@router.post("/{intake_id}/answers", response_model=IntakeView)
def add_answers(
    intake_id: str, body: AnswersIn, session: Session = Depends(get_session)
):
    row = _get_draft(session, intake_id)
    if row.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Intake draft expired")
    merged = dict(row.answers)
    for key, value in body.answers.items():
        if value is None:
            merged.pop(key, None)  # a null value deletes the answer
        else:
            merged[key] = value
    result = classify(merged, _active_manifest(session))
    row.answers = merged
    row.missing_slots = result.missing
    row.invalid_slots = result.invalid
    session.commit()
    session.refresh(row)
    return _view(row, result)
