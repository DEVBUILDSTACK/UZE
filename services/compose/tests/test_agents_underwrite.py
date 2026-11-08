"""Headless agent surface — GIRA & SURA underwrite endpoints.

Pins the dual-surface contract:
  - no X-IDENTITY -> 401 (x401 gate first)
  - identity but no X-PAYMENT -> 402 with x402 requirements
  - invalid X-PAYMENT -> 402
  - GIRA: a polygon with nothing approved -> INSUFFICIENT_DATA with
    the PENDING staging count visible but unconsumed; after the
    staging gate approves a payload, the same call is READY and its
    guidance is derived from the ingested payload itself
  - SURA: unknown spec -> 404; the demo spec -> a structured
    assessment from real market state
"""
from __future__ import annotations

import json

import pytest

import metering
import models
from db import session as db_session
from test_intents import _post_spec
from tests.test_partners_ingest import AGRO, TOKENS

ADMIN = {"Authorization": "Bearer tok-admin-test"}


@pytest.fixture()
def agent_env(monkeypatch):
    monkeypatch.setenv("PARTNER_API_TOKENS", json.dumps(TOKENS))
    monkeypatch.setenv("PARTNER_ADMIN_TOKEN", "tok-admin-test")
    yield
    with db_session() as session:
        session.query(models.StagingProviderSnapshot).delete()
        session.query(models.ProviderSnapshot).delete()
        session.commit()


def _headers(payer="agent:underwriter-1"):
    return {
        "X-IDENTITY": metering.build_mock_identity(payer),
        "X-PAYMENT": metering.build_mock_authorization(payer),
    }


def _gira(client, polygon="BR-MT-36400", headers=None):
    return client.post(
        "/api/v1/agents/gira/underwrite",
        json={"polygonId": polygon},
        headers=headers if headers is not None else _headers(),
    )


def test_gates_identity_then_payment(market_client, agent_env):
    no_identity = market_client.post(
        "/api/v1/agents/gira/underwrite", json={"polygonId": "BR-MT-36400"}
    )
    assert no_identity.status_code == 401

    identity_only = market_client.post(
        "/api/v1/agents/gira/underwrite",
        json={"polygonId": "BR-MT-36400"},
        headers={"X-IDENTITY": metering.build_mock_identity("agent:x")},
    )
    assert identity_only.status_code == 402
    assert identity_only.json()["accepts"][0]["scheme"] == "mock-exact"

    bad_payment = market_client.post(
        "/api/v1/agents/gira/underwrite",
        json={"polygonId": "BR-MT-36400"},
        headers={
            "X-IDENTITY": metering.build_mock_identity("agent:x"),
            "X-PAYMENT": "not-a-real-authorization",
        },
    )
    assert bad_payment.status_code == 402


def test_gira_insufficient_data_until_approval(market_client, agent_env):
    # Stage the Agro payload: it is PENDING, so GIRA must not consume it.
    staged = market_client.post(
        "/api/v1/partners/ingest",
        json=AGRO,
        headers={"Authorization": "Bearer tok-agro-test"},
    )
    assert staged.status_code == 202
    staging_id = staged.json()["staging_id"]

    before = _gira(market_client)
    assert before.status_code == 200
    body = before.json()
    assert body["agent"] == "GIRA"
    assert body["assessment"]["status"] == "INSUFFICIENT_DATA"
    assert body["assessment"]["liveSnapshots"] == 0
    assert body["assessment"]["pendingStaging"] == 1

    approved = market_client.post(
        f"/api/v1/admin/partners/approve/{staging_id}", headers=ADMIN
    )
    assert approved.status_code == 200

    after = _gira(market_client)
    body = after.json()
    assert body["assessment"]["status"] == "READY"
    assert body["assessment"]["liveSnapshots"] == 1
    assert body["assessment"]["pendingStaging"] == 0
    guidance = " ".join(body["assessment"]["guidance"])
    assert "pH 5.8" in guidance
    assert "ZARC risk LOW" in guidance
    assert body["assessment"]["sources"][0]["providerStatus"] == "UNVERIFIED"


def test_sura_unknown_spec_is_404(market_client, agent_env):
    response = market_client.post(
        "/api/v1/agents/sura/underwrite",
        json={"specId": "no-such-spec"},
        headers=_headers(),
    )
    assert response.status_code == 404


def test_sura_assesses_demo_spec(market_client, agent_env, demo_fixture):
    spec = _post_spec(market_client, demo_fixture)
    response = market_client.post(
        "/api/v1/agents/sura/underwrite",
        json={"specId": spec["id"]},
        headers=_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["agent"] == "SURA"
    assessment = body["assessment"]
    assert assessment["assetSubclass"] == "H"
    assert assessment["microRegionId"] == spec["microRegionId"]
    assert assessment["budgetMinUsdc"] == spec["budgetMinUsdc"]
    assert assessment["entityId"] == spec["entityId"]
