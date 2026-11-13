"""x402 v2 paywall on the underwrite SKUs (owner-endorsed
build, 2026-11-13).

Simulates the agent flow end to end: hit the endpoint, get
a 402 with a decodable PAYMENT-REQUIRED header quoting the
configured amount on Base + Solana, retry with a
PAYMENT-SIGNATURE, and receive the underwrite with a
PAYMENT-RESPONSE receipt and a mock-flagged EventLog row.
Also pins the honesty rails: unconfigured pricing answers
503 (never an invented quote), a short payment is refused,
and unserved SKUs say so.
"""

from __future__ import annotations

import base64
import json

import db
import models
import x402

YEARS = [{
    "line_items": {
        "Rental Revenue": 1_000_000,
        "Payroll - Property Manager": -60_000,
        "Property Taxes": -90_000,
        "Insurance": -25_000,
    }
}]

ENV = {
    "X402_SKU_AMOUNT_ATOMIC": "5000000",
    "X402_PAYTO_BASE": "0x1111111111111111111111111111111111111111",
    "X402_PAYTO_SOLANA": "SoLanaPayTo1111111111111111111111111111",
}


def _configure(monkeypatch):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)


def test_unconfigured_pricing_is_a_labelled_503(client, monkeypatch):
    for k in ENV:
        monkeypatch.delenv(k, raising=False)
    r = client.post("/api/v1/underwrite/UZ-W-001", json={"years": YEARS})
    assert r.status_code == 503
    assert r.json()["error"] == "PRICING_NOT_CONFIGURED"


def test_agent_flow_402_then_paid_retry(client, monkeypatch):
    _configure(monkeypatch)
    r = client.post("/api/v1/underwrite/UZ-W-001", json={"years": YEARS})
    assert r.status_code == 402
    payload = json.loads(base64.b64decode(r.headers["PAYMENT-REQUIRED"]))
    assert payload["x402Version"] == 2
    assert payload["resource"]["url"] == "/api/v1/underwrite/UZ-W-001"
    by_network = {a["network"]: a for a in payload["accepts"]}
    assert by_network["eip155:8453"]["asset"] == x402.BASE_USDC
    assert by_network["solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp"]["asset"] \
        == x402.SOLANA_USDC
    assert all(a["amount"] == "5000000" for a in payload["accepts"])
    # No feePayer is shipped when none is configured.
    sol = by_network["solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp"]
    assert "feePayer" not in sol["extra"]

    header = x402.build_mock_signature_header(
        payer="agent-wallet-1",
        network="eip155:8453",
        amount="5000000",
        pay_to=ENV["X402_PAYTO_BASE"],
    )
    r2 = client.post(
        "/api/v1/underwrite/UZ-W-001",
        json={"years": YEARS},
        headers={"PAYMENT-SIGNATURE": header},
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["payment"]["mock"] is True
    assert "talent_placement" in body["result"]
    receipt = json.loads(base64.b64decode(r2.headers["PAYMENT-RESPONSE"]))
    assert receipt["success"] is True and receipt["mock"] is True

    session = db.session()
    try:
        rows = (
            session.query(models.EventLog)
            .filter_by(event_type="x402.mock_settlement")
            .all()
        )
    finally:
        session.close()
    mine = [e for e in rows if e.actor == "agent-wallet-1"]
    assert mine and mine[-1].payload["mock"] is True
    assert mine[-1].payload["amountAtomic"] == "5000000"


def test_short_payment_is_refused_with_a_fresh_402(client, monkeypatch):
    _configure(monkeypatch)
    header = x402.build_mock_signature_header(
        payer="agent-wallet-2",
        network="eip155:8453",
        amount="4999999",
        pay_to=ENV["X402_PAYTO_BASE"],
    )
    r = client.post(
        "/api/v1/underwrite/UZ-W-001",
        json={"years": YEARS},
        headers={"PAYMENT-SIGNATURE": header},
    )
    assert r.status_code == 402
    assert "below the quoted amount" in r.json()["error"]


def test_unserved_sku_says_so(client, monkeypatch):
    _configure(monkeypatch)
    r = client.post("/api/v1/underwrite/UZ-W-005", json={"years": YEARS})
    assert r.status_code == 422
    assert r.json()["error"] == "SKU_NOT_SERVED"
