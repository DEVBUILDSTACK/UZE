"""FIDELITY-CHECK AUTHORING SOURCE — codegen criterion 6 (R4 review).

Demo model ONLY — not schema authoring. This file exists to answer one
question before Sprint 0 schema authoring writes OfferSnapshot.payload
per rail: does the reviewed codegen chain

    SQLAlchemy -> bridge (JSON Schema) -> datamodel-code-generator
    -> Pydantic -> model_json_schema() -> json-schema-to-typescript

carry a DISCRIMINATED UNION and OPTIONAL fields at full fidelity?

The case under test is the first one the chain has not met: a JSON column
whose value is one of several per-rail shapes, discriminated by the `rail`
field — exactly the structure R4 specifies for OfferSnapshot.payload.

Design, following the parent round-trip's Price pattern:
- The union is declared HERE, in the authoring source, as the
  `json_schema` fragment on the RailPayloadJSON TypeDecorator. The bridge
  lifts the fragment verbatim into the JSON Schema $defs, so the union
  declaration survives every regeneration and is never edited into a
  generated file.
- Members are inline in the fragment (the bridge lifts ONE fragment per
  column type; it cannot add sibling $defs). Each member carries a
  `title` (its class name downstream), a `const` discriminator value on
  `rail`, `additionalProperties: false` (closed shape), and its own
  required set.
- TicketPayload.gate is the optional field INSIDE a payload member.
- PayloadOwner.note is the optional (nullable) top-level column.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RailPayloadJSON(TypeDecorator):
    """Typed JSON column carrying a DISCRIMINATED UNION schema fragment.

    Two per-rail payload shapes, discriminated by the `rail` property:
      - TicketPayload: rail == "ticket" — seat + tier required, gate optional
      - StayPayload:   rail == "stay"   — phaseKind + nights required

    The `discriminator` keyword is declared in the fragment so the intent
    is in the authoring source; whether the generator chain HONORS it
    (emits a Pydantic discriminator) or drops it (plain union, smart-union
    validation only) is precisely what this fidelity check measures.
    """

    impl = JSON
    cache_ok = True

    json_schema = {
        "title": "RailPayload",
        "discriminator": {"propertyName": "rail"},
        "oneOf": [
            {
                "title": "TicketPayload",
                "type": "object",
                "properties": {
                    "rail": {"const": "ticket"},
                    "seat": {"type": "string"},
                    "tier": {"type": "string"},
                    "gate": {"type": "string"},
                },
                "required": ["rail", "seat", "tier"],
                "additionalProperties": False,
            },
            {
                "title": "StayPayload",
                "type": "object",
                "properties": {
                    "rail": {"const": "stay"},
                    "phaseKind": {"type": "string"},
                    "nights": {"type": "integer"},
                },
                "required": ["rail", "phaseKind", "nights"],
                "additionalProperties": False,
            },
        ],
    }


class PayloadOwner(Base):
    """Fidelity-check carrier model: one discriminated-union payload
    column, one optional column, one optional member field (gate, above).
    """

    __tablename__ = "payload_owner"

    id: Mapped[str] = mapped_column(
        "id", String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    label: Mapped[str] = mapped_column("label", String, nullable=False)
    payload: Mapped[dict] = mapped_column("payload", RailPayloadJSON, nullable=False)
    note: Mapped[str | None] = mapped_column("note", String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
