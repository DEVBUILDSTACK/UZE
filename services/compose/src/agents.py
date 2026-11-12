"""Headless agent surface — GIRA & SURA underwriting endpoints.

The M2M half of the dual-surface architecture (composite directive,
2026-11-08):

  POST /api/v1/agents/gira/underwrite  {polygonId}
      GIRA — the A/D/R agent. Assesses a polygon from the LIVE
      ProviderSnapshot cache (approved partner data only; staged
      PENDING payloads are counted but never consumed).
  POST /api/v1/agents/sura/underwrite  {specId}
      SURA — the HiCRE agent. Assesses a marketplace spec (Intent)
      from the compose market state.

Both return structured JSON assessments — not chat. Both are gated
the same way as the metered surface (src/metering.py, Sprint 1.5):

  - x401 identity: an X-IDENTITY header judged by the identity stub
    verifier. Missing/invalid -> 401. (The stub is swapped for the
    Assurative trust-layer verification in Sprint 2 — the same swap
    the metered surface awaits.)
  - x402 metering: an X-PAYMENT header carrying a mock
    authorization. Missing/invalid -> 402 with the x402
    requirements. The tariff is the Sprint 1.5 mock tariff and no
    funds move; the call is logged as a mock metering event.

Assessments are deterministic and computed from real records —
partner payloads in the live cache and market state in compose.
No LLM is consulted (attested inference is a separate, metered
call; see src/inference.py).
"""
from __future__ import annotations

import copy
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import metering
import models
import partners as partners_module
import treasury_router
from db import get_session

router = APIRouter(prefix="/api/v1/agents")


def _gate(request: Request, resource: str):
    """x401 then x402, in that order.

    Returns (identity, None) when both gates pass, or
    (None, response) with the 401/402 challenge to send back —
    the 402 body is the x402 requirements document, exactly as the
    metered surface issues it."""
    identity_header = request.headers.get("X-IDENTITY")
    if not identity_header:
        return None, JSONResponse(
            status_code=401,
            content={"error": "X-IDENTITY header is required (x401)", "mock": True},
        )
    ok, identity = metering.verify_identity_payload(
        metering._decode_header(identity_header)
    )
    if not ok:
        return None, JSONResponse(
            status_code=401,
            content={"error": identity.get("error", "identity verification failed"), "mock": True},
        )

    payment_header = request.headers.get("X-PAYMENT")
    if not payment_header:
        return None, JSONResponse(
            status_code=402, content=metering.payment_requirements(resource)
        )
    valid, reason, _auth = metering.validate_mock_authorization(payment_header)
    if not valid:
        content = metering.payment_requirements(resource)
        content["error"] = f"invalid X-PAYMENT authorization: {reason}"
        return None, JSONResponse(status_code=402, content=content)
    return identity, None


def _snapshots_for_polygon(db: Session, polygon_id: str, model) -> list:
    return (
        db.query(model)
        .filter(model.raw_payload["polygon_id"].as_string() == polygon_id)
        .all()
    )


