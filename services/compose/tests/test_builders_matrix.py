"""UZE Builder registration (mock) + Yield Matrix endpoints
(mock over a synthetic snapshot). Owner's tap 2026-11-11."""


def test_builder_register_email_and_wallet_only(client):
    r = client.post(
        "/api/v1/treasury/sub-builder/register",
        json={"email": "Agent@Example.com", "x401_wallet_address": "wallet-abc-123"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["lane"] == "UZE_BUILDER"
    assert body["entity_id"] is None
    assert body["kyb_required"] is False
    assert body["email"] == "agent@example.com"
    assert "Compute Credits" in body["welcome"]
    assert "NEAR" not in body["welcome"]  # opaque: source never named
    # idempotent re-register
    r2 = client.post(
        "/api/v1/treasury/sub-builder/register",
        json={"email": "agent@example.com", "x401_wallet_address": "wallet-abc-123"},
    )
    assert r2.json()["existing"] is True
    got = client.get(f"/api/v1/treasury/sub-builder/{body['builder_id']}")
    assert got.status_code == 200


def test_builder_register_validation(client):
    r = client.post(
        "/api/v1/treasury/sub-builder/register",
        json={"email": "not-an-email", "x401_wallet_address": "wallet-abc-123"},
    )
    assert r.status_code == 422
    r = client.post(
        "/api/v1/treasury/sub-builder/register",
        json={"email": "a@b.co", "x401_wallet_address": "x"},
    )
    assert r.status_code == 422


def test_matrix_subscribe_and_preferred(client):
    r = client.post(
        "/api/v1/matrix/subscribe",
        json={"email": "lead@example.com", "phone_number": "+1-555-0100"},
    )
    assert r.status_code == 200 and r.json()["subscribed"] is True
    r = client.post("/api/v1/matrix/subscribe", json={"email": "nope"})
    assert r.status_code == 422
    r = client.get("/api/v1/matrix/preferred-yield")
    body = r.json()
    assert body["synthetic"] is True and body["mock"] is True
    assert body["route"]["provider"] == body["preferred"]["protocol_name"]
    names = {row["protocol_name"] for row in body["snapshot"]}
    assert names == {"NEAR AI", "Venice", "Arcium", "Phala"}
    # synthetic figures are labelled, never presented as yields
    assert all(row["monthly_yield_usd"] == 0.0 for row in body["snapshot"])
