"""Trust-layer references on the Intent (James's stack
clarification, 2026-11-08; audit in docs/audit/).

The Intent now carries the Assurative V2 linkage: entityId /
affiliateId as string-carried UUIDs (cross-database references are
plain strings, never FKs — Scope Tenet 01 + the R4 rule), the
execution environment, and the poster's attestation kind. These
tests pin the round-trip, the null defaults for specs that predate
the linkage, and enum validation at the wire.
"""

from __future__ import annotations

import copy

ENTITY_ID = "a380c150-1fb9-49fb-992a-1e3b89593472"
AFFILIATE_ID = "b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e"


def _spec(fixture, **overrides) -> dict:
    body = copy.deepcopy(fixture["spec"])
    body.pop("posterLabel", None)
    for key in ("entityId", "affiliateId", "executionEnvironment",
                "agentAttestation"):
        body.pop(key, None)
    body.update(overrides)
    return body


def test_trust_layer_references_round_trip(market_client, demo_fixture):
    r = market_client.post("/api/v1/specs", json=_spec(
        demo_fixture,
        entityId=ENTITY_ID,
        affiliateId=AFFILIATE_ID,
        executionEnvironment="arcium_auction",
        agentAttestation="agent_x401",
    ))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["entityId"] == ENTITY_ID
    assert body["affiliateId"] == AFFILIATE_ID
    assert body["executionEnvironment"] == "arcium_auction"
    assert body["agentAttestation"] == "agent_x401"

    view = market_client.get(f"/api/v1/specs/{body['id']}").json()
    assert view["entityId"] == ENTITY_ID
    assert view["executionEnvironment"] == "arcium_auction"


def test_demo_fixture_carries_the_syndicate_entity(market_client, demo_fixture):
    # The filed demo: the syndicate is an Entity, posting as a
    # human-attested party, executing via NEAR intents.
    body = copy.deepcopy(demo_fixture["spec"])
    body.pop("posterLabel", None)
    r = market_client.post("/api/v1/specs", json=body)
    assert r.status_code == 201, r.text
    assert r.json()["entityId"] == ENTITY_ID
    assert r.json()["executionEnvironment"] == "near_intents"
    assert r.json()["agentAttestation"] == "human"
    assert r.json()["affiliateId"] is None


def test_unlinked_spec_defaults_to_null(market_client, demo_fixture):
    r = market_client.post("/api/v1/specs", json=_spec(demo_fixture))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["entityId"] is None
    assert body["affiliateId"] is None
    assert body["executionEnvironment"] is None
    assert body["agentAttestation"] is None


def test_invalid_execution_environment_is_422(market_client, demo_fixture):
    r = market_client.post("/api/v1/specs", json=_spec(
        demo_fixture, executionEnvironment="solana_direct"))
    assert r.status_code == 422, r.text
