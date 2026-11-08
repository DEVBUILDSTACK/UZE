"""Trust-layer resolution in compose (post-audit spec, 2026-11-08).

When the Assurative trust layer resolves a NEAR account, compose
stamps its Entity on the intent (and attributes settlements to the
bidder's Entity in the EventLog). The trust layer is the source of
truth: a contradicting client-supplied entityId is a 422. When
resolution is unavailable, posted references stand — the trust
layer never blocks the marketplace. Resolution is monkeypatched
here; the live two-service proof is the demo-environment run.
"""

from __future__ import annotations

import copy

import pytest

import db as db_module
import models
import near_client
import settle as settle_module
import settlement
import trust

ENTITY_ID = "a380c150-1fb9-49fb-992a-1e3b89593472"
BIDDER_ENTITY_ID = "c9d8e7f6-a5b4-4c3d-2e1f-0a9b8c7d6e5f"
AFFILIATE_ID = "b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e"


def _spec(fixture, **overrides) -> dict:
    body = copy.deepcopy(fixture["spec"])
    body.pop("posterLabel", None)
    for key in ("entityId", "affiliateId"):
        body.pop(key, None)
    body.update(overrides)
    return body


def test_resolution_stamps_entity_and_affiliate(
    market_client, demo_fixture, monkeypatch
):
    monkeypatch.setattr(
        trust,
        "resolve_account",
        lambda account: {
            "entityId": ENTITY_ID,
            "affiliateId": AFFILIATE_ID,
            "scopes": [],
            "agent": False,
        },
    )
    r = market_client.post("/api/v1/specs", json=_spec(demo_fixture))
    assert r.status_code == 201, r.text
    assert r.json()["entityId"] == ENTITY_ID
    assert r.json()["affiliateId"] == AFFILIATE_ID


def test_conflicting_entity_id_is_422(market_client, demo_fixture, monkeypatch):
    monkeypatch.setattr(
        trust,
        "resolve_account",
        lambda account: {
            "entityId": ENTITY_ID,
            "affiliateId": None,
            "scopes": [],
            "agent": False,
        },
    )
    r = market_client.post(
        "/api/v1/specs",
        json=_spec(
            demo_fixture,
            entityId="00000000-0000-4000-8000-000000000000",
        ),
    )
    assert r.status_code == 422, r.text
    assert "trust layer" in r.json()["detail"]


def test_unresolved_falls_back_to_posted_references(
    market_client, demo_fixture, monkeypatch
):
    monkeypatch.setattr(trust, "resolve_account", lambda account: None)
    body = _spec(demo_fixture, entityId=ENTITY_ID)
    r = market_client.post("/api/v1/specs", json=body)
    assert r.status_code == 201, r.text
    assert r.json()["entityId"] == ENTITY_ID


def test_settle_attributes_bidder_entity_in_event_log(
    market_client, demo_fixture, monkeypatch
):
    def resolve(account):
        if account == "recon.uzemarkets-talent.testnet":
            return {
                "entityId": BIDDER_ENTITY_ID,
                "affiliateId": None,
                "scopes": ["bid"],
                "agent": True,
            }
        return None

    monkeypatch.setattr(trust, "resolve_account", resolve)
    monkeypatch.setattr(near_client, "chain_enabled", lambda: True)
    monkeypatch.setattr(
        near_client,
        "settle",
        lambda intent_ref, bid_ref: {
            "status": "submitted",
            "result": "stub_settlement_id",
        },
    )
    monkeypatch.setattr(
        settlement,
        "settle_usdc",
        lambda account, amount: {
            "status": "signed",
            "reason": "test double: signed, not broadcast",
            "payerAddress": "payer",
            "payeeAddress": "payee",
        },
    )

    spec = copy.deepcopy(demo_fixture["spec"])
    spec.pop("posterLabel", None)
    spec_id = market_client.post("/api/v1/specs", json=spec).json()["id"]
    bid = copy.deepcopy(demo_fixture["bids"][1])  # the agent bid
    bid.pop("bidderLabel", None)
    bid["intentId"] = spec_id
    bid_id = market_client.post("/api/v1/bids", json=bid).json()["id"]

    r = market_client.post(
        "/api/v1/settle", json={"intentId": spec_id, "bidId": bid_id}
    )
    assert r.status_code == 200, r.text
    assert r.json()["settlement"]["status"] == "signed"

    session = db_module.session()
    try:
        rows = (
            session.query(models.EventLog)
            .filter(
                models.EventLog.aggregate_id == spec_id,
                models.EventLog.event_type == "settlement.signed",
            )
            .all()
        )
    finally:
        session.close()
    assert len(rows) == 1
    assert rows[0].payload["bidderEntityId"] == BIDDER_ENTITY_ID
    assert rows[0].payload["bidderAffiliateId"] is None
