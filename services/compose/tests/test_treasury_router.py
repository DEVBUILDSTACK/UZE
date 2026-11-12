"""Autonomous Treasury & Swap Engine — treasury_router.

Built 2026-11-11 on James's override (see treasury_router's
module docstring). Pins:

  - a low NEAR balance triggers exactly one autonomous swap,
    recorded as an EventLog `agent.treasury.swap_executed` with
    the directive's payload shape, labelled mock;
  - a funded balance triggers no swap and writes no event;
  - every supported rail (Solana USDC, Base ETH, Robinhood USDG,
    Ink) executes through the same router;
  - an unsupported rail is refused;
  - the balance + ensure-compute endpoints serve the same state;
  - the x402-gated GIRA endpoint runs the pre-task check: its
    response carries the treasury result (swap on first call
    from a low balance, none once funded).
"""
from __future__ import annotations

import pytest

import models
import treasury_router
from db import session as db_session
from test_agents_underwrite import _gira


@pytest.fixture(autouse=True)
def _reset_balances(migrated_db):
    # Depending on migrated_db here forces the session-scoped
    # database reset to happen before this module's plain-session
    # tests open pooled connections (which would otherwise block
    # the fixture's DROP DATABASE when a TestClient test runs
    # later in the same session).
    treasury_router.set_mock_near_balance("GIRA", 0.10)
    treasury_router.set_mock_near_balance("SURA", 0.10)
    yield
    treasury_router.set_mock_near_balance("GIRA", 0.10)
    treasury_router.set_mock_near_balance("SURA", 0.10)


def _swap_events(agent="SURA"):
    with db_session() as s:
        rows = (
            s.query(models.EventLog)
            .filter_by(
                aggregate_type="agent",
                aggregate_id=agent,
                event_type="agent.treasury.swap_executed",
            )
            .all()
        )
        return [r.payload for r in rows]


def _ensure(agent="SURA", rail="SOLANA_USDC"):
    with db_session() as s:
        result = treasury_router.ensure_compute_funded(s, agent, rail)
        s.commit()
        return result


def test_low_balance_triggers_one_swap_and_event():
    before = len(_swap_events())
    result = _ensure()
    assert result["swap_executed"] is True
    swap = result["swap"]
    assert swap["source_asset"] == "SOLANA_USDC"
    assert swap["target_asset"] == "NEAR"
    assert swap["amount"] == 10
    assert swap["mock"] is True
    assert result["near_balance"] >= treasury_router.INFERENCE_THRESHOLD_NEAR
    events = _swap_events()
    assert len(events) == before + 1
    assert events[-1]["source_asset"] == "SOLANA_USDC"
    # Second call: balance now funded — no further swap, no event.
    again = _ensure()
    assert again["swap_executed"] is False
    assert len(_swap_events()) == before + 1


def test_funded_balance_no_swap():
    treasury_router.set_mock_near_balance("SURA", 5.0)
    before = len(_swap_events())
    result = _ensure()
    assert result["funded"] is True
    assert result["swap_executed"] is False
    assert len(_swap_events()) == before


@pytest.mark.parametrize(
    "rail,source_asset,amount",
    [
        ("SOLANA_USDC", "SOLANA_USDC", 10),
        ("BASE_ETH", "BASE_ETH", 0.05),
        ("ROBINHOOD_USDG", "ROBINHOOD_USDG", 10),
        ("INK_ASSET", "INK_ASSET", 10),
    ],
)
def test_every_supported_rail_swaps(rail, source_asset, amount):
    treasury_router.set_mock_near_balance("SURA", 0.0)
    result = _ensure(rail=rail)
    assert result["swap_executed"] is True
    assert result["swap"]["source_asset"] == source_asset
    assert result["swap"]["amount"] == amount
    assert result["swap"]["target_asset"] == "NEAR"


def test_unsupported_rail_refused():
    with db_session() as s:
        with pytest.raises(ValueError):
            treasury_router.ensure_compute_funded(s, "SURA", "DOGE_RAIL")


def test_treasury_endpoints(client):
    treasury_router.set_mock_near_balance("SURA", 0.10)
    bal = client.get("/api/v1/treasury/balance/SURA")
    assert bal.status_code == 200
    assert bal.json()["funded"] is False
    assert "SOLANA_USDC" in bal.json()["supported_rails"]

    resp = client.post(
        "/api/v1/treasury/ensure-compute",
        json={"agent": "SURA", "rail": "BASE_ETH"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["swap_executed"] is True
    assert body["swap"]["source_asset"] == "BASE_ETH"

    bad = client.post(
        "/api/v1/treasury/ensure-compute",
        json={"agent": "SURA", "rail": "NOPE"},
    )
    assert bad.status_code == 422


def test_gira_endpoint_runs_pre_task_check(market_client):
    resp = _gira(market_client)
    assert resp.status_code == 200
    treasury = resp.json()["treasury"]
    assert treasury["swap_executed"] is True
    assert treasury["swap"]["target_asset"] == "NEAR"
    # Funded now — the next task runs without a swap.
    resp2 = _gira(market_client)
    assert resp2.json()["treasury"]["swap_executed"] is False
