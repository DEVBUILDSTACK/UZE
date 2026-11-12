"""A2A contribution receipts (mock escrow) — share math + true-up."""
import pytest


def _contribute(client, entity, partner, amount, agent=None):
    resp = client.post(
        "/api/v1/treasury/escrow/contribute",
        json={
            "entity_id": entity,
            "partner_id": partner,
            "agent_id": agent,
            "amount_usdc": amount,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_three_equal_partners_get_third_shares(client):
    entity = "syndicate-equal"
    for partner in ("partner-a", "partner-b", "partner-c"):
        receipt = _contribute(client, entity, partner, 100000, agent=f"agent-{partner}")
    pool = client.get(f"/api/v1/treasury/escrow/{entity}").json()
    assert pool["total_usdc"] == 300000
    shares = {r["partner_id"]: r["share_bps"] for r in pool["receipts"]}
    assert sum(shares.values()) == 10000
    assert sorted(shares.values()) == [3333, 3333, 3334]  # residue to one, stated rule
    assert pool["mock"] is True


def test_receipt_records_share_after_each_contribution(client):
    entity = "syndicate-seq"
    r1 = _contribute(client, entity, "p1", 75000)
    assert r1["share_bps_after"] == 10000
    r2 = _contribute(client, entity, "p2", 25000)
    assert r2["share_bps_after"] == 2500
    assert r2["pool_total_usdc_after"] == 100000


def test_true_up_equal_contributions_to_50_25_25_equity(client):
    entity = "syndicate-trueup"
    for partner in ("partner-a", "partner-b", "partner-c"):
        _contribute(client, entity, partner, 100000)
    resp = client.post(
        f"/api/v1/treasury/escrow/{entity}/true-up",
        json={"equity_bps": {"partner-a": 5000, "partner-b": 2500, "partner-c": 2500}},
    )
    assert resp.status_code == 200, resp.text
    transfers = resp.json()["transfers"]
    # A holds 100k of a 300k pool but should hold 150k: B and C
    # each send A 25k. Net of all transfers = 0; A receives 50k.
    to_a = sum(t["amount_usdc"] for t in transfers if t["to_partner"] == "partner-a")
    from_a = sum(t["amount_usdc"] for t in transfers if t["from_partner"] == "partner-a")
    assert to_a == 50000 and from_a == 0
    assert all(t["executed"] is False for t in transfers)


def test_true_up_equity_must_sum_to_10000(client):
    entity = "syndicate-bad-equity"
    _contribute(client, entity, "p1", 1000)
    resp = client.post(
        f"/api/v1/treasury/escrow/{entity}/true-up",
        json={"equity_bps": {"p1": 9000}},
    )
    assert resp.status_code == 422


def test_unknown_pool_404(client):
    assert client.get("/api/v1/treasury/escrow/nope").status_code == 404
