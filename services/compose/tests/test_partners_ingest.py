"""DevPartner ingestion API — POST /api/v1/partners/ingest.

Pins the Snapshot Pattern + onboarding gate contract:
  - unconfigured deployment -> 503 (never silently open)
  - missing/unknown bearer token -> 401
  - token partner != payload partner_id -> 403
  - payload failing the partner's filed JSON schema -> 422
  - a valid payload per partner -> 202, written to the STAGING
    table as PENDING (never directly to the live ProviderSnapshot
    cache — promotion is the admin API's job), stored verbatim,
    provider UNVERIFIED (Evidence-Gated Architecture)
"""
from __future__ import annotations

import json

import pytest

import models
from db import session as db_session

TOKENS = {
    "tok-agro-test": "AGRO_DIGITAL",
    "tok-bdcs-test": "BDCS",
    "tok-effatha-test": "EFFATHA",
}

# The Agro Digital shape exactly as agreed with the partner on
# 2026-11-08 — the filed schema validates this shape.
AGRO = {
    "partner_id": "AGRO_DIGITAL",
    "polygon_id": "BR-MT-36400",
    "geojson_polygon": {
        "type": "Polygon",
        "coordinates": [
            [[-56.1, -12.5], [-56.0, -12.5], [-56.0, -12.4],
             [-56.1, -12.4], [-56.1, -12.5]]
        ],
    },
    "soil_profile": {
        "ph_level": 5.8,
        "nitrogen_ppm": 12.4,
        "phosphorus_ppm": 8.2,
        "potassium_ppm": 45.0,
        "organic_matter_pct": 2.1,
    },
    "crop_suitability": {
        "crop_type": "CORN_SILAGE",
        "yield_potential_tons_per_ha": 14.5,
        "zarc_risk_score": "LOW",
    },
    "attestation": {
        "provider_timestamp": "2026-11-08T14:00:00Z",
        "cryptographic_hash": "sha256:a1b2c3d4...",
        "satellite_source": "Sentinel-2",
    },
}

BDCS = {
    "partner_id": "BDCS",
    "polygon_id": "BR-MT-36400",
    "language": "pt-BR",
    "feedlot_context": {
        "cattle_head_count": 1500,
        "feed_type": "CORN_SILAGE",
        "target_slaughter_weight_kg": 550,
        "feed_optimization_index": 0.85,
    },
}

EFFATHA = {
    "partner_id": "EFFATHA",
    "polygon_id": "BR-MT-36400",
    "language": "pt-BR",
    "agrotechnical_context": {
        "delivery_mechanism": "SATELLITE_FREQUENCY",
        "treatment_protocol_id": "EFFATHA-CORN-01",
        "target_crop": "CORN_SILAGE",
        "activation_date": "2026-11-08T00:00:00Z",
    },
    "attestation": {
        "provider_timestamp": "2026-11-08T14:00:00Z",
        "cryptographic_hash": "sha256:e5f6g7h8...",
    },
}


@pytest.fixture()
def configured(monkeypatch):
    monkeypatch.setenv("PARTNER_API_TOKENS", json.dumps(TOKENS))
    yield
    with db_session() as session:
        session.query(models.StagingProviderSnapshot).delete()
        session.query(models.ProviderSnapshot).delete()
        session.commit()


def _post(client, payload, token=None):
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return client.post("/api/v1/partners/ingest", json=payload, headers=headers)


def test_unconfigured_deployment_is_503(market_client, monkeypatch):
    monkeypatch.delenv("PARTNER_API_TOKENS", raising=False)
    response = _post(market_client, AGRO, token="tok-agro-test")
    assert response.status_code == 503


def test_missing_and_unknown_tokens_are_401(market_client, configured):
    assert _post(market_client, AGRO).status_code == 401
    assert _post(market_client, AGRO, token="tok-nope").status_code == 401


def test_token_partner_mismatch_is_403(market_client, configured):
    response = _post(market_client, BDCS, token="tok-agro-test")
    assert response.status_code == 403


def test_schema_violation_is_422(market_client, configured):
    broken = {k: v for k, v in AGRO.items() if k != "soil_profile"}
    response = _post(market_client, broken, token="tok-agro-test")
    assert response.status_code == 422
    errors = response.json()["detail"]["errors"]
    assert any(
        "soil_profile" in e["field"] or "soil_profile" in e["error"]
        for e in errors
    )


@pytest.mark.parametrize(
    "payload,token,category",
    [
        (AGRO, "tok-agro-test", "SOIL_SPATIAL"),
        (BDCS, "tok-bdcs-test", "FEEDLOT"),
        (EFFATHA, "tok-effatha-test", "AGROTECHNICAL"),
    ],
)
def test_valid_payloads_are_staged_pending(
    market_client, configured, payload, token, category
):
    response = _post(market_client, payload, token=token)
    assert response.status_code == 202
    body = response.json()
    assert body["partner_id"] == payload["partner_id"]
    assert body["data_category"] == category
    assert body["approval_status"] == "PENDING"
    assert body["provider_status"] == "UNVERIFIED"

    with db_session() as session:
        staged = session.query(models.StagingProviderSnapshot).all()
        assert len(staged) == 1
        row = staged[0]
        assert row.id == body["staging_id"]
        assert row.raw_payload == payload
        assert row.approval_status == "PENDING"
        assert row.fetched_at > 0
        # The gate: nothing reaches the live cache without approval.
        assert session.query(models.ProviderSnapshot).count() == 0
