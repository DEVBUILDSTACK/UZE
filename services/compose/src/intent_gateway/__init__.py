"""Intent Gateway — Sprint 2 scaffold (NOT wired into the app).

The Intent Gateway is the Sprint 2 boundary at which external
and solver-originated intents enter the compose marketplace. This
package is scaffolding only: it fixes the envelope/receipt shapes
and the gateway protocol so Sprint 2 builds against a stable
surface, and its only implementation refuses everything.

Both directing questions were RESOLVED by DeepSeek on
2026-11-08 (relayed by James); the resolutions are recorded in
the gateway module docstring and this package's README:
  Q-1  The gateway stays a distinct Python package inside
       services/compose — no separate microservice unless
       solver-matching load requires independent scaling.
  Q-2  Solver quotes inherit R4's TTL and commit-time
       reconciliation wholesale, plus one distinct divergence
       code: SOLVER_WITHDREW (a quote expiring or being pulled
       is a failed negotiation, not vanished inventory).

Nothing in services/compose imports this package yet.
"""
from __future__ import annotations

from .gateway import DisabledIntentGateway, IntentGateway, IntentGatewayNotEnabled
from .types import GatewayEnvelope, GatewayReceipt

__all__ = [
    "DisabledIntentGateway",
    "GatewayEnvelope",
    "GatewayReceipt",
    "IntentGateway",
    "IntentGatewayNotEnabled",
]
