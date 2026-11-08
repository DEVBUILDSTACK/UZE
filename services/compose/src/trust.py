"""Assurative V2 trust-layer client (UZEmarkets side).

Compose consumes the trust layer over HTTP — separate service,
separate database (Scope Tenet 01); the only things that cross
the boundary are the string references the Intent carries.

Configuration: ASSURATIVE_API_URL (e.g. http://127.0.0.1:8200).
When it is unset, or the trust layer is unreachable, or the
account is unbound, resolution returns None and the marketplace
proceeds on what the client posted — the trust layer enriches
identity, it never blocks the transaction layer. Outcomes are
never fabricated: a resolved entity is one the trust layer
actually returned.

httpx is constructed with trust_env=False: this deployment's
proxy environment breaks httpx's env parsing (bracketed IPv6
no_proxy entries) and the trust call is a direct service call.
"""
from __future__ import annotations

import os
from typing import Any

import httpx


def _base_url() -> str | None:
    return os.environ.get("ASSURATIVE_API_URL") or None


def resolve_account(near_account: str | None) -> dict[str, Any] | None:
    """GET /api/v1/trust/resolve/{near_account} -> normalized
    {entityId, affiliateId, scopes, agent} or None."""
    base = _base_url()
    if not base or not near_account:
        return None
    try:
        with httpx.Client(base_url=base, timeout=5.0, trust_env=False) as client:
            response = client.get(f"/api/v1/trust/resolve/{near_account}")
        if response.status_code != 200:
            return None
        data = response.json().get("data") or {}
    except Exception:
        return None
    if not data.get("entity_id"):
        return None
    return {
        "entityId": data["entity_id"],
        "affiliateId": data.get("affiliate_id"),
        "scopes": data.get("scopes") or [],
        "agent": bool(data.get("agent")),
    }


def verify_x401(near_account: str, message: str, signature_b64: str) -> dict[str, Any] | None:
    """POST /api/v1/trust/verify-x401 -> the trust layer's verdict
    {verified, reason, entityId, scopes} or None when the trust
    layer is not configured/reachable. None means 'not evaluated'
    — callers must not treat it as verified."""
    base = _base_url()
    if not base:
        return None
    try:
        with httpx.Client(base_url=base, timeout=10.0, trust_env=False) as client:
            response = client.post(
                "/api/v1/trust/verify-x401",
                json={
                    "near_account": near_account,
                    "message": message,
                    "signature": signature_b64,
                },
            )
        if response.status_code != 200:
            return None
        data = response.json().get("data") or {}
    except Exception:
        return None
    return {
        "verified": bool(data.get("verified")),
        "reason": data.get("reason"),
        "entityId": data.get("entity_id"),
        "scopes": data.get("scopes") or [],
    }
