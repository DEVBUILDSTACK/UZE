"""Paid underwrite SKUs behind the x402 v2 flow
(owner-endorsed build, 2026-11-13).

POST /api/v1/underwrite/{sku} — the SKU surface from
docs/specifications/underwrite-sku-menu.md, gated by the
x402 module: no PAYMENT-SIGNATURE -> 402 with a
PAYMENT-REQUIRED header quoting the configured amount;
a validated (mock-profile) signature runs the real
multiyear engine and logs an EventLog row flagged as a
mock settlement. Served SKUs are the ones the multiyear
engine backs today (UZ-W-001 Full T-12, UZ-W-002
Multi-Year); every other SKU answers 422 SKU_NOT_SERVED
rather than pretending. Pricing is configuration-quoted
per request — unconfigured, the endpoint answers 503
PRICING_NOT_CONFIGURED (no static prices, per the owner's
2026-11-12 ruling).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
import research
import x402
from db import get_session
from email_gateway import analyze_multiyear

router = APIRouter(prefix="/api/v1/underwrite", tags=["underwrite-sku"])

SERVED_SKUS: dict[str, str] = {
    "UZ-W-001": "UZE Underwrite — Full T-12",
    "UZ-W-002": "UZE Underwrite — Multi-Year",
}


class SkuIngest(BaseModel):
    years: list[dict]
    context: dict | None = None
    context_run_id: str | None = None
    # Optional comp-set benchmarking inputs (D5 directive,
    # 2026-11-13), passed through to analyze_multiyear.
    subject_profile: dict | None = None
    comps: list[dict] | None = None
    comp_threshold_pct: float | None = None


@router.post("/{sku}")
def underwrite_sku(
    sku: str,
    body: SkuIngest,
    request: Request,
    session: Session = Depends(get_session),
):
    if sku not in SERVED_SKUS:
        return JSONResponse(
            status_code=422,
            content={
                "error": "SKU_NOT_SERVED",
                "served_skus": sorted(SERVED_SKUS),
            },
        )
    if not body.years:
        return JSONResponse(
            status_code=422,
            content={
                "error": "INSUFFICIENT_DATA",
                "missing_fields": ["years"],
            },
        )
    config = x402.pricing_config()
    if config is None:
        return JSONResponse(
            status_code=503,
            content={
                "error": "PRICING_NOT_CONFIGURED",
                "mock": True,
                "note": (
                    "amounts are quoted per request from "
                    "UZEguidance market pricing; no static "
                    "price is posted and none is invented here"
                ),
            },
        )
    resource_url = f"/api/v1/underwrite/{sku}"
    required = x402.build_payment_required(
        resource_url, SERVED_SKUS[sku], config
    )
    header_value = request.headers.get("payment-signature")
    if not header_value:
        return JSONResponse(
            status_code=402,
            content=required,
            headers={"PAYMENT-REQUIRED": x402.encode_header(required)},
        )
    ok, reason, auth = x402.validate_payment_signature(
        header_value, config
    )
    if not ok:
        content = dict(required)
        content["error"] = f"invalid PAYMENT-SIGNATURE: {reason}"
        return JSONResponse(
            status_code=402,
            content=content,
            headers={"PAYMENT-REQUIRED": x402.encode_header(required)},
        )
    research_context = None
    if body.context_run_id:
        # Composition by run ID (explainer section 7): a run
        # may be referenced as this request's context only by
        # the identity that owns it. The referenced run's
        # sources are cited on the result; the years in this
        # request remain the underwrite's input.
        found = research.find_run(session, body.context_run_id)
        if found is None:
            return JSONResponse(
                status_code=422,
                content={
                    "error": "RUN_NOT_FOUND",
                    "run_id": body.context_run_id,
                },
            )
        run_payload, run_actor = found
        if run_actor != auth["payer"]:
            return JSONResponse(
                status_code=422,
                content={
                    "error": "COMPOSITION_IDENTITY_MISMATCH",
                    "note": (
                        "a run may only be referenced by the "
                        "identity that owns it"
                    ),
                },
            )
        stored = run_payload.get("result") or {}
        research_context = {
            "run_id": body.context_run_id,
            "kind": run_payload.get("kind"),
            "sources": [
                {"title": r.get("title"), "url": r.get("url")}
                for r in stored.get("results", [])
            ],
        }
    try:
        result = analyze_multiyear(
            body.years,
            body.context,
            subject_profile=body.subject_profile,
            comps=body.comps,
            comp_threshold_pct=body.comp_threshold_pct,
        )
    except ValueError as exc:
        return JSONResponse(status_code=422, content={"error": str(exc)})
    if research_context is not None:
        result["research_context"] = research_context
    # Logged as a MOCK settlement in the append-only audit
    # trail — flagged mock:true, moves no funds, exactly the
    # metering.mock_transfer convention.
    session.add(
        models.EventLog(
            aggregate_type="underwrite_sku",
            aggregate_id=sku,
            event_type="x402.mock_settlement",
            actor=auth["payer"],
            payload={
                "mock": True,
                "scheme": auth["scheme"],
                "network": auth["network"],
                "asset": auth["asset"],
                "amountAtomic": auth["amount"],
                "payer": auth["payer"],
                "payTo": auth["payTo"],
                "resource": resource_url,
                "composed_from": body.context_run_id,
            },
        )
    )
    session.commit()
    receipt = {
        "success": True,
        "mock": True,
        "network": auth["network"],
        "transaction": "mock:" + auth["signature"].removeprefix("mock:")[:16],
        "payer": auth["payer"],
    }
    return JSONResponse(
        content={"sku": sku, "payment": receipt, "result": result},
        headers={"PAYMENT-RESPONSE": x402.encode_header(receipt)},
    )
