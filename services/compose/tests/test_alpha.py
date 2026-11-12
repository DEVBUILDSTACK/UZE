"""Alpha signup list — UZEguidance priced-market levels.

Owner directive 2026-11-12: posted prices removed; the market bids
the levels for UZEBuilder / UZEaffiliate / UZEaffiliate-onramped;
levels honored prospectively only for KYB entities / KYC partner
agents signing up 2026-11-15 00:00 PT – 2027-01-12 22:59 PT.
Storage is the v1 JSONL file (post-demo DB migration deferred).
"""

from datetime import datetime, timezone

import pytest

import alpha


@pytest.fixture(autouse=True)
def _isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ALPHA_SIGNUPS_PATH", str(tmp_path / "signups.jsonl"))
    alpha._signups = None
    yield
    alpha._signups = None


SOL = "4Nd1mPz8kFaWxT9VbGnckdQ8rYyHqXvMpKvJtRZE1w"
SOL2 = "7EcDhSYGxXyscszYEp35KHN8vvw3svAuLKTzXwCFLt"
EVM = "0x1234567890abcdef1234567890abcdef12345678"
NEAR_NAMED = "uzefan.near"
NEAR_IMPLICIT = "a" * 64


def _post(client, **over):
    body = {
        "level": "builder",
        "name": "Ana Agent",
        "email": "ana@example.com",
        "chain": "solana",
        "wallet_address": SOL,
    }
    body.update(over)
    return client.post("/api/v1/alpha/signups", json=body)


def test_signup_each_chain_shape(client):
    r = _post(client)
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["id"].startswith("uze-alpha-")
    assert b["chain"] == "solana"
    # 2026-11-12 (test run date context) is before the window opens;
    # the window state is computed from the real clock, so assert the
    # invariant instead of a fixed value:
    assert b["in_honored_window"] == (b["window_state"] == "in_window")
    assert b["honored"] is False  # no attestation on this signup

    r = _post(client, email="b@example.com", chain="near", wallet_address=NEAR_NAMED)
    assert r.status_code == 200, r.text
    r = _post(client, email="c@example.com", chain="near", wallet_address=NEAR_IMPLICIT)
    assert r.status_code == 200, r.text
    for i, chain in enumerate(("robinhood", "ink", "lightlink")):
        r = _post(
            client,
            email=f"{chain}@example.com",
            chain=chain,
            wallet_address="0x" + "ab" * 19 + f"{i:02x}",
        )
        assert r.status_code == 200, (chain, r.text)


def test_wallet_format_validation(client):
    assert _post(client, wallet_address="0xnotsolana").status_code == 422
    assert _post(client, chain="ink", wallet_address=SOL).status_code == 422
    assert _post(client, chain="near", wallet_address="BAD ADDRESS!!").status_code == 422
    assert _post(client, chain="near", wallet_address="UPPER.near").status_code == 422
    assert _post(client, chain="robinhood", wallet_address=EVM[:-1]).status_code == 422


def test_levels_and_lanes(client):
    r = _post(client, level="affiliate_onramped", email="d@example.com")
    assert r.status_code == 422  # lane required
    r = _post(
        client,
        level="affiliate_onramped",
        email="d@example.com",
        onramp_lane="siglayer",
        kyc_attested=True,
    )
    assert r.status_code == 200, r.text
    assert r.json()["onramp_lane"] == "siglayer"
    assert r.json()["verification_status"] == "attested"
    r = _post(client, level="builder", email="e@example.com", onramp_lane="tradelayer")
    assert r.status_code == 422  # lane only on the onramped level
    assert _post(client, level="partner").status_code == 422
    assert _post(client, chain="bitcoin").status_code == 422
    assert _post(client, email="not-an-email").status_code == 422


def test_duplicate_rules(client):
    assert _post(client).status_code == 200
    r = _post(client)  # exact duplicate -> idempotent
    assert r.status_code == 200 and r.json()["duplicate"] is True
    r = _post(client, email="other@example.com")  # same wallet, other email
    assert r.status_code == 409


def test_window_boundaries():
    inside, state = alpha._window(datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc))
    assert inside is True and state == "in_window"
    inside, state = alpha._window(datetime(2026, 11, 15, 7, 59, tzinfo=timezone.utc))
    assert inside is False and state == "pre_window"  # 23:59 PT Nov 14
    inside, state = alpha._window(datetime(2026, 11, 15, 8, 0, tzinfo=timezone.utc))
    assert inside is True  # exactly opens: 00:00 PT Nov 15
    inside, state = alpha._window(datetime(2027, 1, 13, 6, 59, tzinfo=timezone.utc))
    assert inside is True  # 22:59 PT Jan 12 — last valid minute
    inside, state = alpha._window(datetime(2027, 1, 13, 7, 0, tzinfo=timezone.utc))
    assert inside is False and state == "post_window"  # 23:00 PT Jan 12


def test_honored_requires_window_and_attestation(client):
    # Direct record-logic check with a faked in-window clock is covered
    # by _window tests; here the endpoint invariant: honored implies
    # in-window AND attested.
    r = _post(client, kyb_attested=True, entity_name="Acme LLC", email="f@example.com")
    b = r.json()
    assert b["honored"] == (b["in_honored_window"] and b["kyb_attested"])
    assert b["entity_name"] == "Acme LLC"


def test_count_endpoint(client):
    _post(client)
    _post(client, email="g@example.com", wallet_address=SOL2)
    r = client.get("/api/v1/alpha/signups/count")
    b = r.json()
    assert b["count"] == 2
    assert b["by_chain"]["solana"] == 2
    assert b["window"]["closes_last_valid"].startswith("2027-01-12T22:59:59")