def _gira_guidance(snapshots: list) -> list[str]:
    """Deterministic explanations derived from the ingested payloads
    themselves — the same data GIRA's human surface narrates."""
    lines: list[str] = []
    for snap in snapshots:
        payload = snap.raw_payload or {}
        if snap.partner_id == "AGRO_DIGITAL":
            soil = payload.get("soil_profile") or {}
            crop = payload.get("crop_suitability") or {}
            if soil:
                lines.append(
                    "Agro Digital soil chemistry: pH "
                    f"{soil.get('ph_level')}, nitrogen {soil.get('nitrogen_ppm')} ppm, "
                    f"phosphorus {soil.get('phosphorus_ppm')} ppm, potassium "
                    f"{soil.get('potassium_ppm')} ppm, organic matter "
                    f"{soil.get('organic_matter_pct')}%."
                )
            if crop:
                lines.append(
                    f"Crop suitability: {crop.get('crop_type')} at "
                    f"{crop.get('yield_potential_tons_per_ha')} t/ha potential, "
                    f"ZARC risk {crop.get('zarc_risk_score')}."
                )
        elif snap.partner_id == "BDCS":
            feed = payload.get("feedlot_context") or {}
            if feed:
                lines.append(
                    f"BDCS feedlot: {feed.get('cattle_head_count')} head on "
                    f"{feed.get('feed_type')}, target slaughter "
                    f"{feed.get('target_slaughter_weight_kg')} kg, feed "
                    f"optimization index {feed.get('feed_optimization_index')}."
                )
        elif snap.partner_id == "EFFATHA":
            agro = payload.get("agrotechnical_context") or {}
            if agro:
                lines.append(
                    f"Effatha treatment: {agro.get('delivery_mechanism')} "
                    f"protocol {agro.get('treatment_protocol_id')} for "
                    f"{agro.get('target_crop')}, activation "
                    f"{agro.get('activation_date')}."
                )
    return lines


@router.post("/gira/underwrite")
async def gira_underwrite(
    request: Request,
    db: Session = Depends(get_session),
):
    try:
        body = await request.json()
    except Exception:
        body = {}
    polygon_id = (body or {}).get("polygonId")
    if not polygon_id:
        raise HTTPException(status_code=422, detail="polygonId is required")
    identity, challenge = _gate(request, polygon_id)
    if challenge is not None:
        return challenge

    # Autonomous treasury (2026-11-11 override): before the task
    # executes, check GIRA's NEAR compute balance; if it is below
    # the inference threshold the engine swaps into NEAR itself
    # (mock execution — see treasury_router) and the swap lands
    # in the EventLog with this handler's commit.
    treasury = treasury_router.ensure_compute_funded(db, "GIRA")

    live = _snapshots_for_polygon(db, polygon_id, models.ProviderSnapshot)
    staged = _snapshots_for_polygon(db, polygon_id, models.StagingProviderSnapshot)
    pending = [s for s in staged if s.approval_status == "PENDING"]

    sources = [
        {
            "partnerId": s.partner_id,
            "dataCategory": s.data_category,
            "providerStatus": s.provider_status,
            "fetchedAt": s.fetched_at,
        }
        for s in live
    ]
    assessment = {
        "status": "READY" if live else "INSUFFICIENT_DATA",
        "liveSnapshots": len(live),
        "pendingStaging": len(pending),
        "sources": sources,
        "guidance": _gira_guidance(live),
    }
    db.add(
        models.EventLog(
            aggregate_type="polygon",
            aggregate_id=polygon_id,
            event_type="agent.underwrite",
            actor="agent:GIRA",
            payload={
                "status": assessment["status"],
                "liveSnapshots": len(live),
                "identitySubject": identity.get("subject"),
                "metering": "mock-x402",
            },
        )
    )
    db.commit()
    return JSONResponse(
        content={
            "agent": "GIRA",
            "surface": "headless",
            "tracks": ["A", "D", "R"],
            "polygonId": polygon_id,
            "identity": {"subject": identity.get("subject"), "verified": True, "mock": True},
            "metering": {"scheme": "mock-exact", "mock": True},
            "treasury": treasury,
            "assessment": assessment,
        }
    )


