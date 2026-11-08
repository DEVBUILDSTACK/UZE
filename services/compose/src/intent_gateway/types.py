"""Gateway envelope/receipt shapes (Sprint 2 scaffold).

Boundary law carried over from the filed architecture:
- references to anything outside this database are plain strings
  (``external_ref``), never foreign keys (R4 §8);
- an envelope *proposes* an intent — acceptance is a separate,
  explicit gateway decision, never a side effect of arrival.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GatewayEnvelope:
    """An intent crossing (or proposing to cross) the gateway."""

    source: str  # e.g. "solver", "partner-webhook", "near-intents"
    external_ref: str  # the source system's id — a string reference
    kind: str  # intent kind, e.g. "spec" / "bid" / "quote"
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GatewayReceipt:
    """The gateway's explicit answer to an envelope."""

    accepted: bool
    gateway_ref: str | None  # compose-side id when accepted
    reason: str  # machine-readable refusal/acceptance reason
