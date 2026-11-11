"""Treasury — on-ramp configuration + Send/Receive (treasury.py).

Pins the corrected Treasury spec (2026-11-11):

  - the increment ladder is enforced exactly: $5–$100 by $5,
    $101–$250 by $10, $251–$1,750 by $50, above $1,750 refused,
    below $5 refused, non-whole dollars refused;
  - the on-ramp config defaults to Solana USDC, is
    self-custodial, and UZEmarkets never touches fiat;
  - Send/Receive mocks the CDP routing across Solana, Base,
    Ink, Robinhood, Arc and NEAR; unsupported chains refused;
  - a Send/Receive into NEAR for an agent credits the agent's
    mock compute balance and lands in the EventLog;
  - every Send/Receive payload carries the X401 identity block
    with Arc support stated.
"""
from __future__ import annotations

import pytest

import models
import treasury_router
from db import session as db_session


@pytest.fixture(autouse=True)
def _db_ready(migrated_db):
    yield


@pytest.mark.parametrize(
    "amount", [5, 25, 100, 110, 200, 250, 300, 1000, 1750]
)
def test_onramp_valid_amounts(client, amount):
    resp = client.post("/api/v1/treasury/onramp/config", json={"amount": amount})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["amount"] == amount
    assert body["target_chain"] == "Solana"
    assert body["target_asset"] == "USDC"
    assert body["custody"] == "self-custodial"
    assert body["uze_touches_fiat"] is False


@pytest.mark.parametrize(
    "amount",
    [0, 3, 7, 102, 105, 255, 260, 1751, 1800, 100.5, -50],
)
def test_onramp_invalid_amounts_422(client, amount):
    resp = client.post("/api/v1/treasury/onramp/config", json={"amount": amount})
    assert resp.status_code == 422, (amount, resp.text)


