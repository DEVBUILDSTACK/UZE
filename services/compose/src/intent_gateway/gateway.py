"""Intent Gateway protocol + the scaffold's refusing
implementation (Sprint 2).

The refusing implementation is the point: until Sprint 2 opens
the gateway under the filed decisions, any code that wires a
gateway in gets a loud, named refusal — never a silent accept.
"""
from __future__ import annotations

from typing import Protocol

from .types import GatewayEnvelope, GatewayReceipt


class IntentGatewayNotEnabled(RuntimeError):
    """Raised when a gateway operation is attempted before the
    Sprint 2 gateway is enabled under its filed decisions."""


class IntentGateway(Protocol):
    """The gateway boundary protocol (shape only, Sprint 2)."""

    def submit(self, envelope: GatewayEnvelope) -> GatewayReceipt:
        """Accept or refuse an envelope, explicitly."""
        ...


class DisabledIntentGateway:
    """Scaffold implementation: refuses every envelope."""

    def submit(self, envelope: GatewayEnvelope) -> GatewayReceipt:
        raise IntentGatewayNotEnabled(
            "Intent Gateway is Sprint 2 scaffolding; it is not "
            "enabled and accepts no envelopes "
            f"(refused source={envelope.source!r} kind={envelope.kind!r})"
        )
