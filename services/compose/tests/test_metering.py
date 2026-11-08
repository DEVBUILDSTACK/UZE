"""The Sprint 1.5 Day 5 metering mocks (x402 / x401).

The protocol flow is what these tests prove — attempt, 402 with
payment requirements, mock authorization, retry, proceeds; and for
tier C+ specs, the 401 identity challenge in between. The mock
transfer must land in the audit trail flagged as a mock, and the
inference outcome must be the honest one for this environment
(no NEARAI_API_KEY -> "unavailable"). Nothing here fakes a payment,
an identity, or an attestation.
"""

from __future__ import annotations

import copy

import models
import metering
from db import session as db_session
from test_intents import _post_spec


def _post_spec_tier(client, fixture, tier: str) -> dict:
    body = copy.deepcopy(fixture["spec"])
    body.pop("posterLabel", None)
    body["tier"] = tier
    resp = client.post("/api/v1/specs", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_analyze_without_payment_is_402_with_requirements(
    market_client, demo_fixture
):
    spec = _post_spec(market_client, demo_fixture)
    resp = market_client.post(
        "/api/v1/metered/analyze", json={"specId": spec["id"]}
    )
    assert resp.status_code == 402, resp.text
    body = resp.json()
    assert body["mock"] is True
    accepts = body["accepts"][0]
    assert accepts["scheme"] == "mock-exact"
    assert accepts["network"] == "solana-devnet"
    assert accepts["asset"] == "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
    assert accepts["maxAmountRequired"] == str(metering.MOCK_PRICE_BASE_UNITS)
    assert accepts["payTo"] == "5za47wLNFUJyqXhT2eTjeTNC1NsuJpnqLbvHBLBjG8Fy"


def test_analyze_missing_spec_is_404(market_client):
    resp = market_client.post(
        "/api/v1/metered/analyze",
        json={"specId": "00000000-0000-0000-0000-000000000000"},
    )
    assert resp.status_code == 404, resp.text


def test_underpaid_authorization_is_402_again(market_client, demo_fixture):
    spec = _post_spec(market_client, demo_fixture)
    resp = market_client.post(
        "/api/v1/metered/analyze",
        json={"specId": spec["id"]},
        headers={
            "X-PAYMENT": metering.build_mock_authorization(
                "recon.uzemarkets-talent.testnet", amount=1
            )
        },
    )
    assert resp.status_code == 402, resp.text
    assert "amount" in resp.json()["error"]


def test_full_x402_flow_proceeds_and_logs_mock_transfer(
    market_client, demo_fixture
):
    spec = _post_spec(market_client, demo_fixture)
    resp = metering.call_metered_analyze(
        market_client, spec["id"], "recon.uzemarkets-talent.testnet"
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["payment"]["status"] == "mock_settled"
    assert body["payment"]["mock"] is True
    # No key in the test environment -> the honest inference state.
    assert body["inference"]["status"] == "unavailable"

    with db_session() as s:
        events = (
            s.query(models.EventLog)
            .filter_by(event_type="metering.mock_transfer", aggregate_id=spec["id"])
            .all()
        )
    assert len(events) == 1
    assert events[0].payload["mock"] is True
    assert events[0].payload["amountBaseUnits"] == metering.MOCK_PRICE_BASE_UNITS
    assert events[0].actor == "recon.uzemarkets-talent.testnet"


def test_identity_verify_stub_shapes(market_client):
    missing = market_client.post(
        "/api/v1/identity/verify", json={"subject": "syndicate.acme.testnet"}
    )
    assert missing.status_code == 401, missing.text
    assert missing.json()["mock"] is True
    assert "attestation" in missing.json()["required"]

    ok = market_client.post(
        "/api/v1/identity/verify",
        json={
            "subject": "syndicate.acme.testnet",
            "credentialType": "near-account-attestation",
            "attestation": "mock-attested",
        },
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["verified"] is True
    assert body["mock"] is True
    assert body["credential"]["issuer"] == "uzemarkets-identity-stub"


def test_tier_c_spec_requires_identity_after_payment(
    market_client, demo_fixture
):
    spec = _post_spec_tier(market_client, demo_fixture, "C")
    paid_only = market_client.post(
        "/api/v1/metered/analyze",
        json={"specId": spec["id"]},
        headers={
            "X-PAYMENT": metering.build_mock_authorization(
                "syndicate.acme.testnet"
            )
        },
    )
    assert paid_only.status_code == 401, paid_only.text
    assert paid_only.json()["mock"] is True

    full = metering.call_metered_analyze(
        market_client, spec["id"], "syndicate.acme.testnet"
    )
    assert full.status_code == 200, full.text
    assert full.json()["identity"]["verified"] is True
