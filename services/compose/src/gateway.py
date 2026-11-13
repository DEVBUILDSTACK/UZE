"""Trace opt-in endpoint (owner tap, 2026-11-13).

POST /api/v1/gateway/traces/opt-in — a LABELLED MOCK. It
records that an account expressed a data-sharing intent,
using the four consent tiers verified from the NEAR AI
Gateway data policy (gateway.near.ai/your-data/):
debugging & evaluation are always on; benchmark generation,
ranking-model training, and model training are optional
opt-ins. The endpoint collects, moves, and shares NO traces
— there is no gateway integration behind it (see
docs/specifications/private-inference-gateway-proposal.md).
Storage follows the v1 pattern: append-only JSONL (env
GATEWAY_TRACE_OPTIN_PATH).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/gateway", tags=["gateway"])

OPTIONAL_TIERS: tuple[str, ...] = (
    "benchmark_generation",
    "ranking_model_training",
    "model_training",
)


class TraceOptIn(BaseModel):
    account: str = ""
    opt_in: bool | None = None
    tiers: list[str] = []


def _store_path() -> Path:
    return Path(
        os.environ.get(
            "GATEWAY_TRACE_OPTIN_PATH", "./data/gateway-trace-optins.jsonl"
        )
    )


def record_opt_in(record: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"record": record}) + "\n")


@router.post("/traces/opt-in")
def trace_opt_in(body: TraceOptIn):
    problems: list[str] = []
    if not body.account.strip():
        problems.append("account")
    if body.opt_in is None:
        problems.append("opt_in")
    bad_tiers = [t for t in body.tiers if t not in OPTIONAL_TIERS]
    if bad_tiers:
        problems.append("tiers")
    if problems:
        return JSONResponse(
            status_code=422,
            content={
                "error": "INSUFFICIENT_DATA",
                "missing_fields": problems,
            },
        )
    record = {
        "account": body.account.strip(),
        "opt_in": body.opt_in,
        # Always on per the source policy; not a choice the
        # caller makes.
        "always_on": ["debugging_evaluation"],
        "optional_tiers": list(body.tiers) if body.opt_in else [],
    }
    record_opt_in(record)
    return JSONResponse(
        content={
            "status": "mock_recorded",
            "mock": True,
            **record,
            "note": (
                "intent logged only — this endpoint collects, "
                "moves, and shares no traces; no gateway "
                "integration exists behind it"
            ),
        }
    )
