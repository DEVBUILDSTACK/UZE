"""Agriculture webhook — evidence-gated intake (governance spec
06, 2026-11-08).

Pins the three enforcements and the Iron Rule: authentication
(503 unconfigured, 401 wrong secret), idempotency (a replay
returns the original referral, never a duplicate), validation
against the §3A shape — and the referral stops at
INPUT_VALIDATED. A fiat_collapse macro driver is recorded as a
flag and advances nothing.
"""

from __future__ import annotations

import pytest

import db as db_module
import models

SECRET = "test-webhook-secret"

BODY = {
    "schema_version": "1.0",
    "track": "A",
    "transaction_type": "agtech_referral",
    "crop_type": "CORN",
    "production_purpose": "SILAGE",
    "provider_preference": "EFFATHA",
    "provider_status": "VERIFIED",  # the payload claims verified…
    "requested_next_action": "ELIGIBILITY_ASSESSMENT",
    "consent_record_ids": ["c0ffee00-0000-4000-8000-000000000001"],
    "country_code": "PY",
    "macro_driver": "fiat_collapse",
    "polygon": {
        "type": "Polygon",
        "coordinates": [[
            [-57.6, -25.3], [-57.5, -25.3],
            [-57.5, -25.2], [-57.6, -25.3],
        ]],
    },
}


@pytest.fixture()
def webhook_env(monkeypatch):
    monkeypatch.setenv("AGTECH_WEBHOOK_SECRET", SECRET)
    return {"X-Webhook-Secret": SECRET, "Idempotency-Key": "wh-0001"}


def _referrals():
    session = db_module.session()
    try:
        return session.query(models.AgReferral).all()
    finally:
        session.close()


def test_unconfigured_secret_refuses_everything(market_client, monkeypatch):
    monkeypatch.delenv("AGTECH_WEBHOOK_SECRET", raising=False)
    r = market_client.post(
        "/api/v1/webhooks/agriculture/intent",
        json=BODY,
        headers={"X-Webhook-Secret": "anything", "Idempotency-Key": "wh-x"},
    )
    assert r.status_code == 503
    assert _referrals() == []


def test_wrong_secret_is_401(market_client, webhook_env):
    headers = dict(webhook_env, **{"X-Webhook-Secret": "nope"})
    r = market_client.post(
        "/api/v1/webhooks/agriculture/intent", json=BODY, headers=headers
    )
    assert r.status_code == 401
    assert _referrals() == []


def test_missing_idempotency_key_is_422(market_client, webhook_env):
    r = market_client.post(
        "/api/v1/webhooks/agriculture/intent",
        json=BODY,
        headers={"X-Webhook-Secret": SECRET},
    )
    assert r.status_code == 422
    assert _referrals() == []


def test_valid_intake_stops_at_input_validated(market_client, webhook_env):
    r = market_client.post(
        "/api/v1/webhooks/agriculture/intent", json=BODY, headers=webhook_env
    )
    assert r.status_code == 201, r.text
    body = r.json()
    # The Iron Rule: validated, flagged — and nothing further.
    assert body["state"] == "input_validated"
    assert body["nextState"] == "spatial_assessment_pending"
    assert body["providerEligibility"] == "pending"
    assert body["countryCode"] == "PY"
    assert body["macroDistressExit"] is True
    assert body["replayed"] is False

    rows = _referrals()
    assert len(rows) == 1
    referral = rows[0]
    assert referral.state is models.AgReferralState.INPUT_VALIDATED
    # …but the server does not let the payload claim it (§4).
    assert referral.payload["provider_status"] == "UNVERIFIED"
    assert referral.payload["outcome_status"] == "NOT_ASSESSED"

    session = db_module.session()
    try:
        events = (
            session.query(models.EventLog)
            .filter(models.EventLog.aggregate_id == referral.id)
            .all()
        )
    finally:
        session.close()
    assert {e.event_type for e in events} == {
        "ag_referral.received",
        "ag_referral.transition",
    }
    transition = next(
        e for e in events if e.event_type == "ag_referral.transition"
    )
    assert transition.payload["fromState"] == "intent_received"
    assert transition.payload["toState"] == "input_validated"


def test_replay_returns_original_without_duplicating(
    market_client, webhook_env
):
    first = market_client.post(
        "/api/v1/webhooks/agriculture/intent", json=BODY, headers=webhook_env
    )
    second = market_client.post(
        "/api/v1/webhooks/agriculture/intent", json=BODY, headers=webhook_env
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["replayed"] is True
    assert len(_referrals()) == 1


def test_shape_violations_are_422(market_client, webhook_env):
    for patch in (
        {"schema_version": "2.0"},
        {"track": "H"},
        {"transaction_type": "direct_sale"},
        {"country_code": "AR"},
    ):
        body = dict(BODY, **patch)
        r = market_client.post(
            "/api/v1/webhooks/agriculture/intent",
            json=body,
            headers=dict(webhook_env, **{"Idempotency-Key": f"wh-bad-{patch}"}),
        )
        assert r.status_code == 422, (patch, r.text)
    assert _referrals() == []
