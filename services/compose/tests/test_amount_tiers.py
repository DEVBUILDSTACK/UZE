"""Three-tier amount compliance (owner's tap 2026-11-11) —
exact boundaries, tier requirements, and the endpoint."""
import metering

IDENTITY = {
    "subject": "agent-sura",
    "credentialType": "x401-agent",
    "attestation": "mock-attestation",
}
LINKED = {**IDENTITY, "entityId": "entity-456"}


def test_boundaries_are_exact():
    assert metering.classify_amount_tier(0.10) == 1
    assert metering.classify_amount_tier(29.99) == 1
    assert metering.classify_amount_tier(29.999) == 1
    assert metering.classify_amount_tier(30.00) == 2
    assert metering.classify_amount_tier(199.99) == 2
    assert metering.classify_amount_tier(200.00) == 3
    assert metering.classify_amount_tier(500_000) == 3


def test_tier1_needs_no_identity():
    allowed, status, detail = metering.enforce_amount_tier(10.0)
    assert allowed and status == 200 and detail["tier"] == 1


def test_tier2_requires_entity_linked_identity():
    allowed, status, _ = metering.enforce_amount_tier(100.0)
    assert not allowed and status == 401
    # identity present but NOT tied to an Entity -> still 401
    allowed, status, detail = metering.enforce_amount_tier(100.0, IDENTITY)
    assert not allowed and status == 401
    assert "entity-link" in detail["requirements"]
    allowed, status, detail = metering.enforce_amount_tier(100.0, LINKED)
    assert allowed and status == 200 and detail["entity_id"] == "entity-456"


def test_tier3_requires_kyb():
    allowed, status, _ = metering.enforce_amount_tier(250.0, LINKED)
    assert not allowed and status == 403
    allowed, status, _ = metering.enforce_amount_tier(250.0, LINKED, entity_kyb=True)
    assert allowed and status == 200


def test_tier_check_endpoint(client):
    r = client.post("/api/v1/metering/tier-check", json={"amount_usd": 29.99})
    assert r.status_code == 200 and r.json()["tier"] == 1
    r = client.post("/api/v1/metering/tier-check", json={"amount_usd": 30.00})
    assert r.status_code == 401
    r = client.post(
        "/api/v1/metering/tier-check",
        json={"amount_usd": 199.99, "identity": LINKED},
    )
    assert r.status_code == 200 and r.json()["tier"] == 2
    r = client.post(
        "/api/v1/metering/tier-check",
        json={"amount_usd": 200.00, "identity": LINKED},
    )
    assert r.status_code == 403
    r = client.post(
        "/api/v1/metering/tier-check",
        json={"amount_usd": 200.00, "identity": LINKED, "entity_kyb": True},
    )
    assert r.status_code == 200 and r.json()["tier"] == 3
