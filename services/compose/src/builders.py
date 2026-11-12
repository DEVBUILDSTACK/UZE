"""UZE Builders — low-friction agent onboarding (MOCK).

Built 2026-11-11 on the owner's own tap (Directive 2 of the
evening's scoped set: D1/D2/D3/D5/D7/D8 as mocks; DB migration
and the Yield Matrix cron deferred post-demo by the owner).

The low-friction lane of the Two Lanes of Capital: an
autonomous agent registers as a UZE Builder with ONLY an
email and an x401 wallet address. No KYB at this lane — the
three-tier gate in metering.py is what keeps a Builder inside
Tier-1/Tier-2 amounts; anything Tier 3 routes through an
Entity with full KYB.

MOCK SCOPE: the registry is in-memory, like the escrow pools
in contributions.py. No database table (the owner's D6
migration is deferred post-demo), no email is sent, no wallet
is verified beyond shape. The welcome copy is the ratified
opaque-credit copy: it never names the credit source.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/treasury", tags=["builders"])

WELCOME_COPY = (
    "Welcome to UZE Builders. Your account is active. "
    "Workflows will render Compute Credits when available "
    "based on network capacity."
)

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_builders: dict[str, dict[str, Any]] = {}
_by_email: dict[str, str] = {}


class BuilderRegisterIn(BaseModel):
    email: str
    x401_wallet_address: str


def _builder_id(email: str) -> str:
    return "uze-builder-" + hashlib.sha256(email.encode()).hexdigest()[:12]


@router.post("/sub-builder/register")
def register_builder(body: BuilderRegisterIn):
    email = (body.email or "").strip().lower()
    wallet = (body.x401_wallet_address or "").strip()
    if not _EMAIL.match(email):
        raise HTTPException(status_code=422, detail="a valid email is required")
    if len(wallet) < 8:
        raise HTTPException(
            status_code=422, detail="an x401 wallet address is required"
        )
    if email in _by_email:
        record = _builders[_by_email[email]]
        return {**record, "existing": True}
    record = {
        "builder_id": _builder_id(email),
        "email": email,
        "x401_wallet_address": wallet,
        "entity_id": None,
        "lane": "UZE_BUILDER",
        "status": "active",
        "kyb_required": False,
        "welcome": WELCOME_COPY,
        "mock": True,
    }
    _builders[record["builder_id"]] = record
    _by_email[email] = record["builder_id"]
    return {**record, "existing": False}


@router.get("/sub-builder/{builder_id}")
def get_builder(builder_id: str):
    record = _builders.get(builder_id)
    if record is None:
        raise HTTPException(status_code=404, detail="builder not found")
    return record
