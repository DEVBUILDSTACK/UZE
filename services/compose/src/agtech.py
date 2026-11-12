"""Agriculture referral webhook — evidence-gated intake.

Implements step 3 of docs/specifications/
06-EVIDENCE-GATED-ARCHITECTURE.md for the one ingestion surface
that exists today: POST /api/v1/webhooks/agriculture/intent.

The endpoint enforces, in order:
  1. Authentication — a shared secret (X-Webhook-Secret against
     AGTECH_WEBHOOK_SECRET). Unconfigured secret = the endpoint
     refuses everything (503): an unauthenticated intake that
     creates records is exactly what the governance spec exists
     to prevent.
  2. Idempotency — the Idempotency-Key header is required; a
     replay returns the original referral (200, replayed=true)
     instead of creating a duplicate.
  3. Validation — the payload is checked against the governance
     spec §3A shape (schema_version 1.0, an A/D/R track, the
     agtech_referral transaction type). provider_status is
     normalized to UNVERIFIED server-side: until commercial
     agreements are signed, every adapter is unverified (§4),
     whatever the payload claims.

And then it STOPS. The referral is recorded at INPUT_VALIDATED
with the next state pending. No provider is called, no spatial
assessment is run, no financing or auction step is taken. A
macro_driver of fiat_collapse is recorded as the
macroDistressExit flag — under the Iron Rule a macro signal
proposes; it never triggers.
"""
from __future__ import annotations

import os
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

import models
from agtech_workflow import transition_ag_referral
from db import get_session

router = APIRouter(prefix="/api/v1", tags=["agtech-webhooks"])

_TRACKS = {"A", "D", "R"}


class AgIntentWebhookIn(BaseModel):
    """The governance spec §3A payload (snake_case — it is the
    partner-facing shape) plus the routing fields the Paraguay
    directive names (country_code, macro_driver) and an optional
    GeoJSON polygon."""

    model_config = ConfigDict(extra="allow")

    schema_version: str
    track: str
    transaction_type: str
    crop_type: str | None = None
    production_purpose: str | None = None
    provider_preference: str | None = None
    provider_status: str | None = None
    requested_next_action: str | None = None
    consent_record_ids: list[str] = []
    outcome_status: str | None = None
    country_code: str | None = None
    macro_driver: str | None = None
    polygon: dict[str, Any] | None = None


def _view(referral: models.AgReferral, *, replayed: bool) -> dict:
    return {
        "id": referral.id,
        "state": referral.state.value,
        "nextState": models.AgReferralState.SPATIAL_ASSESSMENT_PENDING.value,
        "providerEligibility": "pending",
        "countryCode": referral.country_code.value if referral.country_code else None,
        "macroDistressExit": referral.macro_distress_exit,
        "replayed": replayed,
    }


@router.post("/webhooks/agriculture/intent", status_code=201)
def agriculture_intent_webhook(
    body: AgIntentWebhookIn,
    db: Session = Depends(get_session),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
):
    expected = os.environ.get("AGTECH_WEBHOOK_SECRET")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="webhook authentication is not configured",
        )
    if x_webhook_secret != expected:
        raise HTTPException(status_code=401, detail="invalid webhook secret")

    existing = (
        db.query(models.AgReferral)
        .filter(models.AgReferral.idempotency_key == idempotency_key)
        .first()
    )
    if existing is not None:
        return _view(existing, replayed=True)

    if body.schema_version != "1.0":
        raise HTTPException(
            status_code=422,
            detail=f"unsupported schema_version: {body.schema_version}",
        )
    if body.track not in _TRACKS:
        raise HTTPException(
            status_code=422,
            detail="track must be one of A, D, R for the evidence-gated ladder",
        )
    if body.transaction_type != "agtech_referral":
        raise HTTPException(
            status_code=422,
            detail="transaction_type must be agtech_referral on this endpoint",
        )
    if body.polygon is not None and body.polygon.get("type") != "Polygon":
        raise HTTPException(
            status_code=422, detail="polygon must be a GeoJSON Polygon"
        )
    country = None
    if body.country_code is not None:
        try:
            country = models.CountryCode(body.country_code)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"unknown country_code: {body.country_code}",
            )

    payload = body.model_dump(mode="json")
    # §4: adapters are UNVERIFIED until agreements are signed —
    # the payload does not get to claim otherwise.
    payload["provider_status"] = "UNVERIFIED"
    if not payload.get("outcome_status"):
        payload["outcome_status"] = "NOT_ASSESSED"

    referral = models.AgReferral(
        idempotency_key=idempotency_key,
        state=models.AgReferralState.INTENT_RECEIVED,
        payload=payload,
        country_code=country,
        macro_distress_exit=(
            True if body.macro_driver == "fiat_collapse" else None
        ),
        created_at=int(time.time()),
    )
    db.add(referral)
    db.flush()
    db.add(
        models.EventLog(
            aggregate_type="ag_referral",
            aggregate_id=referral.id,
            event_type="ag_referral.received",
            actor="agtech-webhook",
            payload={
                "state": models.AgReferralState.INTENT_RECEIVED.value,
                "track": body.track,
            },
        )
    )
    # The only state change the webhook itself may make: one
    # single step through the workflow guard, to INPUT_VALIDATED.
    transition_ag_referral(
        db,
        referral,
        models.AgReferralState.INPUT_VALIDATED,
        actor="agtech-webhook",
    )
    db.commit()
    db.refresh(referral)
    return _view(referral, replayed=False)