# SURA's institutional analysis directive (2026-11-11, owner's
# tap). This is the instruction set the underwriting analysis
# follows — carried in code so the demo surface, the email
# gateway, and any future model-backed path all read the same
# words. (juror.py is a different instrument — the Assuraties
# claim judge — and is deliberately NOT edited for this.)
SURA_ANALYSIS_DIRECTIVE = (
    "You are an institutional real estate financial analyst. "
    "Analyze the provided multi-year T-12s, normalized through "
    "the Standard Chart of Accounts into the seven-bucket P&L "
    "(Revenue / Operating Expenses / Taxes / Insurance(s) / "
    "Interest Expense/Income / Miscellaneous Net / Profit) — "
    "operating expenses never absorb taxes, insurance, or "
    "interest. Calculate historical NOI growth across the "
    "years provided. Evaluate the asking price using Cap Rate, "
    "Price per Unit, and Price per Square Foot against the "
    "provided micro-region sales comps. Highlight any anomalous "
    "line items or unexplained expense fluctuations (any bucket "
    "moving more than 15% year-over-year is flagged). Judge "
    "only against same-micro-region benchmarks. Work in three "
    "tiers: (1) historicals — multi-year T-12s normalized into "
    "the seven buckets, unlevered NOI, year-over-year bucket "
    "trends stated plainly; (2) projections — a 12-month "
    "forward NOI whose every growth assumption and known shock "
    "is labelled by source, projected NOI reported separately "
    "from projected levered cash flow; (3) verification — when "
    "actuals arrive, score the projection's variance against "
    "them and treat a miss beyond the threshold as a "
    "methodology flag, not a rounding error. Value on verified "
    "unlevered NOI only — levered cash flow is never a "
    "valuation basis."
)


@router.post("/sura/underwrite")
async def sura_underwrite(
    request: Request,
    db: Session = Depends(get_session),
):
    try:
        body = await request.json()
    except Exception:
        body = {}
    spec_id = (body or {}).get("specId")
    if not spec_id:
        raise HTTPException(status_code=422, detail="specId is required")
    identity, challenge = _gate(request, spec_id)
    if challenge is not None:
        return challenge

    intent = db.get(models.Intent, spec_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="spec not found")

    # Autonomous treasury (2026-11-11 override): same pre-task
    # compute check for SURA as for GIRA (see above) — after the
    # spec resolves, before the assessment executes.
    treasury = treasury_router.ensure_compute_funded(db, "SURA")

    bids = db.query(models.Bid).filter(models.Bid.intent_id == spec_id).all()
    amounts = [b.amount_usdc for b in bids if b.amount_usdc is not None]
    in_budget = [
        a for a in amounts
        if intent.budget_min_usdc <= a <= intent.budget_max_usdc
    ]
    status_value = intent.status.value if hasattr(intent.status, "value") else intent.status
    assessment = {
        "analysisDirective": SURA_ANALYSIS_DIRECTIVE,
        "status": status_value,
        "assetSubclass": intent.asset_subclass.value if intent.asset_subclass else None,
        "microRegionId": intent.micro_region_id,
        "budgetMinUsdc": intent.budget_min_usdc,
        "budgetMaxUsdc": intent.budget_max_usdc,
        "bidCount": len(bids),
        "bidsInBudget": len(in_budget),
        "lowestBidUsdc": min(amounts) if amounts else None,
        "entityId": intent.entity_id,
        "guidance": [
            f"Spec is {status_value} in {intent.micro_region_id} with "
            f"{len(bids)} bid(s); {len(in_budget)} inside the "
            f"{intent.budget_min_usdc}–{intent.budget_max_usdc} USDC budget band."
        ],
    }
    db.add(
        models.EventLog(
            aggregate_type="intent",
            aggregate_id=spec_id,
            event_type="agent.underwrite",
            actor="agent:SURA",
            payload={
                "status": assessment["status"],
                "bidCount": len(bids),
                "identitySubject": identity.get("subject"),
                "metering": "mock-x402",
            },
        )
    )
    db.commit()
    return JSONResponse(
        content={
            "agent": "SURA",
            "surface": "headless",
            "tracks": ["H", "I"],
            "specId": spec_id,
            "identity": {"subject": identity.get("subject"), "verified": True, "mock": True},
            "metering": {"scheme": "mock-exact", "mock": True},
            "treasury": treasury,
            "assessment": assessment,
        }
    )


