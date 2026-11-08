"""Intent Gateway — Sprint 2 scaffold (NOT wired into the app).

The Intent Gateway is the Sprint 2 boundary at which external
and solver-originated intents enter the compose marketplace. This
package is scaffolding only: it fixes the envelope/receipt shapes
and the gateway protocol so Sprint 2 builds against a stable
surface, and its only implementation refuses everything.

Two directing questions remain open for DeepSeek/James and are
deliberately NOT decided here (filed 2026-11-07, scope v0.3):
  Q-1  Where exactly the gateway boundary sits (which intent
       kinds cross it, and in which direction).
  Q-2  Whether solver quotes inherit the R4 read-through
       contract wholesale or a gateway-specific subset.

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
