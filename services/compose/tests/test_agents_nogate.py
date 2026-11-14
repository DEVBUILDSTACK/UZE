"""NoGate alignment — the base builder lane on the agent
doors (James's correction, 2026-11-13, 22:46 ET).

James's filed taxonomy (Tier-1 directive + TREASURY-
ARCHITECTURE.md): the base builder level, UZEBuilder_NO_Entity,
is NOGATE — identity is the agent's email address, the
credential is the wallet payment signature, no KYC, no KYB,
and no x402 spend cap. KYC/KYB belong to the ENTITY tiers.
The attestation requirement follows the ENGAGEMENT's tier
(metering Gate 2's condition): IntentTier C, D, E only.

Pinned here:
  - a plain email X-IDENTITY + a valid mock payment underwrites
    a locally seeded spec (tier ANY) — and the response reports
    the identity honestly (lane base_builder, verified False:
    an email address as presented is not a verification);
  - the same lane works on the GIRA door (polygons carry no
    IntentTier, so that door is always the base band);
  - a payload whose subject is an email is the same identity;
  - a tier C engagement with only a bare email still 401s;
  - a tier C engagement with the attestation passes the gate;
  - base-builder calls are never rejected for spend volume —
    repeated calls and a far-above-tariff authorization both
    proceed (the per-call mock tariff is a protocol stub, not
    a cap, and no cumulative counter exists);
  - no identity at all -> 401 whose body names the email lane;
  - the UZE_Underwrite MCP tool resolves the same email
    identity from the header onto the persisted report.
"""

from __future__ import annotations

import base64
import copy
import json

import metering
from test_mcp_underwrite import ARGS as MCP_ARGS
from test_mcp_underwrite import _call as mcp_call
from test_research import _configure, _pay_header_for

EMAIL = "builder@example.com"
PAYER = "agent:base-builder-1"


def _email_headers(email=EMAIL, payer=PAYER, amount=None):
    return {
        "X-IDENTITY": email,
        "X-PAYMENT": metering.build_mock_authorization(
            payer,
            amount if amount is not None else metering.MOCK_PRICE_BASE_UNITS,
        ),
    }


def _attested_headers(payer=PAYER):
    return {
        "X-IDENTITY": metering.build_mock_identity(payer),
        "X-PAYMENT": metering.build_mock_authorization(payer),
    }


def _post_spec(client, fixture, tier=None):
    spec = copy.deepcopy(fixture["spec"])
    if tier is not None:
        spec["tier"] = tier
    resp = client.post("/api/v1/specs", json=spec)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _sura(client, spec_id, headers):
    return client.post(
        "/api/v1/agents/sura/underwrite",
        json={"specId": spec_id},
        headers=headers,
    )


def test_base_builder_email_underwrites_seeded_spec(
    market_client, demo_fixture
):
    spec = _post_spec(market_client, demo_fixture)
    assert spec["tier"] == "ANY"
    response = _sura(market_client, spec["id"], _email_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["agent"] == "SURA"
    # The identity is reported as what it is: the email address
    # as presented, on the base builder lane — NOT verified.
    assert body["identity"]["subject"] == EMAIL
    assert body["identity"]["lane"] == "base_builder"
    assert body["identity"]["verified"] is False
    assert body["assessment"]["microRegionId"] == spec["microRegionId"]


def test_base_builder_email_on_gira_door(market_client):
    response = market_client.post(
        "/api/v1/agents/gira/underwrite",
        json={"polygonId": "BR-MT-36400"},
        headers=_email_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["assessment"]["status"] == "INSUFFICIENT_DATA"
    assert body["identity"]["subject"] == EMAIL
    assert body["identity"]["lane"] == "base_builder"
    assert body["identity"]["verified"] is False


def test_payload_with_email_subject_is_the_same_identity(
    market_client, demo_fixture
):
    spec = _post_spec(market_client, demo_fixture)
    header = base64.urlsafe_b64encode(
        json.dumps({"subject": EMAIL}).encode()
    ).decode()
    response = _sura(
        market_client,
        spec["id"],
        {
            "X-IDENTITY": header,
            "X-PAYMENT": metering.build_mock_authorization(PAYER),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["identity"]["subject"] == EMAIL
    assert body["identity"]["lane"] == "base_builder"


def test_tier_c_plus_bare_email_still_401(market_client, demo_fixture):
    spec = _post_spec(market_client, demo_fixture, tier="C")
    response = _sura(market_client, spec["id"], _email_headers())
    assert response.status_code == 401
    assert "tier C+" in response.json()["error"]


def test_tier_c_plus_attestation_passes_the_gate(
    market_client, demo_fixture
):
    spec = _post_spec(market_client, demo_fixture, tier="C")
    response = _sura(market_client, spec["id"], _attested_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["identity"]["verified"] is True
    assert body["identity"]["lane"] == "attested"


def test_base_builder_never_rejected_for_spend_volume(
    market_client, demo_fixture
):
    spec = _post_spec(market_client, demo_fixture)
    # Repetition: no cumulative or per-period counter may trip.
    for _ in range(12):
        response = _sura(market_client, spec["id"], _email_headers())
        assert response.status_code == 200
    # Magnitude: an authorization far above the per-call mock
    # tariff is the caller's own business at this band.
    response = _sura(
        market_client,
        spec["id"],
        _email_headers(amount=metering.MOCK_PRICE_BASE_UNITS * 10_000),
    )
    assert response.status_code == 200


def test_missing_identity_401_names_the_email_lane(market_client):
    response = market_client.post(
        "/api/v1/agents/sura/underwrite", json={"specId": "any"}
    )
    assert response.status_code == 401
    body = response.json()
    assert "email" in body["identity"]["base_builder"]
    assert "UZEBuilder_NO_Entity" in body["identity"]["base_builder"]
    assert "IntentTier C, D or E" in body["identity"]["tier_c_plus"]


def test_mcp_underwrite_resolves_email_identity_from_header(
    client, monkeypatch
):
    # The MCP gate's only credential is the payment signature;
    # the email identity rides the header onto the persisted
    # report — no attestation anywhere in the flow.
    _configure(monkeypatch)
    args = {k: v for k, v in MCP_ARGS.items() if k != "sender_email"}
    r = mcp_call(
        client,
        args,
        headers={
            "PAYMENT-SIGNATURE": _pay_header_for("nogate@uze.test"),
            "X-IDENTITY": "mcp-builder@example.com",
        },
    )
    result = r.json()["result"]
    assert result["isError"] is False
    report_id = result["structuredContent"]["receipt"]["report_id"]
    stored = client.get(f"/api/v1/underwrite/reports/{report_id}")
    assert stored.status_code == 200
    assert stored.json()["report"]["sender"] == "mcp-builder@example.com"
