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
    result = analyze_multiyear(body.years, body.context)
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
