"""The Sprint 1.5 intent marketplace flow (Day 2): the demo fixture —
a 340-room Aloft in Miami-Brickell, a human bid and an agent bid —
posted through the real API against the real migrated schema.

The chain gate is closed in tests (COMPOSE_NEAR_CHAIN unset): every
response must state chain.status "disabled" and leave the chain refs
null. The live chain round trip is proven separately by
scripts/near_roundtrip.py — tests never fake it.
"""

from __future__ import annotations


def _post_spec(client, fixture) -> dict:
    resp = client.post("/api/v1/specs", json=fixture["spec"])
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_spec_posts_posted_with_chain_disabled(market_client, demo_fixture):
    spec = _post_spec(market_client, demo_fixture)
    assert spec["status"] == "POSTED"
    assert spec["microRegionId"] == "miami-brickell"
    assert spec["assetContext"]["doorCount"] == 340
    assert spec["assetContext"]["brandAffiliation"] == "Aloft"
    assert spec["chainIntentRef"] is None
    assert spec["chain"] == {"status": "disabled"}
    assert spec["bidCount"] == 0


def test_two_bids_move_spec_to_bidding_and_list_in_order(
    market_client, demo_fixture
):
    spec = _post_spec(market_client, demo_fixture)
    posted = []
    for bid in demo_fixture["bids"]:
        body = {k: v for k, v in bid.items() if k != "bidderLabel"}
        body["intentId"] = spec["id"]
        resp = market_client.post("/api/v1/bids", json=body)
        assert resp.status_code == 201, resp.text
        posted.append(resp.json())

    assert [b["amountUsdc"] for b in posted] == [22500, 4200]
    assert posted[0]["bidderKind"] == "human"
    assert posted[1]["bidderKind"] == "agent"
    assert all(b["chainBidRef"] is None for b in posted)

    view = market_client.get(f"/api/v1/specs/{spec['id']}").json()
    assert view["status"] == "BIDDING"
    assert view["bidCount"] == 2

    listed = market_client.get(f"/api/v1/specs/{spec['id']}/bids").json()
    assert [b["bidderAccount"] for b in listed] == [
        "treasury.uzemarkets-talent.testnet",
        "recon.uzemarkets-talent.testnet",
    ]


def test_unknown_micro_region_is_422(market_client, demo_fixture):
    body = dict(demo_fixture["spec"], microRegionId="nowhere-special")
    resp = market_client.post("/api/v1/specs", json=body)
    assert resp.status_code == 422


def test_inverted_budget_is_422(market_client, demo_fixture):
    body = dict(demo_fixture["spec"], budgetMinUsdc=99999, budgetMaxUsdc=1)
    resp = market_client.post("/api/v1/specs", json=body)
    assert resp.status_code == 422


def test_bid_on_missing_spec_is_404(market_client, demo_fixture):
    body = {k: v for k, v in demo_fixture["bids"][0].items() if k != "bidderLabel"}
    body["intentId"] = "no-such-spec"
    resp = market_client.post("/api/v1/bids", json=body)
    assert resp.status_code == 404


def test_missing_spec_reads_are_404(market_client):
    assert market_client.get("/api/v1/specs/nope").status_code == 404
    assert market_client.get("/api/v1/specs/nope/bids").status_code == 404
