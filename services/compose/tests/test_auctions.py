"""Commitment Ladder + Arcium auction mock (owner's tap
2026-11-11): ladder math, whitelist discipline, sealed bids,
and the human-Execute Temporal Trigger."""

CLOSE = "2026-12-20T00:00:00Z"


def _create(client, target=1_000_000):
    r = client.post(
        "/api/v1/assign/auctions",
        json={
            "entity_id": "entity-456",
            "title": "Harbor portfolio",
            "target_bid_usdc": target,
            "close_at": CLOSE,
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_ladder_schedule_math(client):
    a = _create(client)
    ladder = {cp["pct"]: cp for cp in a["ladder"]}
    assert ladder[30]["amount_usdc"] == 300_000
    assert ladder[90]["amount_usdc"] == 900_000
    assert ladder[100]["amount_usdc"] == 1_000_000
    assert ladder[30]["due_at"].startswith("2026-12-13")  # T-7 days
    assert ladder[90]["due_at"].startswith("2026-12-17")  # T-72 hours
    assert ladder[100]["due_at"].startswith("2026-12-19")  # T-12 hours


def test_under_locked_partner_falls_off_whitelist(client):
    a = _create(client)
    aid = a["auction_id"]
    client.post(f"/api/v1/assign/auctions/{aid}/lock",
                json={"partner_id": "partner-full", "amount_usdc": 400_000})
    client.post(f"/api/v1/assign/auctions/{aid}/lock",
                json={"partner_id": "partner-light", "amount_usdc": 100_000})
    # T-6 days: the 30% checkpoint is due; 10% locked is not enough
    r = client.post(f"/api/v1/assign/auctions/{aid}/evaluate",
                    json={"now": "2026-12-14T00:00:00Z"})
    view = r.json()
    assert view["due_pct"] == 30
    assert "partner-full" in view["whitelist"]
    assert "partner-light" in view["removed"]


def test_sealed_bids_and_human_execute_gate(client):
    a = _create(client)
    aid = a["auction_id"]
    client.post(f"/api/v1/assign/auctions/{aid}/bids",
                json={"partner_id": "partner-a", "amount_usdc": 950_000})
    client.post(f"/api/v1/assign/auctions/{aid}/bids",
                json={"partner_id": "partner-b", "amount_usdc": 1_050_000})
    view = client.get(f"/api/v1/assign/auctions/{aid}").json()
    assert view["bid_count"] == 2
    assert "result" not in view  # nothing revealed while open

    closed = client.post(f"/api/v1/assign/auctions/{aid}/close").json()
    assert closed["status"] == "READY_TO_EXECUTE"
    assert closed["executed"] is False  # trigger locks + alerts only
    assert closed["alerts"][0]["type"] == "READY_TO_EXECUTE"

    r = client.post(f"/api/v1/assign/auctions/{aid}/execute",
                    json={"human_confirmed": False})
    assert r.status_code == 422  # no auto-execution, ever
    r = client.post(f"/api/v1/assign/auctions/{aid}/execute",
                    json={"human_confirmed": True})
    body = r.json()
    assert body["status"] == "EXECUTED_MOCK"
    assert body["result"]["winner"] == "partner-b"
    assert body["result"]["winning_bid_usdc"] == 1_050_000
