"""Intent Gateway scaffold pins (Sprint 2 scaffolding, 2026-11-08).

The scaffold's contract is refusal: the gateway is not enabled,
accepts nothing, and is not wired into the app. These tests keep
it that way until Sprint 2 opens it under the filed decisions.
"""

from __future__ import annotations

import pytest

from intent_gateway import (
    DisabledIntentGateway,
    GatewayEnvelope,
    IntentGatewayNotEnabled,
)


def test_envelope_carries_string_external_ref():
    env = GatewayEnvelope(
        source="solver",
        external_ref="solver-intent-123",
        kind="quote",
        payload={"amountUsdc": 100},
    )
    assert env.external_ref == "solver-intent-123"
    assert env.kind == "quote"


def test_disabled_gateway_refuses_everything():
    gateway = DisabledIntentGateway()
    with pytest.raises(IntentGatewayNotEnabled):
        gateway.submit(
            GatewayEnvelope(source="solver", external_ref="x", kind="spec")
        )


def test_gateway_is_not_wired_into_the_app(market_client):
    from app import create_app

    paths = {route.path for route in create_app().routes}
    assert not any("gateway" in path for path in paths)
