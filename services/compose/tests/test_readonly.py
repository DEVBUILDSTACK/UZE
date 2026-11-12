"""The Sprint 1.5 Day 6 read-only projections: micro-regions and
talent — the data behind the human (HTML) surface. D4: the pages
project the same fields the agent API serves; these tests pin the
aggregation semantics (spec counts, comparable counts from the
audit trail, talent totals across a bidder's bids) and the 404s.
"""

from __future__ import annotations

from test_intents import _post_spec
from test_settle import _post_bids


def test_micro_regions_list_with_counts(market_client, demo_fixture):
    resp = market_client.get("/api/v1/micro-regions")
    assert resp.status_code == 200, resp.text
    regions = {r["id"]: r for r in resp.json()}
    assert set(regions) == {r["id"] for r in demo_fixture["microRegions"]}
    brickell = regions["miami-brickell"]
    assert brickell["label"] == "Miami — Brickell"
    assert brickell["specCount"] == 0
    assert brickell["comparableCount"] == 0

    spec = _post_spec(market_client, demo_fixture)
    regions = {r["id"]: r for r in market_client.get("/api/v1/micro-regions").json()}
    assert regions["miami-brickell"]["specCount"] == 1

    detail = market_client.get("/api/v1/micro-regions/miami-brickell")
    assert detail.status_code == 200, detail.text
    assert [s["id"] for s in detail.json()["specs"]] == [spec["id"]]
    assert detail.json()["specs"][0]["budgetMaxUsdc"] == 25000


def test_micro_region_missing_is_404(market_client):
    resp = market_client.get("/api/v1/micro-regions/nope")
    assert resp.status_code == 404, resp.text


def test_talent_profile_aggregates_bids(market_client, demo_fixture):
    spec = _post_spec(market_client, demo_fixture)
    _post_bids(market_client, demo_fixture, spec["id"])

    agent = market_client.get("/api/v1/talent/recon.uzemarkets-talent.testnet")
    assert agent.status_code == 200, agent.text
    body = agent.json()
    assert body["kind"] == "agent"
    assert body["bidCount"] == 1
    assert body["totalBidUsdc"] == 4200
    assert body["bids"][0]["amountUsdc"] == 4200
    assert body["bids"][0]["intentId"] == spec["id"]

    human = market_client.get("/api/v1/talent/treasury.uzemarkets-talent.testnet")
    assert human.json()["kind"] == "human"
    assert human.json()["totalBidUsdc"] == 22500


def test_talent_missing_is_404(market_client):
    resp = market_client.get("/api/v1/talent/nobody.testnet")
    assert resp.status_code == 404, resp.text
