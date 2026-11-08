"""DevPartner ingestion API — POST /api/v1/partners/ingest.

The Snapshot Pattern (partners/README.md): a partner pushes a JSON
payload with its Bearer token; the token maps to exactly one
partner_id; the payload is validated against the partner's filed
JSON schema (partners/schemas/); the validated payload lands in
the STAGING table (StagingProviderSnapshot, approval_status
PENDING). An admin then approves it — which copies it verbatim
into ProviderSnapshot, the live cache downstream consumers query —
or rejects it with a recorded reason. This is the onboarding gate
from the partner-facing flow: sandbox first, review, then live.

Governance (Evidence-Gated Architecture): every partner is
UNVERIFIED until an agreement is signed and its API is reviewed, so
snapshots are stored with provider_status "UNVERIFIED" and nothing
downstream executes on them. Approval gates consumption, not
truth.

Configuration:
  PARTNER_API_TOKENS  JSON object mapping bearer token -> partner_id,
                      e.g. {"tok-...": "AGRO_DIGITAL"}. Unconfigured
                      -> the endpoint answers 503, never open.
  PARTNER_ADMIN_TOKEN Bearer token for the admin approval API.
                      Unconfigured -> the admin API answers 503.
  PARTNER_SCHEMAS_DIR Optional override for the schemas directory;
                      defaults to the repo's partners/schemas folder.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator
from sqlalchemy.orm import Session

import models
from db import get_session

router = APIRouter(prefix="/api/v1/partners")

SCHEMA_FILES = {
    "AGRO_DIGITAL": "agro-digital.json",
    "BDCS": "bdcs.json",
    "EFFATHA": "effatha.json",
}

DATA_CATEGORIES = {
    "AGRO_DIGITAL": "SOIL_SPATIAL",
    "BDCS": "FEEDLOT",
    "EFFATHA": "AGROTECHNICAL",
}


def _tokens() -> dict[str, str]:
    raw = os.environ.get("PARTNER_API_TOKENS")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(k): str(v) for k, v in parsed.items()}


def _schemas_dir() -> Path:
    override = os.environ.get("PARTNER_SCHEMAS_DIR")
    if override:
        return Path(override)
    # services/compose/src/partners.py -> repo root / partners / schemas
    return Path(__file__).resolve().parents[3] / "partners" / "schemas"


def _validator(partner_id: str) -> Draft202012Validator:
    schema_file = _schemas_dir() / SCHEMA_FILES[partner_id]
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


@router.post("/ingest", status_code=202)
async def partner_ingest(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_session),
):
    tokens = _tokens()
    if not tokens:
        raise HTTPException(
            status_code=503,
            detail="partner ingestion is not configured on this deployment",
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    partner_id = tokens.get(token)
    if partner_id is None or partner_id not in SCHEMA_FILES:
        raise HTTPException(status_code=401, detail="unknown bearer token")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=422, detail="body is not valid JSON")
    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="body must be a JSON object")

    if body.get("partner_id") != partner_id:
        raise HTTPException(
            status_code=403,
            detail="payload partner_id does not match the token's partner",
        )

    errors = sorted(
        _validator(partner_id).iter_errors(body),
        key=lambda e: list(e.absolute_path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(p) for p in first.absolute_path) or "(root)"
        raise HTTPException(
            status_code=422,
            detail=f"schema validation failed at {location}: {first.message}",
        )

    staged = models.StagingProviderSnapshot(
        partner_id=partner_id,
        data_category=DATA_CATEGORIES[partner_id],
        raw_payload=body,
        fetched_at=int(time.time()),
        approval_status="PENDING",
    )
    db.add(staged)
    db.flush()
    db.add(
        models.EventLog(
            aggregate_type="staging_provider_snapshot",
            aggregate_id=staged.id,
            event_type="partner.snapshot_staged",
            actor=f"partner:{partner_id}",
            payload={
                "dataCategory": staged.data_category,
                "polygonId": body.get("polygon_id"),
                "approvalStatus": "PENDING",
                "providerStatus": "UNVERIFIED",
            },
        )
    )
    db.commit()

    return JSONResponse(
        status_code=202,
        content={
            "staging_id": staged.id,
            "partner_id": partner_id,
            "data_category": staged.data_category,
            "approval_status": staged.approval_status,
            "provider_status": "UNVERIFIED",
        },
    )


admin_router = APIRouter(prefix="/api/v1/admin/partners")


def _require_admin(authorization: str | None) -> None:
    expected = os.environ.get("PARTNER_ADMIN_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="partner admin API is not configured on this deployment",
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    if authorization.removeprefix("Bearer ").strip() != expected:
        raise HTTPException(status_code=401, detail="unknown bearer token")


def _pending_staged(db: Session, staging_id: str) -> models.StagingProviderSnapshot:
    staged = db.get(models.StagingProviderSnapshot, staging_id)
    if staged is None:
        raise HTTPException(status_code=404, detail="staging_id not found")
    if staged.approval_status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail=f"staging payload already decided: {staged.approval_status}",
        )
    return staged


@admin_router.post("/approve/{staging_id}")
def partner_approve(
    staging_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_session),
):
    """Move a staged payload into the live ProviderSnapshot cache."""
    _require_admin(authorization)
    staged = _pending_staged(db, staging_id)

    snapshot = models.ProviderSnapshot(
        partner_id=staged.partner_id,
        data_category=staged.data_category,
        raw_payload=staged.raw_payload,
        fetched_at=staged.fetched_at,
        cache_status="LIVE",
        provider_status="UNVERIFIED",
    )
    db.add(snapshot)
    db.flush()
    staged.approval_status = "APPROVED"
    staged.reviewed_at = int(time.time())
    staged.reviewed_by = "partner-admin"
    db.add(
        models.EventLog(
            aggregate_type="provider_snapshot",
            aggregate_id=snapshot.id,
            event_type="partner.snapshot_approved",
            actor="partner-admin",
            payload={
                "stagingId": staged.id,
                "partnerId": staged.partner_id,
                "dataCategory": staged.data_category,
                "providerStatus": "UNVERIFIED",
            },
        )
    )
    db.commit()

    return JSONResponse(
        status_code=200,
        content={
            "staging_id": staged.id,
            "snapshot_id": snapshot.id,
            "approval_status": "APPROVED",
        },
    )


@admin_router.post("/reject/{staging_id}")
async def partner_reject(
    staging_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_session),
):
    """Reject a staged payload, recording the reason. Nothing goes live."""
    _require_admin(authorization)
    staged = _pending_staged(db, staging_id)

    try:
        body = await request.json()
    except Exception:
        body = {}
    reason = (body or {}).get("reason") if isinstance(body, dict) else None
    if not reason or not str(reason).strip():
        raise HTTPException(status_code=422, detail="a rejection reason is required")

    staged.approval_status = "REJECTED"
    staged.rejection_reason = str(reason)
    staged.reviewed_at = int(time.time())
    staged.reviewed_by = "partner-admin"
    db.add(
        models.EventLog(
            aggregate_type="staging_provider_snapshot",
            aggregate_id=staged.id,
            event_type="partner.snapshot_rejected",
            actor="partner-admin",
            payload={
                "partnerId": staged.partner_id,
                "rejectionReason": staged.rejection_reason,
            },
        )
    )
    db.commit()

    return JSONResponse(
        status_code=200,
        content={
            "staging_id": staged.id,
            "approval_status": "REJECTED",
            "rejection_reason": staged.rejection_reason,
        },
    )
