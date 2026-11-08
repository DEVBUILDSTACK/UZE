"""DevPartner ingestion API — POST /api/v1/partners/ingest.

The Snapshot Pattern (partners/README.md): a partner pushes a JSON
payload with its Bearer token; the token maps to exactly one
partner_id; the payload is validated against the partner's filed
JSON schema (partners/schemas/); the validated payload is cached
verbatim in ProviderSnapshot so downstream consumers query our
database, not the partner's API.

Governance (Evidence-Gated Architecture): every partner is
UNVERIFIED until an agreement is signed and its API is reviewed, so
snapshots are stored with provider_status "UNVERIFIED" and nothing
downstream executes on them. This endpoint accepts and caches —
it authorizes nothing.

Configuration:
  PARTNER_API_TOKENS  JSON object mapping bearer token -> partner_id,
                      e.g. {"tok-...": "AGRO_DIGITAL"}. Unconfigured
                      -> the endpoint answers 503, never open.
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

    snapshot = models.ProviderSnapshot(
        partner_id=partner_id,
        data_category=DATA_CATEGORIES[partner_id],
        raw_payload=body,
        fetched_at=int(time.time()),
        cache_status="LIVE",
        provider_status="UNVERIFIED",
    )
    db.add(snapshot)
    db.flush()
    db.add(
        models.EventLog(
            aggregate_type="provider_snapshot",
            aggregate_id=snapshot.id,
            event_type="partner.snapshot_ingested",
            actor=f"partner:{partner_id}",
            payload={
                "dataCategory": snapshot.data_category,
                "polygonId": body.get("polygon_id"),
                "providerStatus": "UNVERIFIED",
            },
        )
    )
    db.commit()

    return JSONResponse(
        status_code=202,
        content={
            "snapshot_id": snapshot.id,
            "partner_id": partner_id,
            "data_category": snapshot.data_category,
            "cache_status": snapshot.cache_status,
            "provider_status": snapshot.provider_status,
        },
    )
