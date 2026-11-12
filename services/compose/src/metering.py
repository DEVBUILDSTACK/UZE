"""Metering — the Sprint 1.5 Day 5 x402 / x401 mock flow (stretch day).

Filed flow (02-SPRINT-1.5-PLAN.md Day 5; Diagram 4 note: in the full
design x401/x402 fire during SETTLING — that is Sprint 2; here they
are stubbed against the inference call, which is the metered resource
the hackathon demo actually exercises):

  x402  POST /api/v1/metered/analyze {specId}
        - no X-PAYMENT header -> HTTP 402 with payment requirements
          (x402-shaped body; scheme "mock-exact"; network
          solana-devnet; asset = the devnet USDC mint; fixed mock
          tariff). Nothing runs, nothing is charged.
        - X-PAYMENT header carrying a mock authorization (base64
          JSON) -> validated for scheme, network, asset and amount;
          the mock transfer is LOGGED as an EventLog row
          (metering.mock_transfer) whose payload is flagged
          mock: true — it is not a settlement, moves no funds, and
          never touches the Diagram 4 settlement states. The call
          then proceeds.

  x401  identity for tier C+ engagements (IntentTier C, D, E):
        - after payment validates, a C+ spec without an X-IDENTITY
          header -> HTTP 401 with an identity challenge body.
        - POST /api/v1/identity/verify is the stub verifier: a
          payload with subject + credentialType + attestation
          returns the verified credential shape; anything missing
          returns 401 with what is required. The X-IDENTITY header
          carries the same payload (base64 JSON) and is judged by
          the same function.

  After both gates the endpoint runs inference.analyze_property on
  the spec and returns its honest outcome (ok | unavailable |
  error). Without NEARAI_API_KEY that is "unavailable" — the
  metering flow is what Day 5 proves, not the model call.

Everything in this module is a protocol-shape mock for the demo,
and everything it emits says so (mock flags, the "mock:" signature
prefix, the mock_transfer event name). Real x402 facilitation (the
PayAI / Coinbase CDP decision has been held since Oct 19) and real
identity verification (Intent Gateway / Tag Registry) are Sprint 2.
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

import chain_sig
import inference
import models
import settlement
from db import get_session
from intents import _spec_view

router = APIRouter(prefix="/api/v1", tags=["metering"])

# The Sprint 1.5 mock tariff for one property analysis: 0.10 USDC.
# A placeholder price for the protocol flow; the real tariff is a
# Sprint 2 decision (tier A/B metering details are an open item).
MOCK_PRICE_BASE_UNITS = 100_000
MOCK_NETWORK = "solana-devnet"
MOCK_SCHEME = "mock-exact"
TIER_C_PLUS = {models.IntentTier.C, models.IntentTier.D, models.IntentTier.E}


def _pay_to() -> str:
    address, _ = chain_sig.derive_address(settlement.OPERATOR_ACCOUNT)
    return address


def payment_requirements(spec_id: str) -> dict[str, Any]:
    return {
        "x402Version": 1,
        "mock": True,
        "error": "X-PAYMENT header is required",
        "accepts": [
            {
                "scheme": MOCK_SCHEME,
                "network": MOCK_NETWORK,
                "maxAmountRequired": str(MOCK_PRICE_BASE_UNITS),
                "asset": settlement.USDC_MINT_DEVNET,
                "payTo": _pay_to(),
                "resource": f"/api/v1/metered/analyze",
                "description": (
                    "UZEMARKETS metered property analysis (Sprint 1.5 "
                    "mock tariff — no funds move)"
                ),
                "mimeType": "application/json",
                "extra": {"specId": spec_id},
            }
        ],
    }


def _canonical(auth: dict[str, Any]) -> str:
    return json.dumps(
        {k: auth[k] for k in ("scheme", "network", "asset", "amount", "payer", "nonce")},
        sort_keys=True,
        separators=(",", ":"),
    )


def mock_signature(auth: dict[str, Any]) -> str:
    """Deterministic mock signature. The "mock:" prefix is the point:
    this proves the retry carried a well-formed authorization, and it
    can never be mistaken for a cryptographic payment signature."""
    return "mock:" + hashlib.sha256(_canonical(auth).encode()).hexdigest()


def build_mock_authorization(payer: str, amount: int = MOCK_PRICE_BASE_UNITS) -> str:
    """The agent side of the mock: build the X-PAYMENT header value."""
    auth: dict[str, Any] = {
        "scheme": MOCK_SCHEME,
        "network": MOCK_NETWORK,
        "asset": settlement.USDC_MINT_DEVNET,
        "amount": amount,
        "payer": payer,
        "nonce": f"{int(time.time())}-{payer}",
    }
    auth["signature"] = mock_signature(auth)
    return base64.urlsafe_b64encode(json.dumps(auth).encode()).decode()


def _decode_header(value: str) -> dict[str, Any] | None:
    try:
        return json.loads(base64.urlsafe_b64decode(value.encode()))
    except Exception:
        return None


def validate_mock_authorization(value: str) -> tuple[bool, str, dict[str, Any] | None]:
    auth = _decode_header(value)
    if auth is None:
        return False, "authorization is not base64 JSON", None
    if auth.get("scheme") != MOCK_SCHEME:
        return False, f"scheme must be {MOCK_SCHEME}", None
    if auth.get("network") != MOCK_NETWORK:
        return False, f"network must be {MOCK_NETWORK}", None
    if auth.get("asset") != settlement.USDC_MINT_DEVNET:
        return False, "asset must be the devnet USDC mint", None
    if not isinstance(auth.get("amount"), int) or auth["amount"] < MOCK_PRICE_BASE_UNITS:
        return False, f"amount must be >= {MOCK_PRICE_BASE_UNITS} base units", None
    if auth.get("signature") != mock_signature(auth):
        return False, "mock signature does not verify", None
    return True, "", auth


def verify_identity_payload(payload: Any) -> tuple[bool, dict[str, Any]]:
    """The x401 stub verifier — one function judging both the
    /identity/verify body and the X-IDENTITY header."""
    required = ["subject", "credentialType", "attestation"]
    if not isinstance(payload, dict) or any(not payload.get(k) for k in required):
        return False, {
            "error": "identity verification required for tier C+ engagements",
            "mock": True,
            "required": required,
        }
    return True, {
        "verified": True,
        "mock": True,
        "subject": payload["subject"],
        "tier": "C+",
        "credential": {
            "type": payload["credentialType"],
            "subject": payload["subject"],
            "issuer": "uzemarkets-identity-stub",
            "verifiedAt": int(time.time()),
        },
    }


class AnalyzeIn(BaseModel):
    specId: str


class IdentityIn(BaseModel):
    subject: str | None = None
    credentialType: str | None = None
    attestation: str | None = None


@router.post("/identity/verify")
def identity_verify(body: IdentityIn):
    ok, result = verify_identity_payload(body.model_dump())
    if not ok:
        return JSONResponse(status_code=401, content=result)
    return result


@router.post("/metered/analyze")
def metered_analyze(
    body: AnalyzeIn, request: Request, session: Session = Depends(get_session)
):
    intent = session.get(models.Intent, body.specId)
    if intent is None:
        return JSONResponse(
            status_code=404, content={"detail": f"spec {body.specId} not found"}
        )

    # Gate 1 — x402 payment (mock).
    payment_header = request.headers.get("x-payment")
    if not payment_header:
        return JSONResponse(
            status_code=402, content=payment_requirements(str(intent.id))
        )
    ok, reason, auth = validate_mock_authorization(payment_header)
    if not ok:
        content = payment_requirements(str(intent.id))
        content["error"] = f"invalid X-PAYMENT authorization: {reason}"
        return JSONResponse(status_code=402, content=content)

    # The mock transfer is logged — as a mock, in the append-only
    # audit trail, never as a settlement.
    event = models.EventLog(
        aggregate_type="intent",
        aggregate_id=str(intent.id),
        event_type="metering.mock_transfer",
        actor=auth["payer"],
        payload={
            "mock": True,
            "scheme": MOCK_SCHEME,
            "network": MOCK_NETWORK,
            "asset": settlement.USDC_MINT_DEVNET,
            "amountBaseUnits": auth["amount"],
            "payer": auth["payer"],
            "payTo": _pay_to(),
            "resource": "/api/v1/metered/analyze",
        },
    )
    session.add(event)
    session.commit()

    # Gate 2 — x401 identity, tier C+ engagements only.
    identity_result: dict[str, Any] | None = None
    if intent.tier in TIER_C_PLUS:
        identity_header = request.headers.get("x-identity")
        payload = _decode_header(identity_header) if identity_header else None
        ok, identity_result = verify_identity_payload(payload)
        if not ok:
            return JSONResponse(status_code=401, content=identity_result)

    # Both gates passed — the metered call proceeds.
    analysis = inference.analyze_property(_spec_view(intent).model_dump())
    return {
        "specId": str(intent.id),
        "payment": {
            "status": "mock_settled",
            "mock": True,
            "amountBaseUnits": auth["amount"],
            "eventLogId": event.id,
        },
        "identity": identity_result,
        "inference": analysis,
    }


def build_mock_identity(subject: str) -> str:
    """The agent side of the x401 stub: build the X-IDENTITY header."""
    payload = {
        "subject": subject,
        "credentialType": "near-account-attestation",
        "attestation": "mock-attested",
    }
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def call_metered_analyze(client, spec_id: str, payer: str) -> Any:
    """The filed Day 5 agent flow: attempt -> 402 -> sign the mock
    authorization -> retry -> (C+ only) 401 -> present identity ->
    retry -> proceeds. Returns the final response."""
    resp = client.post("/api/v1/metered/analyze", json={"specId": spec_id})
    if resp.status_code == 402:
        resp = client.post(
            "/api/v1/metered/analyze",
            json={"specId": spec_id},
            headers={"X-PAYMENT": build_mock_authorization(payer)},
        )
    if resp.status_code == 401:
        resp = client.post(
            "/api/v1/metered/analyze",
            json={"specId": spec_id},
            headers={
                "X-PAYMENT": build_mock_authorization(payer),
                "X-IDENTITY": build_mock_identity(payer),
            },
        )
    return resp


# ------------------------------------------------------------------
# Three-tier amount compliance (owner's tap, 2026-11-11 ~19:31 ET —
# the Directive-1 family, built as a protocol-shape mock in the
# same discipline as the rest of this module).
#
#   Tier 1  amount <  $30.00   x402 payment only. No x401, no KYB.
#   Tier 2  $30.00 – $199.99   x402 + x401 identity, and the
#                              identity must be tied to an Entity
#                              (entityId on the credential).
#   Tier 3  amount >= $200.00  x402 + x401 + full Entity KYB.
#
# Boundaries are exact: $29.999 is the largest Tier-1 amount at
# three-decimal precision; $30.00 opens Tier 2; $199.99 is the
# largest Tier-2 amount; $200.00 opens Tier 3. Identity here is
# Proof's x401 shape judged by this module's stub verifier —
# identity verification does NOT route through Circle or Arc
# (research note 18: Arc is settlement-side only). Enforcement
# failures: Tier 2 -> HTTP 401, Tier 3 -> HTTP 403, per spec.
# ------------------------------------------------------------------

TIER2_MIN_USD = 30.00
TIER3_MIN_USD = 200.00


def classify_amount_tier(amount_usd: float) -> int:
    """1 / 2 / 3 by the exact ratified boundaries."""
    if amount_usd < TIER2_MIN_USD:
        return 1
    if amount_usd < TIER3_MIN_USD:
        return 2
    return 3


def enforce_amount_tier(
    amount_usd: float,
    identity_payload: Any = None,
    entity_kyb: bool = False,
) -> tuple[bool, int, dict[str, Any]]:
    """Judge one transaction against its amount tier.

    Returns (allowed, http_status, detail). `identity_payload`
    is an x401 credential payload judged by the same stub
    verifier as /identity/verify; Tier 2 additionally requires
    its `entityId` (the credential tied to an Entity). Tier 3
    requires `entity_kyb` (the Entity's KYB standing, asserted
    by the caller in this mock; the real KYB provider check is
    Sprint 2, like every real verifier in this module)."""
    tier = classify_amount_tier(amount_usd)
    base = {"tier": tier, "amount_usd": amount_usd, "mock": True}
    if tier == 1:
        return True, 200, {**base, "requirements": ["x402"], "allowed": True}
    ok, cred = verify_identity_payload(identity_payload)
    if not ok:
        return False, 401, {
            **base,
            "allowed": False,
            "requirements": ["x402", "x401"],
            "error": "x401 identity required for this amount tier",
            "identity_challenge": cred,
        }
    if tier == 2:
        entity_id = (
            identity_payload.get("entityId")
            if isinstance(identity_payload, dict)
            else None
        )
        if not entity_id:
            return False, 401, {
                **base,
                "allowed": False,
                "requirements": ["x402", "x401", "entity-link"],
                "error": "x401 identity must be tied to an Entity for Tier 2",
            }
        return True, 200, {
            **base,
            "allowed": True,
            "requirements": ["x402", "x401", "entity-link"],
            "entity_id": entity_id,
        }
    # Tier 3
    if not entity_kyb:
        return False, 403, {
            **base,
            "allowed": False,
            "requirements": ["x402", "x401", "entity-kyb"],
            "error": "full Entity KYB required for Tier 3 amounts",
        }
    return True, 200, {
        **base,
        "allowed": True,
        "requirements": ["x402", "x401", "entity-kyb"],
    }


class TierCheckIn(BaseModel):
    amount_usd: float
    identity: dict[str, Any] | None = None
    entity_kyb: bool = False


@router.post("/metering/tier-check")
def metering_tier_check(body: TierCheckIn):
    """The three-tier gate as an endpoint: what a transaction of
    this size must present before x402 settlement proceeds."""
    allowed, status, detail = enforce_amount_tier(
        body.amount_usd, body.identity, body.entity_kyb
    )
    if not allowed:
        return JSONResponse(status_code=status, content=detail)
    return detail