# ---------------------------------------------------------------------
# GIRA debug — the agentic debugging surface. A partner pastes a
# payload that failed validation; GIRA returns the structured errors
# and, where a deterministic fix exists, the corrected payload:
# numeric values sent as strings are coerced, a top-level
# zarc_risk_score is nested into crop_suitability, and keys the
# schema does not define are dropped (each fix is reported).
# Anything that cannot be fixed deterministically is returned in
# remainingErrors with the field path — never guessed at.
# ---------------------------------------------------------------------

_NUMERIC_PATHS: dict[str, list[tuple[str, str]]] = {
    "AGRO_DIGITAL": [
        ("soil_profile", "ph_level"),
        ("soil_profile", "nitrogen_ppm"),
        ("soil_profile", "phosphorus_ppm"),
        ("soil_profile", "potassium_ppm"),
        ("soil_profile", "organic_matter_pct"),
        ("crop_suitability", "yield_potential_tons_per_ha"),
    ],
    "BDCS": [
        ("feedlot_context", "cattle_head_count"),
        ("feedlot_context", "target_slaughter_weight_kg"),
        ("feedlot_context", "current_avg_weight_kg"),
        ("feedlot_context", "feed_optimization_index"),
    ],
    "EFFATHA": [
        ("agrotechnical_context", "application_rate_liters_per_ha"),
    ],
}

_TOP_LEVEL_KEYS: dict[str, set[str]] = {
    "AGRO_DIGITAL": {
        "partner_id", "polygon_id", "geojson_polygon",
        "soil_profile", "crop_suitability", "attestation",
    },
    "BDCS": {
        "partner_id", "polygon_id", "geojson_polygon",
        "feedlot_context", "attestation",
    },
    "EFFATHA": {
        "partner_id", "polygon_id", "geojson_polygon",
        "agrotechnical_context", "attestation",
    },
}


def debug_payload(partner_id: str, payload: dict) -> dict:
    errors_before = partners_module.schema_errors(partner_id, payload)
    corrected = copy.deepcopy(payload)
    fixes: list[str] = []

    for parent, field in _NUMERIC_PATHS.get(partner_id, []):
        node = corrected.get(parent)
        if isinstance(node, dict) and isinstance(node.get(field), str):
            raw = node[field].strip()
            try:
                value = float(raw)
            except ValueError:
                continue
            node[field] = int(value) if value.is_integer() else value
            fixes.append(
                f"{parent}.{field}: coerced string \"{raw}\" to number {node[field]}"
            )

    if partner_id == "AGRO_DIGITAL" and "zarc_risk_score" in corrected:
        crop = corrected.setdefault("crop_suitability", {})
        if isinstance(crop, dict) and "zarc_risk_score" not in crop:
            crop["zarc_risk_score"] = corrected.pop("zarc_risk_score")
            fixes.append(
                "zarc_risk_score: moved from the top level into crop_suitability"
            )

    allowed = _TOP_LEVEL_KEYS.get(partner_id, set())
    for key in sorted(set(corrected) - allowed - {"partner_id"}):
        corrected.pop(key, None)
        fixes.append(f"{key}: removed (not defined in the {partner_id} schema)")

    remaining = partners_module.schema_errors(partner_id, corrected)
    return {
        "agent": "GIRA",
        "partnerId": partner_id,
        "validBefore": not errors_before,
        "validAfter": not remaining,
        "errors": errors_before,
        "fixes": fixes,
        "correctedPayload": corrected if fixes else None,
        "remainingErrors": remaining,
    }


@router.post("/gira/debug")
async def gira_debug(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    payload = (body or {}).get("payload")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="payload must be a JSON object")
    partner_id = (body or {}).get("partnerId") or payload.get("partner_id")
    if partner_id not in partners_module.SCHEMA_FILES:
        raise HTTPException(status_code=400, detail=f"unknown partner: {partner_id}")
    return JSONResponse(content=debug_payload(partner_id, payload))
