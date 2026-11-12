"""The Sprint 1.5 settle flow (Day 3), chain gate closed: selection
semantics against the real migrated schema.

With COMPOSE_NEAR_CHAIN unset, settle must record the Match and the
selection honestly and claim nothing about settlement: the spec
rests at SELECTED, the settlement block says "disabled", no
settlement event is written. The live leg (contract call, MPC sign,
devnet broadcast) is exercised by scripts/settle_dryrun.py — tests
never fake it.
"""

from __future__ import annotations

from test_intents import _post_spec  # the demo fixture poster


def _post_bids(client, demo_fixture, spec_id) -> list[dict]:
    posted = []
    for bid in demo_fixture["bids"]:
        body = {k: v for k, v in bid.items() if k != "bidderLabel"}
        body["intentId"] = spec_id
        resp = client.post("/api/v1/bids", json=body)
        assert resp.status_code == 201, resp.text
        posted.append(resp.json())
    return posted


def test_settle_selects_agent_bid_and_rests_at_selected(
    market_client, demo_fixture
):
    spec = _post_spec(market_client, demo_fixture)
    bids = _post_bids(market_client, demo_fixture, spec["id"])
    agent_bid = bids[1]

    resp = market_client.post(
        "/api/v1/settle", json={"intentId": spec["id"], "bidId": agent_bid["id"]}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # Selection is real; settlement is honestly unclaimed.
    assert body["spec"]["status"] == "SELECTED"
    assert body["settlement"] == {"status": "disabled"}
    assert body["match"]["state"] == "SELECTED"
    assert body["match"]["bidId"] == agent_bid["id"]
    assert body["match"]["matchedBy"] == demo_fixture["spec"]["posterAccount"]
    assert body["match"]["settlementRef"] is None

    view = market_client.get(f"/api/v1/specs/{spec['id']}/bids").json()
    by_amount = {b["amountUsdc"]: b["status"] for b in view}
    assert by_amount[4200] == "SELECTED"
    assert by_amount[22500] == "NOT_SELECTED"


def test_settle_is_repeatable_while_selected(market_client, demo_fixture):
    spec = _post_spec(market_client, demo_fixture)
    bids = _post_bids(market_client, demo_fixture, spec["id"])
    first = market_client.post(
        "/api/v1/settle", json={"intentId": spec["id"], "bidId": bids[0]["id"]}
    ).json()
    second = market_client.post(
        "/api/v1/settle", json={"intentId": spec["id"], "bidId": bids[0]["id"]}
    )
    assert second.status_code == 200
    assert second.json()["match"]["id"] == first["match"]["id"]


def test_settle_other_bid_after_match_is_409(market_client, demo_fixture):
    spec = _post_spec(market_client, demo_fixture)
    bids = _post_bids(market_client, demo_fixture, spec["id"])
    market_client.post(
        "/api/v1/settle", json={"intentId": spec["id"], "bidId": bids[0]["id"]}
    )
    resp = market_client.post(
        "/api/v1/settle", json={"intentId": spec["id"], "bidId": bids[1]["id"]}
    )
    assert resp.status_code == 409


def test_settle_mismatched_bid_is_422(market_client, demo_fixture):
    spec_a = _post_spec(market_client, demo_fixture)
    spec_b = _post_spec(market_client, demo_fixture)
    bids_b = _post_bids(market_client, demo_fixture, spec_b["id"])
    resp = market_client.post(
        "/api/v1/settle",
        json={"intentId": spec_a["id"], "bidId": bids_b[0]["id"]},
    )
    assert resp.status_code == 422


def test_settle_missing_records_are_404(market_client):
    assert (
        market_client.post(
            "/api/v1/settle", json={"intentId": "nope", "bidId": "nope"}
        ).status_code
        == 404
    )
