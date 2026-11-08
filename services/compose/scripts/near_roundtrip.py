"""Live NEAR round trip for Sprint 1.5 Day 2 — the Kitchen-Standard
evidence for the py-near integration: real calls against the deployed
testnet contract, through the same near_client the API uses.

    COMPOSE_NEAR_CHAIN=1 PYTHONPATH=src \
        ~/workspace/tools/composevenv/bin/python scripts/near_roundtrip.py

The Day 1 contract is a stub: post_intent returns "stub_intent_id" and
get_matches returns "[]" for any input. This script asserts exactly
those specified stub values come back from chain — it proves the
transport (keys, RPC, gas, serialization), not business logic, which
is Day 2+'s typed work.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

os.environ.setdefault("COMPOSE_NEAR_CHAIN", "1")

import near_client  # noqa: E402


def main() -> int:
    print(f"contract: {near_client.CONTRACT_ID}  account: {near_client.ACCOUNT_ID}")

    posted = near_client.post_intent(
        {"specId": "roundtrip-check", "microRegionId": "miami-brickell"}
    )
    print("post_intent ->", json.dumps(posted))
    assert posted["status"] == "submitted", posted
    assert posted["result"] == "stub_intent_id", posted

    bid = near_client.submit_bid(
        "stub_intent_id", {"bidId": "roundtrip-check", "amountUsdc": 4200}
    )
    print("submit_bid  ->", json.dumps(bid))
    assert bid["status"] == "submitted", bid
    assert bid["result"] == "stub_bid_id", bid

    matches = near_client.get_matches("stub_intent_id")
    print("get_matches ->", json.dumps(matches))
    assert matches["status"] == "submitted", matches
    # The scaffold returns the String "[]" (see 01-PICKUP-TONIGHT); the
    # view path surfaces it as that string — parse before comparing.
    parsed = (
        json.loads(matches["result"])
        if isinstance(matches["result"], str)
        else matches["result"]
    )
    assert parsed == [], matches

    print("ROUND TRIP OK: post_intent, submit_bid, get_matches all answered on-chain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
