"""Pulse — the HIADR Content Desk data layer (Addendum A §4, B).

GET /api/v1/micro-regions/{id}/pulse returns the schema.org
Dataset payload the Content Desk publishes: in the post format of
Addendum B, a human-readable analysis up top and this JSON at the
bottom, carrying the agent action an AI crawler can act on.

Honesty rules, as everywhere in this build: the measured variables
are computed from the marketplace's own records — specs posted,
comparables recorded at settlement, settled volume summed from
the comparable payloads — never invented. `pulse_data` (the
period-aggregate layer the data pipeline will populate: prior
30d / 90d, 18m / 36m lookbacks) is served verbatim when present
and as null when it is not. The Content Desk bot that publishes
this payload is NOT built (directive: schema + docs first).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from db import get_session

router = APIRouter(prefix="/api/v1", tags=["pulse"])


@router.get("/micro-regions/{region_id}/pulse")
def micro_region_pulse(region_id: str, db: Session = Depends(get_session)):
    region = db.get(models.MicroRegion, region_id)
    if region is None:
        raise HTTPException(status_code=404, detail="micro-region not found")

    specs = (
        db.query(models.Intent).filter_by(micro_region_id=region.id).all()
    )
    comparables = (
        db.query(models.EventLog)
        .filter_by(
            aggregate_type="micro_region",
            aggregate_id=region.id,
            event_type="comparable.recorded",
        )
        .all()
    )
    settled_volume = sum(
        int((row.payload or {}).get("settledAmountUsdc") or 0)
        for row in comparables
    )

    stamps = [s.created_at for s in specs if s.created_at]
    if stamps:
        start = min(stamps)
        now = datetime.now(timezone.utc)
        temporal = f"{start:%Y-%m}/{now:%Y-%m}"
    else:
        temporal = None

    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": f"{region.label} Pulse",
        "temporalCoverage": temporal,
        "variableMeasured": {
            "spec_count": len(specs),
            "comparable_count": len(comparables),
            "settled_volume_usdc": settled_volume,
        },
        "pulse_data": region.pulse_data,
        "agent_action": "POST /api/v1/specs to initiate underwriting",
    }