def test_onramp_alternative_chains(client):
    for chain, label in [
        ("BASE", "Base"),
        ("ROBINHOOD", "Robinhood Chain"),
        ("INK", "Ink"),
        ("ARC", "Arc"),
    ]:
        resp = client.post(
            "/api/v1/treasury/onramp/config",
            json={"amount": 50, "chain": chain},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["target_chain"] == label
    bad = client.post(
        "/api/v1/treasury/onramp/config",
        json={"amount": 50, "chain": "DOGE"},
    )
    assert bad.status_code == 422


def test_send_receive_cross_chain_mock(client):
    resp = client.post(
        "/api/v1/treasury/send-receive",
        json={"amount": 25, "source_chain": "SOLANA", "target_chain": "BASE"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["route"] == "cdp-swap"
    assert body["cross_chain"] is True
    assert body["mock"] is True
    assert body["identity"]["protocol"] == "x401"
    assert body["identity"]["arc_supported"] is True
    assert body["payments"]["protocol"] == "x402"


def test_send_receive_same_chain_is_p2p(client):
    resp = client.post(
        "/api/v1/treasury/send-receive",
        json={
            "amount": 25,
            "source_chain": "SOLANA",
            "target_chain": "SOLANA",
            "recipient": "some-wallet",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["route"] == "p2p-send"


def test_send_receive_into_near_credits_agent(client):
    treasury_router.set_mock_near_balance("GIRA", 0.10)
    before = treasury_router.get_mock_near_balance("GIRA")
    resp = client.post(
        "/api/v1/treasury/send-receive",
        json={
            "amount": 10,
            "source_chain": "SOLANA",
            "target_chain": "NEAR",
            "agent": "GIRA",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["credited_near"] == 10
    assert treasury_router.get_mock_near_balance("GIRA") == before + 10
    with db_session() as s:
        rows = (
            s.query(models.EventLog)
            .filter_by(
                aggregate_type="agent",
                aggregate_id="GIRA",
                event_type="treasury.send_receive",
            )
            .all()
        )
        assert rows
        assert rows[-1].payload["target_chain"] == "NEAR"
    treasury_router.set_mock_near_balance("GIRA", 0.10)


def test_send_receive_refusals(client):
    for body in [
        {"amount": 0, "source_chain": "SOLANA", "target_chain": "BASE"},
        {"amount": -5, "source_chain": "SOLANA", "target_chain": "BASE"},
        {"amount": 10, "source_chain": "DOGE", "target_chain": "BASE"},
        {"amount": 10, "source_chain": "SOLANA", "target_chain": "DOGE"},
        {"amount": 10, "source_chain": "SOLANA"},
    ]:
        resp = client.post("/api/v1/treasury/send-receive", json=body)
        assert resp.status_code == 422, (body, resp.text)


# ------------------------------------------------------------------
# NEAR Intents swap route — the 1Click seam is stubbed here (the
# live API is exercised separately; see the build report). The
# tests pin the asset mapping, the wet/dry quote shapes, and the
# refusals — including Ink, which the 1Click registry does not
# list today.
# ------------------------------------------------------------------
import treasury as treasury_module


@pytest.fixture()
def stub_oneclick(monkeypatch):
    calls = []

    def _fake(payload):
        calls.append(payload)
        quote = {
            "amountIn": payload["amount"],
            "amountOut": "424242",
            "deadline": payload["deadline"],
        }
        if not payload["dry"]:
            quote["depositAddress"] = "deposit.testnet-address"
            quote["depositMemo"] = None
        return {"quote": quote}

    monkeypatch.setattr(treasury_module, "_oneclick_quote", _fake)
    return calls


def test_swap_dry_quote_maps_solana_usdc_to_near(client, stub_oneclick):
    resp = client.post(
        "/api/v1/treasury/swap",
        json={
            "amount": 10, "source_chain": "SOLANA", "target_chain": "NEAR",
            "dry": True,
            "recipient": "someone.near",
            "refund_to": "SoLanaRefundAddress1111111111111111111111",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["provider"] == "near-intents-1click"
    assert body["dry"] is True
    assert body["deposit_address"] is None
    assert body["mock"] is False
    assert body["origin_asset"].startswith("nep141:sol-")
    assert body["destination_asset"] == "nep141:wrap.near"
    # 10 USDC at 6 decimals -> the exact minor-unit amount.
    assert stub_oneclick[0]["amount"] == "10000000"


def test_swap_wet_quote_returns_deposit_address(client, stub_oneclick):
    resp = client.post(
        "/api/v1/treasury/swap",
        json={
            "amount": 0.01,
            "source_chain": "BASE",
            "source_asset": "ETH",
            "target_chain": "NEAR",
            "recipient": "someone.near",
            "refund_to": "0x0000000000000000000000000000000000000001",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["dry"] is False
    assert body["deposit_address"] == "deposit.testnet-address"
    assert body["origin_asset"] == "nep141:base.omft.near"
    assert stub_oneclick[0]["amount"] == "10000000000000000"


def test_swap_robinhood_usdg_mapping(client, stub_oneclick):
    resp = client.post(
        "/api/v1/treasury/swap",
        json={
            "amount": 25, "source_chain": "ROBINHOOD", "target_chain": "NEAR",
            "recipient": "someone.near",
            "refund_to": "0x0000000000000000000000000000000000000001",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["origin_asset"].startswith("nep141:hood-0x5fc5360d")


def test_swap_ink_refused_not_in_registry(client, stub_oneclick):
    resp = client.post(
        "/api/v1/treasury/swap",
        json={"amount": 10, "source_chain": "INK", "target_chain": "NEAR"},
    )
    assert resp.status_code == 422
    assert "not listed" in resp.json()["detail"]
    assert stub_oneclick == []


def test_swap_upstream_failure_is_502_not_fabricated(client, monkeypatch):
    def _boom(payload):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(treasury_module, "_oneclick_quote", _boom)
    resp = client.post(
        "/api/v1/treasury/swap",
        json={
            "amount": 10, "source_chain": "SOLANA", "target_chain": "NEAR",
            "recipient": "someone.near",
            "refund_to": "SoLanaRefundAddress1111111111111111111111",
        },
    )
    assert resp.status_code == 502
    assert "deposit" not in resp.text.lower() or "never" in resp.text.lower()
