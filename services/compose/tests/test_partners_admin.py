"""DevPartner admin approval API — the onboarding gate's second half.

POST /api/v1/admin/partners/approve/{staging_id} promotes a staged
payload verbatim into the live ProviderSnapshot cache;
POST /api/v1/admin/partners/reject/{staging_id} records REJECTED
with a reason and promotes nothing.

Pins:
  - admin API unconfigured -> 503; missing/wrong admin token -> 401
  - unknown staging_id -> 404
  - approve -> 200, exactly one live row (payload verbatim, LIVE,
    UNVERIFIED), staged row APPROVED with a review timestamp
  - a decided staging row cannot be decided again -> 409
  - reject requires a reason -> 422 without one
"""
from __future__ import annotations

import json

import pytest

import models
from db import session as db_session
from tests.test_partners_ingest import AGRO, TOKENS


@pytest.fixture()
def gate(monkeypatch):
    monkeypatch.setenv("PARTNER_API_TOKENS", json.dumps(TOKENS))
    monkeypatch.setenv("PARTNER_ADMIN_TOKEN", "tok-admin-test")
    yield
    with db_session() as session:
        session.query(models.StagingProviderSnapshot).delete()
        session.query(models.ProviderSnapshot).delete()
        session.commit()


def _stage(client) -> str:
    response = client.post(
        "/api/v1/partners/ingest",
        json=AGRO,
        headers={"Authorization": "Bearer tok-agro-test"},
    )
    assert response.status_code == 202
    return response.json()["staging_id"]


def _admin(path, client, token="tok-admin-test", **kwargs):
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return client.post(path, headers=headers, **kwargs)


def test_admin_unconfigured_is_503(market_client, gate, monkeypatch):
    monkeypatch.delenv("PARTNER_ADMIN_TOKEN", raising=False)
    staging_id = _stage(market_client)
    response = _admin(f"/api/v1/admin/partners/approve/{staging_id}", market_client)
    assert response.status_code == 503


def test_admin_auth_required(market_client, gate):
    staging_id = _stage(market_client)
    path = f"/api/v1/admin/partners/approve/{staging_id}"
    assert _admin(path, market_client, token=None).status_code == 401
    assert _admin(path, market_client, token="tok-wrong").status_code == 401


def test_approve_unknown_staging_id_is_404(market_client, gate):
    response = _admin("/api/v1/admin/partners/approve/nope", market_client)
    assert response.status_code == 404


def test_approve_promotes_verbatim_to_live(market_client, gate):
    staging_id = _stage(market_client)
    response = _admin(f"/api/v1/admin/partners/approve/{staging_id}", market_client)
    assert response.status_code == 200
    body = response.json()
    assert body["staging_id"] == staging_id
    assert body["approval_status"] == "APPROVED"

    with db_session() as session:
        live = session.query(models.ProviderSnapshot).all()
        assert len(live) == 1
        row = live[0]
        assert row.id == body["snapshot_id"]
        assert row.raw_payload == AGRO
        assert row.cache_status == "LIVE"
        assert row.provider_status == "UNVERIFIED"
        staged = session.get(models.StagingProviderSnapshot, staging_id)
        assert staged.approval_status == "APPROVED"
        assert staged.reviewed_at is not None

    # A decided payload cannot be decided again.
    again = _admin(f"/api/v1/admin/partners/approve/{staging_id}", market_client)
    assert again.status_code == 409


def test_reject_records_reason_and_promotes_nothing(market_client, gate):
    staging_id = _stage(market_client)
    path = f"/api/v1/admin/partners/reject/{staging_id}"

    no_reason = _admin(path, market_client, json={})
    assert no_reason.status_code == 422

    response = _admin(path, market_client, json={"reason": "units are mg/kg, not ppm"})
    assert response.status_code == 200
    body = response.json()
    assert body["approval_status"] == "REJECTED"
    assert body["rejection_reason"] == "units are mg/kg, not ppm"

    with db_session() as session:
        assert session.query(models.ProviderSnapshot).count() == 0
        staged = session.get(models.StagingProviderSnapshot, staging_id)
        assert staged.approval_status == "REJECTED"
        assert staged.rejection_reason == "units are mg/kg, not ppm"
