"""Yield Matrix — subscription + preferred route (MOCK).

Built 2026-11-11 on the owner's own tap (Directive 5 of the
evening's scoped set). The Yield Matrix DATABASE TABLE and
its daily cron are the owner's Directive 4 — DEFERRED
post-demo by the owner. What ships tonight is the API shape
over a static, SYNTHETIC snapshot: every payload carries
synthetic: true, and no figure here is a measured yield —
the rows are placeholders with invented efficiency scores,
labelled as such wherever they surface.

Endpoints:
  POST /api/v1/matrix/subscribe        {email, phone_number?}
      Lead-gen capture for the "UZE Value Alert" — in-memory
      only in this mock; nothing is emailed or texted.
  GET  /api/v1/matrix/preferred-yield
      The snapshot's most capital-efficient inference route.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/matrix", tags=["matrix"])

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# SYNTHETIC SNAPSHOT — invented demo figures, not measured
# yields. Replaced by the real table when Directive 4 builds
# post-demo.
_SNAPSHOT: list[dict[str, Any]] = [
    {
        "protocol_name": "NEAR AI",
        "privacy_tier": "standard",
        "token_locked": "NEAR",
        "monthly_yield_usd": 0.0,
        "capital_efficiency": 0.92,
        "snapshot_date": "2026-11-11",
    },
    {
        "protocol_name": "Venice",
        "privacy_tier": "private-inference",
        "token_locked": "VVV",
        "monthly_yield_usd": 0.0,
        "capital_efficiency": 0.81,
        "snapshot_date": "2026-11-11",
    },
    {
        "protocol_name": "Arcium",
        "privacy_tier": "mpc-confidential",
        "token_locked": "ARX",
        "monthly_yield_usd": 0.0,
        "capital_efficiency": 0.77,
        "snapshot_date": "2026-11-11",
    },
    {
        "protocol_name": "Phala",
        "privacy_tier": "tee",
        "token_locked": "PHA",
        "monthly_yield_usd": 0.0,
        "capital_efficiency": 0.74,
        "snapshot_date": "2026-11-11",
    },
]

_subscribers: list[dict[str, Any]] = []


class SubscribeIn(BaseModel):
    email: str
    phone_number: str | None = None


@router.post("/subscribe")
def subscribe(body: SubscribeIn):
    email = (body.email or "").strip().lower()
    if not _EMAIL.match(email):
        raise HTTPException(status_code=422, detail="a valid email is required")
    record = {"email": email, "phone_number": body.phone_number, "mock": True}
    _subscribers.append(record)
    return {"subscribed": True, **record}


@router.get("/preferred-yield")
def preferred_yield():
    best = max(_SNAPSHOT, key=lambda r: r["capital_efficiency"])
    return {
        "preferred": best,
        "route": {
            "provider": best["protocol_name"],
            "privacy_tier": best["privacy_tier"],
            "reason": "highest capital_efficiency in the current snapshot",
        },
        "snapshot": _SNAPSHOT,
        "synthetic": True,
        "mock": True,
        "note": (
            "Synthetic demo snapshot. The Yield Matrix database and "
            "daily cron (Directive 4) are deferred post-demo by the "
            "owner; no figure here is a measured yield."
        ),
    }
