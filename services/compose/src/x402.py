"""x402 v2 header flow (owner-endorsed build, 2026-11-13).

The Exa-style standardization of the Sprint 1.5 metering
mock: where metering.py speaks x402 v1 shapes (X-PAYMENT
header, body-carried requirements, devnet), this module
speaks the v2 envelope an external agent ecosystem uses:

  - no/invalid payment -> HTTP 402 with a base64
    PAYMENT-REQUIRED response header whose JSON payload is
    {x402Version: 2, resource: {url, description},
     accepts: [ {scheme "exact", network, amount, asset,
     payTo, maxTimeoutSeconds, extra} ]} for USDC on Base
     (eip155:8453) and Solana (mainnet), mirrored in the
     response body;
  - the retry carries a base64 PAYMENT-SIGNATURE header;
    validation here is the codebase's established MOCK
    profile (field-level checks + the deterministic
    "mock:" signature of metering.py). Cryptographic
    verification and facilitator settlement are NOT
    implemented — they wait on the real CDP/facilitator
    decision, exactly as metering.py records. A validated
    payment is logged as an EventLog row flagged mock:true
    (event x402.mock_settlement); it is not a settlement
    and moves no funds.

Pricing discipline (owner ruling, 2026-11-12): no static
price is posted anywhere in this platform — participation
is priced by the UZEguidance market and quoted per
request. This module therefore takes the quoted amount
and the payTo addresses from configuration
(X402_SKU_AMOUNT_ATOMIC, X402_PAYTO_BASE, X402_PAYTO_SOLANA,
optional X402_SOLANA_FEEPAYER) and NEVER invents either.
Unconfigured, the gated endpoint answers 503
PRICING_NOT_CONFIGURED instead of fabricating a quote.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from typing import Any

X402_VERSION = 2
SCHEME = "exact"
MAX_TIMEOUT_SECONDS = 60

BASE_NETWORK = "eip155:8453"
BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
SOLANA_NETWORK = "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp"
SOLANA_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

_NETWORKS: dict[str, dict[str, str]] = {
    BASE_NETWORK: {"asset": BASE_USDC, "payto_env": "X402_PAYTO_BASE"},
    SOLANA_NETWORK: {
        "asset": SOLANA_USDC,
        "payto_env": "X402_PAYTO_SOLANA",
    },
}


def pricing_config() -> dict[str, Any] | None:
    """The configured quote, or None. Amount is USDC atomic
    units (6 decimals) as a string, per the v2 schema."""
    raw_amount = os.environ.get("X402_SKU_AMOUNT_ATOMIC", "").strip()
    if not raw_amount.isdigit() or int(raw_amount) <= 0:
        return None
    accepts: list[dict[str, Any]] = []
    for network, spec in _NETWORKS.items():
        pay_to = os.environ.get(spec["payto_env"], "").strip()
        if not pay_to:
            continue
        extra: dict[str, str] = {"name": "USD Coin", "version": "2"}
        if network == SOLANA_NETWORK:
            fee_payer = os.environ.get(
                "X402_SOLANA_FEEPAYER", ""
            ).strip()
            if fee_payer:
                extra["feePayer"] = fee_payer
        accepts.append(
            {
                "scheme": SCHEME,
                "network": network,
                "amount": raw_amount,
                "asset": spec["asset"],
                "payTo": pay_to,
                "maxTimeoutSeconds": MAX_TIMEOUT_SECONDS,
                "extra": extra,
            }
        )
    if not accepts:
        return None
    return {"amount": raw_amount, "accepts": accepts}


def build_payment_required(
    resource_url: str, description: str, config: dict[str, Any]
) -> dict[str, Any]:
    return {
        "x402Version": X402_VERSION,
        "mock": True,
        "resource": {"url": resource_url, "description": description},
        "accepts": config["accepts"],
    }


def encode_header(payload: dict[str, Any]) -> str:
    return base64.b64encode(json.dumps(payload).encode()).decode()


def _decode_header(value: str) -> dict[str, Any] | None:
    try:
        return json.loads(base64.b64decode(value.encode()))
    except Exception:
        return None


def _canonical(auth: dict[str, Any]) -> str:
    return json.dumps(
        {
            k: auth[k]
            for k in (
                "scheme", "network", "asset", "amount",
                "payer", "payTo", "nonce",
            )
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def mock_signature(auth: dict[str, Any]) -> str:
    """Same convention as metering.mock_signature: the
    "mock:" prefix is the point — a well-formed mock
    authorization, never mistakable for a cryptographic
    payment signature."""
    return "mock:" + hashlib.sha256(_canonical(auth).encode()).hexdigest()


def build_mock_signature_header(
    payer: str,
    network: str,
    amount: str,
    pay_to: str,
) -> str:
    """The agent side of the mock: a PAYMENT-SIGNATURE header
    value for tests and demos."""
    auth: dict[str, Any] = {
        "x402Version": X402_VERSION,
        "scheme": SCHEME,
        "network": network,
        "asset": _NETWORKS[network]["asset"],
        "amount": amount,
        "payer": payer,
        "payTo": pay_to,
        "nonce": f"{int(time.time())}-{payer}",
    }
    auth["signature"] = mock_signature(auth)
    return base64.b64encode(json.dumps(auth).encode()).decode()


def validate_payment_signature(
    value: str, config: dict[str, Any]
) -> tuple[bool, str, dict[str, Any] | None]:
    auth = _decode_header(value)
    if auth is None:
        return False, "PAYMENT-SIGNATURE is not base64 JSON", None
    if auth.get("x402Version") != X402_VERSION:
        return False, "x402Version must be 2", None
    if auth.get("scheme") != SCHEME:
        return False, f"scheme must be {SCHEME}", None
    accepted = {a["network"]: a for a in config["accepts"]}
    network = auth.get("network")
    if network not in accepted:
        return False, "network is not among the accepted networks", None
    want = accepted[network]
    if auth.get("asset") != want["asset"]:
        return False, "asset must be the network's USDC contract", None
    if auth.get("payTo") != want["payTo"]:
        return False, "payTo does not match the quote", None
    amount = str(auth.get("amount", ""))
    if not amount.isdigit() or int(amount) < int(want["amount"]):
        return False, "amount is below the quoted amount", None
    if auth.get("signature") != mock_signature(auth):
        return False, "mock signature does not verify", None
    return True, "", auth
