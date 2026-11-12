"""Intent Gateway protocol + the scaffold's refusing
implementation (Sprint 2).

The refusing implementation is the point: until Sprint 2 opens
the gateway under the filed decisions, any code that wires a
gateway in gets a loud, named refusal — never a silent accept.

Directing resolutions (DeepSeek, 2026-11-08, relayed by James):

Q-1 — Boundary: the gateway stays a distinct Python package
inside services/compose (this package). It is NOT split into a
separate microservice: it shares the database and the R4 state
machine with the rest of Compose. Extraction to a separate
service happens only if solver-matching load requires
independent scaling.

Q-2 — R4 inheritance: solver quotes inherit R4's TTL and
commit-time reconciliation discipline wholesale, with ONE
distinct divergence code added: SOLVER_WITHDREW. A solver quote
expiring or being pulled is structurally different from a
static LISTING_GONE — the negotiation failed; the inventory
didn't vanish. SOLVER_WITHDREW is recorded here as the Sprint 2
code to implement when the gateway is wired; it is not part of
the Sprint 1 read-through code set.
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
    """Scaffold implementation: refuses every envelope.

    Stays the only implementation until Sprint 2 wires the
    gateway under the 2026-11-08 resolutions: in-package inside
    services/compose (Q-1), solver quotes reconciled under R4
    with the SOLVER_WITHDREW divergence code (Q-2).
    """

    def submit(self, envelope: GatewayEnvelope) -> GatewayReceipt:
        raise IntentGatewayNotEnabled(
            "Intent Gateway is Sprint 2 scaffolding; it is not "
            "enabled and accepts no envelopes "
            f"(refused source={envelope.source!r} kind={envelope.kind!r})"
        )
