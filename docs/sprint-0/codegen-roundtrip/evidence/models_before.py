"""SINGLE AUTHORING SOURCE — UZEMARKETS composition layer, Sprint 0 gate demo.

This file is the ONLY hand-authored model. Everything downstream
(JSON Schema, Pydantic, TypeScript) is GENERATED from it by `make all`
(see Makefile). Hand-editing a generated artifact breaks the gate.

Model: OfferSnapshot, field shape taken faithfully from
docs/UZEMARKETS-DATA-FIRST-BUILD-PLAN-IMPORTED-DRAFT-v0.1.md:

    model OfferSnapshot {
      id              String          @id @default(uuid())
      tripCandidateId String
      rail            Rail
      sourceRef       String          // supplier-side id
      commitmentClass CommitmentClass
      price           Json            // { amount, currency, taxesIncluded }
      terms           Json            // cancellation window, transfer policy, date-shift rights
      payload         Json            // rail-specific normalized body
      expiresAt       DateTime
      createdAt       DateTime        @default(now())
      @@index([tripCandidateId, rail])
      @@index([expiresAt])
    }
    enum Rail            { SOLANA_NFT HOTEL_AGGREGATOR FLIGHT_SEARCH FACILITY PARKING TRANSFER DINING_TASK }
    enum CommitmentClass { IRREVERSIBLE_ON_CHAIN CANCELLABLE_UNTIL_WINDOW CHANGEABLE_WITH_FEE APPOINTMENT MEDICAL_PACKAGE }

Demo-scope notes:
- tripCandidateId is a plain indexed column here; the FK to TripCandidate is
  wired when the full schema is authored in Sprint 0 proper (single-table
  demo subset — see README).
- Attribute names are snake_case in Python; the DB/contract names are the
  spec's camelCase, set explicitly as the column names. The codegen bridge
  emits contract (camelCase) names into the JSON Schema.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum as SAEnum, Index, String, TypeDecorator, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Rail(enum.Enum):
    SOLANA_NFT = "SOLANA_NFT"
    HOTEL_AGGREGATOR = "HOTEL_AGGREGATOR"
    FLIGHT_SEARCH = "FLIGHT_SEARCH"
    FACILITY = "FACILITY"
    PARKING = "PARKING"
    TRANSFER = "TRANSFER"
    DINING_TASK = "DINING_TASK"


class CommitmentClass(enum.Enum):
    IRREVERSIBLE_ON_CHAIN = "IRREVERSIBLE_ON_CHAIN"
    CANCELLABLE_UNTIL_WINDOW = "CANCELLABLE_UNTIL_WINDOW"
    CHANGEABLE_WITH_FEE = "CHANGEABLE_WITH_FEE"
    APPOINTMENT = "APPOINTMENT"
    MEDICAL_PACKAGE = "MEDICAL_PACKAGE"


class PriceJSON(TypeDecorator):
    """Typed JSON column: the JSON Schema fragment for the frozen price
    structure is declared HERE, in the authoring source, on the type itself.

    The codegen bridge lifts `json_schema` verbatim into the JSON Schema
    $defs, so datamodel-code-generator emits a real nested Pydantic model
    (Price) instead of Any/dict. Because the fragment lives on the SQLAlchemy
    type, it survives every regeneration — it is never edited into a
    generated file. This is the typed-JSON mechanism for the whole schema:
    any JSON column that needs a typed projection gets a TypeDecorator
    carrying its fragment; free-form JSON columns (terms, payload) stay
    plain JSON by design.
    """

    impl = JSON
    cache_ok = True

    json_schema = {
        "title": "Price",
        "type": "object",
        "properties": {
            "amount": {"type": "number"},
            "currency": {"type": "string"},
            "taxesIncluded": {"type": "boolean"},
        },
        "required": ["amount", "currency", "taxesIncluded"],
        "additionalProperties": False,
    }


class OfferSnapshot(Base):
    """A quoted offer with price and terms frozen at quote time.

    Semantically IMMUTABLE: a snapshot is written once and never updated or
    deleted (a changed quote is a new snapshot). Enforced at three levels:
      1. ORM — the before_update / before_delete guards below raise on any
         attempted mutation flush (demonstrated in validate_roundtrip.py).
      2. DB — see README for the Postgres trigger note (belt-and-braces for
         writers that bypass the ORM).
      3. API types — the generated Pydantic model is frozen
         (see base.py / generated offersnapshot_pydantic.py).
    """

    __tablename__ = "offer_snapshot"

    id: Mapped[str] = mapped_column(
        "id", String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_candidate_id: Mapped[str] = mapped_column("tripCandidateId", String, nullable=False)
    rail: Mapped[Rail] = mapped_column("rail", SAEnum(Rail, name="rail"), nullable=False)
    source_ref: Mapped[str] = mapped_column("sourceRef", String, nullable=False)
    commitment_class: Mapped[CommitmentClass] = mapped_column(
        "commitmentClass", SAEnum(CommitmentClass, name="commitment_class"), nullable=False
    )
    price: Mapped[dict] = mapped_column("price", PriceJSON, nullable=False)
    terms: Mapped[dict] = mapped_column("terms", JSON, nullable=False)
    payload: Mapped[dict] = mapped_column("payload", JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column("expiresAt", DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_offer_snapshot_trip_rail", "tripCandidateId", "rail"),
        Index("ix_offer_snapshot_expires", "expiresAt"),
    )


# --- Immutability guard (ORM level) ---------------------------------------
# OfferSnapshot rows are insert-only. Any UPDATE or DELETE flush attempt —
# from any code path using this metadata — raises instead of writing.

@event.listens_for(OfferSnapshot, "before_update")
def _offer_snapshot_no_update(mapper, connection, target):
    raise RuntimeError(
        "OfferSnapshot is immutable: UPDATE refused. A changed quote is a new snapshot."
    )


@event.listens_for(OfferSnapshot, "before_delete")
def _offer_snapshot_no_delete(mapper, connection, target):
    raise RuntimeError("OfferSnapshot is immutable: DELETE refused (append-only record).")
