"""DevPartner ingestion API — POST /api/v1/partners/ingest.

Pins the Snapshot Pattern contract:
  - unconfigured deployment -> 503 (never silently open)
  - missing/unknown bearer token -> 401
  - token partner != payload partner_id -> 403
  - payload failing the partner's filed JSON schema -> 422
  - a valid payload per partner -> 202, cached verbatim in
    ProviderSnapshot with cache_status LIVE and provider_status
    UNVERIFIED (Evidence-Gated Architecture: partner-claimed data is
    never stored as verified)
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

AGRO = {
    "partner_id": "AGRO_DIGITAL",
    "polygon_id": "BR-MT-36400",
    "language": "pt-BR",
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
    "zarc_risk_score": "LOW",
    "attestation": {"cryptographic_hash": "sha256:a1b2c3d4..."},
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
    assert "soil_profile" in response.json()["detail"]


@pytest.mark.parametrize(
    "payload,token,category",
    [
        (AGRO, "tok-agro-test", "SOIL_SPATIAL"),
        (BDCS, "tok-bdcs-test", "FEEDLOT"),
        (EFFATHA, "tok-effatha-test", "AGROTECHNICAL"),
    ],
)
def test_valid_payloads_are_cached_unverified(
    market_client, configured, payload, token, category
):
    response = _post(market_client, payload, token=token)
    assert response.status_code == 202
    body = response.json()
    assert body["partner_id"] == payload["partner_id"]
    assert body["data_category"] == category
    assert body["cache_status"] == "LIVE"
    assert body["provider_status"] == "UNVERIFIED"

    with db_session() as session:
        rows = session.query(models.ProviderSnapshot).all()
        assert len(rows) == 1
        row = rows[0]
        assert row.id == body["snapshot_id"]
        assert row.raw_payload == payload
        assert row.provider_status == "UNVERIFIED"
        assert row.fetched_at > 0
