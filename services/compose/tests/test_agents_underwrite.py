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


def _debug(client, payload):
    return client.post("/api/v1/agents/gira/debug", json={"payload": payload})


def test_debug_coerces_numeric_strings(market_client):
    broken = json.loads(json.dumps(AGRO))
    broken["soil_profile"]["ph_level"] = "5.8"
    response = _debug(market_client, broken)
    assert response.status_code == 200
    body = response.json()
    assert body["validBefore"] is False
    assert body["validAfter"] is True
    assert body["correctedPayload"]["soil_profile"]["ph_level"] == 5.8
    assert any("ph_level" in fix for fix in body["fixes"])


def test_debug_moves_top_level_zarc(market_client):
    broken = json.loads(json.dumps(AGRO))
    broken["zarc_risk_score"] = broken["crop_suitability"].pop("zarc_risk_score")
    body = _debug(market_client, broken).json()
    assert body["validAfter"] is True
    assert body["correctedPayload"]["crop_suitability"]["zarc_risk_score"] == "LOW"
    assert "zarc_risk_score" not in body["correctedPayload"]


def test_debug_drops_undefined_keys(market_client):
    broken = json.loads(json.dumps(AGRO))
    broken["language"] = "pt-BR"
    body = _debug(market_client, broken).json()
    assert body["validAfter"] is True
    assert "language" not in body["correctedPayload"]
    assert any("language" in fix for fix in body["fixes"])


def test_debug_valid_payload_unchanged(market_client):
    body = _debug(market_client, json.loads(json.dumps(AGRO))).json()
    assert body["validBefore"] is True
    assert body["correctedPayload"] is None
    assert body["remainingErrors"] == []


def test_debug_reports_unfixable_errors(market_client):
    broken = {k: v for k, v in AGRO.items() if k != "soil_profile"}
    body = _debug(market_client, broken).json()
    assert body["validAfter"] is False
    assert any("soil_profile" in e["error"] for e in body["remainingErrors"])
