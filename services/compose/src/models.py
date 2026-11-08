"""SINGLE AUTHORING SOURCE — UZEMARKETS composition layer schema (Sprint 0).

This file is the ONLY hand-authored model set for the composition layer
(database `uzemarkets-compose`). Everything downstream (JSON Schema,
Pydantic, TypeScript) is GENERATED from it by `make all` (see Makefile).
Hand-editing a generated artifact is dual authoring and breaks the gate.

Authored under: James's ratification of 2026-10-30 (ORM (C) — SQLAlchemy
+ Alembic end-to-end), the Data-First build plan §4.1 (imported spec,
docs/UZEMARKETS-DATA-FIRST-BUILD-PLAN-IMPORTED-DRAFT-v0.1.md), the scope
consolidation's full data model (QuestionManifest, ServiceTask family,
ConciergeBrief), and the Read-Through Contract R4 DRAFT v0.2 (boundary
law: sourceRef is a reference, never a FK; divergence codes are a typed
enum; OfferSnapshot.payload carries per-rail structure + seat identity).

Conventions (from the reviewed round-trip, docs/sprint-0/codegen-roundtrip):
- Attribute names are snake_case; DB/contract names are the spec's
  camelCase, set explicitly as the column names. The codegen bridge emits
  contract (camelCase) names into the JSON Schema.
- Typed JSON columns carry their JSON Schema fragment on a TypeDecorator
  in THIS file (PriceJSON, OfferPayloadJSON, QuestionSlotListJSON), so the typed projection
  survives every regeneration. Free-form JSON columns stay plain JSON by
  design (terms, criteria, summaries, briefs).
- Internal ownership FKs (Traveler -> TripProfile, etc.) are real foreign
  keys inside this one database. References OUT of this database —
  OfferSnapshot.sourceRef above all — are plain strings, never FKs
  (R4 §8: reference, never own; no cross-database joins, ever).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    ARRAY,
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    TypeDecorator,
    event,
    inspect as sa_inspect,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from config import RESTRICTED_SCHEMA


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums — complete, including dormant members (spec §4.1). Do not remove
# "unused" members: the health members exist in Sprint 0 precisely so the
# month 4–5 vertical needs no enum migration.
# ---------------------------------------------------------------------------


class GeoAnchorType(enum.Enum):
    VENUE = "VENUE"
    FACILITY = "FACILITY"
    ADDRESS = "ADDRESS"
    METRO = "METRO"


class TravelerRole(enum.Enum):
    PATIENT = "PATIENT"
    COMPANION = "COMPANION"
    PRIMARY = "PRIMARY"
    GUEST = "GUEST"


class StayPhaseKind(enum.Enum):
    PRE_EVENT = "PRE_EVENT"
    EVENT = "EVENT"
    POST_EVENT = "POST_EVENT"
    PRE_OP = "PRE_OP"
    INPATIENT = "INPATIENT"
    RECOVERY = "RECOVERY"


class ModuleType(enum.Enum):
    TICKETS = "TICKETS"
    STAY = "STAY"
    FLIGHT = "FLIGHT"
    PARKING = "PARKING"
    TRANSIT = "TRANSIT"
    DINING = "DINING"
    TRANSFER = "TRANSFER"
    VIP_CONCIERGE = "VIP_CONCIERGE"
    FACILITY = "FACILITY"


class CommitmentClass(enum.Enum):
    IRREVERSIBLE_ON_CHAIN = "IRREVERSIBLE_ON_CHAIN"
    CANCELLABLE_UNTIL_WINDOW = "CANCELLABLE_UNTIL_WINDOW"
    CHANGEABLE_WITH_FEE = "CHANGEABLE_WITH_FEE"
    APPOINTMENT = "APPOINTMENT"  # dormant until the health vertical
    MEDICAL_PACKAGE = "MEDICAL_PACKAGE"  # dormant until the health vertical


class Rail(enum.Enum):
    SOLANA_NFT = "SOLANA_NFT"
    HOTEL_AGGREGATOR = "HOTEL_AGGREGATOR"
    FLIGHT_SEARCH = "FLIGHT_SEARCH"
    FACILITY = "FACILITY"  # dormant until the health vertical
    PARKING = "PARKING"
    TRANSFER = "TRANSFER"
    DINING_TASK = "DINING_TASK"


class OfferKind(enum.Enum):
    """The OfferSnapshot payload DISCRIMINATOR (James's tap (c),
    2026-10-30, resolving the schema review's substantive finding).

    Rail is the routing/dispatch vocabulary — it includes DINING_TASK,
    a task rail that produces no offer. While the payload union was
    keyed on Rail, DINING_TASK sat in the offer union as a dead
    branch. The split: OfferKind names exactly the rails that can
    produce an OfferSnapshot, the payload's tag property is `kind`,
    and its values are THIS enum's values. Rail is retained for
    routing and dispatch (the snapshot's `rail` column, EventLog
    routing, the task family) and is no longer the offer
    discriminator. Not a column enum: OfferKind lives in the payload
    tag, in the generated union, and in the DB CHECK that revision
    b3d91c7e5a02 puts on offer_snapshot.
    """

    TICKET = "ticket"
    STAY = "stay"
    FLIGHT = "flight"
    FACILITY = "facility"  # dormant until the health vertical
    PARKING = "parking"
    TRANSFER = "transfer"


_RAIL_TO_OFFER_KIND: dict[Rail, "OfferKind | None"] = {
    Rail.SOLANA_NFT: OfferKind.TICKET,
    Rail.HOTEL_AGGREGATOR: OfferKind.STAY,
    Rail.FLIGHT_SEARCH: OfferKind.FLIGHT,
    Rail.FACILITY: OfferKind.FACILITY,
    Rail.PARKING: OfferKind.PARKING,
    Rail.TRANSFER: OfferKind.TRANSFER,
    Rail.DINING_TASK: None,  # a task rail produces no offer — the point of the split
}


def offer_kind_for_rail(rail: Rail) -> "OfferKind | None":
    """The ONE mapping between Rail (routing/dispatch) and OfferKind
    (the offer discriminator). Every Rail member is present in the
    table — a missing member is a loud KeyError, not a silent None.
    DINING_TASK maps to None by design: it dispatches tasks and can
    never produce an OfferSnapshot."""
    return _RAIL_TO_OFFER_KIND[rail]


class TaskState(enum.Enum):
    """ServiceTask family state machine (spec §4.1; consolidation):
    REQUESTED -> QUOTED -> DEPOSIT_PENDING -> CONFIRMED, with FAILED and
    CANCELLED as terminal exits from any state."""

    REQUESTED = "REQUESTED"
    QUOTED = "QUOTED"
    DEPOSIT_PENDING = "DEPOSIT_PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DivergenceCode(enum.Enum):
    """R4 §5 typed divergence codes (DRAFT v0.2 — eight codes).

    Recorded on the OfferSnapshot that a divergence kills for commit
    (the one permitted post-insert write — see the immutability guard)
    and in EventLog. The EventLog entry is authoritative; the column
    is its derived projection, written atomically by the mirror
    trigger — the exception's three ratified terms are named in the
    OfferSnapshot docstring. Never free-text (criterion 9).
    """

    SNAPSHOT_EXPIRED = "SNAPSHOT_EXPIRED"
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    LISTING_GONE = "LISTING_GONE"
    TICKET_TRANSFERRED = "TICKET_TRANSFERRED"
    TICKET_REDEEMED = "TICKET_REDEEMED"
    SEAT_TAKEN = "SEAT_TAKEN"
    PRICE_MOVED = "PRICE_MOVED"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"


class QuestionSlotType(enum.Enum):
    """The QuestionSlot `type` vocabulary (James's tap (a), 2026-10-30).

    Not a column enum: it lives in the QuestionSlot fragment (the
    slot union's two members split on ENUM — see QuestionSlotListJSON)
    and in revision d52f8b1a904c's validation trigger.
    """

    STRING = "STRING"
    INT = "INT"
    DATE = "DATE"
    BOOL = "BOOL"
    ENUM = "ENUM"
    OBJECT = "OBJECT"
    ARRAY = "ARRAY"


# ---------------------------------------------------------------------------
# Typed JSON columns. The schema fragment lives HERE, on the type; the
# codegen bridge lifts it verbatim into $defs.
# ---------------------------------------------------------------------------


class PriceJSON(TypeDecorator):
    """OfferSnapshot.price — { amount, currency, taxesIncluded }, frozen
    at quote time. (Mechanism as reviewed in the round-trip gate.)

    INVARIANT (2026-11-01, DeepSeek direction relayed by James):
    currency is USDC and only USDC — USDC on Solana is the sole
    commerce settlement rail. The enum below is the enforcement: the
    generated Pydantic Price model rejects any other currency at
    validation, on every write path through the compose layer. UZE is
    a unit of measurement/attribution, never a settlement currency;
    UZD is an incentive token, never a payment method. A non-USDC
    value here is a defect, not a feature."""

    impl = JSON
    cache_ok = True

    json_schema = {
        "title": "Price",
        "type": "object",
        "properties": {
            "amount": {"type": "number"},
            "currency": {"type": "string", "enum": ["USDC"]},
            "taxesIncluded": {"type": "boolean"},
        },
        "required": ["amount", "currency", "taxesIncluded"],
        "additionalProperties": False,
    }


def _offer_member(
    kind: OfferKind, properties: dict, required: list[str]
) -> dict:
    """One OfferPayload union member for `kind`, titled <Kind>OfferDetail.

    The tag is the payload-local `kind` property, const-bound to the
    OfferKind value; the member title is what the generated Pydantic +
    TypeScript classes are named (James's tap (c): union member names
    match OfferKind — the chain's --use-title-as-name flag, adopted
    with this change, is what carries the titles into the artifacts).
    """
    return {
        "title": f"{kind.name.title()}OfferDetail",
        "type": "object",
        "properties": {"kind": {"const": kind.value}, **properties},
        "required": ["kind", *required],
        "additionalProperties": False,
    }


class OfferPayloadJSON(TypeDecorator):
    """OfferSnapshot.payload — the per-kind normalized body, as a
    DISCRIMINATED UNION keyed on the payload's own `kind` tag, whose
    values are the OfferKind enum (James's tap (c), 2026-10-30).

    Mechanism proven by the criterion-6 fidelity check
    (docs/sprint-0/codegen-roundtrip/fidelity/): the fragment declares
    oneOf + discriminator + const member tags in the authoring source;
    the generated Pydantic dispatches on the tag, so a payload whose
    shape matches one member but whose tag names another is rejected.

    HISTORY OF THE SPLIT: this union was previously keyed on Rail
    (tag property `rail`, members TicketPayload…DiningPayload). The
    schema review found the flaw: DINING_TASK is a task rail, not an
    offer, and sat in the offer union as a dead branch. As tapped:
    OfferKind is the discriminator; Rail is retained for routing and
    dispatch only; the ONE mapping between them is
    offer_kind_for_rail() (DINING_TASK -> None); the Dining member is
    deleted — a dining task produces no offer. At the DB level,
    revision b3d91c7e5a02 adds CHECK ck_offer_snapshot_payload_kind,
    so a raw-SQL writer cannot store an out-of-set kind tag either.

    Member shapes are NARROW and closed (additionalProperties: false).
    Only the ticket member's core is ratified content (seat identity +
    Solana mint reference in payload — James's tap; R4 §6 compares seat
    assignment, approval snapshot, and mint reference out of payload).
    The remaining members carry the minimum binding identifiers for
    their kind, re-homed unchanged from the former rail members;
    every field beyond the spec's own words is an AUTHOR'S CHOICE,
    listed in SCHEMA-NOTES.md. FacilityOfferDetail is dormant,
    consistent with the dormant discipline.
    """

    impl = JSON
    cache_ok = True

    json_schema = {
        "title": "OfferPayload",
        "discriminator": {"propertyName": "kind"},
        "oneOf": [
            _offer_member(
                OfferKind.TICKET,
                {
                    "seat": {"type": "string"},
                    "tier": {"type": "string"},
                    "gate": {"type": "string"},
                    "mintRef": {"type": "string"},
                    "ticketRef": {"type": "string"},
                    "listingRef": {"type": "string"},
                },
                ["seat", "tier"],
            ),
            _offer_member(
                OfferKind.STAY,
                {
                    "phaseKind": {"type": "string"},
                    "nights": {"type": "integer"},
                    "propertyRef": {"type": "string"},
                },
                ["phaseKind", "nights"],
            ),
            _offer_member(
                OfferKind.FLIGHT,
                {
                    "itineraryRef": {"type": "string"},
                    "carrier": {"type": "string"},
                    "departAt": {"type": "string", "format": "date-time"},
                },
                ["itineraryRef"],
            ),
            _offer_member(
                OfferKind.FACILITY,
                {
                    "facilityRef": {"type": "string"},
                    "packageRef": {"type": "string"},
                    "procedureClassBand": {"type": "string"},
                },
                ["facilityRef", "packageRef"],
            ),
            _offer_member(
                OfferKind.PARKING,
                {
                    "anchorRef": {"type": "string"},
                    "spotRef": {"type": "string"},
                },
                ["anchorRef"],
            ),
            _offer_member(
                OfferKind.TRANSFER,
                {
                    "taskRef": {"type": "string"},
                    "pickupAt": {"type": "string", "format": "date-time"},
                },
                ["taskRef"],
            ),
        ],
    }


def _question_slot(*, enum_member: bool) -> dict:
    """One member of the QuestionSlot union (see QuestionSlotListJSON).

    The two members share every field except the pair the tap's one
    conditional rule turns on: `type` and `enumValues`.
    """
    properties: dict = {
        "key": {"type": "string"},
        "type": (
            {"const": QuestionSlotType.ENUM.value}
            if enum_member
            else {
                "title": "QuestionSlotType",
                "type": "string",
                "enum": [
                    m.value
                    for m in QuestionSlotType
                    if m is not QuestionSlotType.ENUM
                ],
            }
        ),
        "required": {"type": "boolean"},
        "deferrable": {"type": "boolean"},
        "dependsOn": {
            "type": "array",
            "items": {
                "title": "QuestionSlotDependency",
                "type": "object",
                "properties": {
                    "slot": {"type": "string"},
                    "op": {"type": "string"},
                    "value": {},  # any JSON value — the branch operand
                },
                "required": ["slot", "op", "value"],
                "additionalProperties": False,
            },
        },
        "moduleGate": {
            "title": "ModuleType",
            "type": "string",
            "enum": [m.value for m in ModuleType],
        },
        "validation": {"type": "object"},
        "promptHuman": {"type": "string"},
        "promptAgent": {"type": "string"},
    }
    required = ["key", "type", "required", "deferrable",
                "promptHuman", "promptAgent"]
    if enum_member:
        properties["enumValues"] = {
            "type": "array",
            "items": {"type": "string"},
        }
        required.insert(2, "enumValues")
    return {
        "title": "EnumQuestionSlot" if enum_member else "StandardQuestionSlot",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


class QuestionSlotListJSON(TypeDecorator):
    """QuestionManifest.questions — a typed list of QuestionSlot
    (James's tap (a), 2026-10-30; Author's Choice 1 RESOLVED).

    A slot carries: key (canonical string), type (QuestionSlotType),
    enumValues (string[] — iff type = ENUM), required, deferrable,
    dependsOn (branching entries {slot, op, value}), moduleGate
    (ModuleType), validation (free-form constraint JSON), promptHuman,
    promptAgent. camelCase keys, as everywhere in this schema.

    THE enumValues RULE, enforced structurally: the tap's one
    conditional — enumValues present iff type = ENUM — cannot be a
    generated validator (generated files are never hand-edited), so
    the slot is a two-member union split on exactly that condition.
    EnumQuestionSlot (type const ENUM) REQUIRES the enumValues field;
    StandardQuestionSlot (type one of the other six) does not declare
    it and, being closed (additionalProperties: false), forbids it.
    A slot therefore validates iff it obeys the rule — at the
    generated-Pydantic level, with no hand-written validator anywhere.
    The same rule is enforced again at the DB level by revision
    d52f8b1a904c's validation trigger, for raw-SQL writers.

    The value vocabularies are built FROM the enums (QuestionSlotType,
    ModuleType) at authoring time — they are not a second hand copy.
    """

    impl = JSON
    cache_ok = True

    json_schema = {
        "title": "QuestionSlotList",
        "type": "array",
        "items": {
            "title": "QuestionSlot",
            "oneOf": [
                _question_slot(enum_member=True),
                _question_slot(enum_member=False),
            ],
        },
    }

# ---------------------------------------------------------------------------
# Intake layer (spec §4.1)
# ---------------------------------------------------------------------------


class IntakeDraft(Base):
    """Slot-typed intake draft. `token` is the resume handle (the draft's
    serialized state also lives behind intake:draft:{token} in Redis, 72h;
    Postgres is authoritative — spec §6)."""

    __tablename__ = "intake_draft"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    token: Mapped[str] = mapped_column("token", String, nullable=False, unique=True)
    answers: Mapped[dict] = mapped_column("answers", JSON, nullable=False)
    missing_slots: Mapped[list] = mapped_column(
        "missingSlots", ARRAY(String), nullable=False
    )
    invalid_slots: Mapped[dict] = mapped_column("invalidSlots", JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        "expiresAt", DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False, default=_now
    )

    __table_args__ = (Index("ix_intake_draft_expires", "expiresAt"),)


class TripProfile(Base):
    """The buyer's confirmed trip shape. Travelers are ROWS related to
    this profile (never a party count); stays are StayPhase ROWS (never
    trip-level check-in/check-out columns — spec §3 principles 1–2,
    §11 do-not-do list)."""

    __tablename__ = "trip_profile"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    buyer_id: Mapped[str] = mapped_column("buyerId", String, nullable=False)
    version: Mapped[int] = mapped_column(
        "version", Integer, nullable=False, default=1
    )
    modules: Mapped[list] = mapped_column(
        "modules",
        ARRAY(SAEnum(ModuleType, name="module_type")),
        nullable=False,
    )
    tier: Mapped[str] = mapped_column(
        "tier", String, nullable=False, default="AGENTIC"  # AGENTIC | VIP_PAYG
    )
    authorization: Mapped[dict] = mapped_column(
        "authorization", JSON, nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        "confirmedAt", DateTime(timezone=True), nullable=True
    )
    superseded_by: Mapped[str | None] = mapped_column(
        "supersededBy", String, nullable=True
    )

    travelers: Mapped[list["Traveler"]] = relationship(
        back_populates="trip_profile", cascade="all, delete-orphan"
    )
    stay_phases: Mapped[list["StayPhase"]] = relationship(
        back_populates="trip_profile",
        cascade="all, delete-orphan",
        order_by="StayPhase.seq",
    )

    __table_args__ = (Index("ix_trip_profile_buyer_confirmed", "buyerId", "confirmedAt"),)


class Traveler(Base):
    """A traveler is an object with a role — never a count (spec §3.2).
    Health attributes are NEVER columns here (spec §3.6): they live in
    the restricted namespace, joined only through ConsentRecord."""

    __tablename__ = "traveler"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    trip_profile_id: Mapped[str] = mapped_column(
        "tripProfileId",
        String,
        ForeignKey("trip_profile.id"),
        nullable=False,
    )
    role: Mapped[TravelerRole] = mapped_column(
        "role", SAEnum(TravelerRole, name="traveler_role"), nullable=False
    )
    origin: Mapped[str | None] = mapped_column("origin", String, nullable=True)
    nationality: Mapped[str | None] = mapped_column(
        "nationality", String, nullable=True
    )
    utility_weights: Mapped[dict] = mapped_column(
        "utilityWeights", JSON, nullable=False
    )

    trip_profile: Mapped["TripProfile"] = relationship(back_populates="travelers")

    __table_args__ = (Index("ix_traveler_trip", "tripProfileId"),)


class GeoAnchor(Base):
    """Polymorphic anchor (spec §3.3): VENUE / FACILITY / ADDRESS / METRO.
    `refId` is a reference into whichever surface owns the thing (a
    services/api Event id, a facility id, a metro code) — a plain string
    by the same boundary law as sourceRef, never an FK out of this DB."""

    __tablename__ = "geo_anchor"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    type: Mapped[GeoAnchorType] = mapped_column(
        "type", SAEnum(GeoAnchorType, name="geo_anchor_type"), nullable=False
    )
    ref_id: Mapped[str | None] = mapped_column("refId", String, nullable=True)
    label: Mapped[str] = mapped_column("label", String, nullable=False)
    lat: Mapped[float] = mapped_column("lat", Float, nullable=False)
    lng: Mapped[float] = mapped_column("lng", Float, nullable=False)
    radius_km: Mapped[float] = mapped_column(
        "radiusKm", Float, nullable=False, default=15.0
    )
    metro_id: Mapped[str | None] = mapped_column("metroId", String, nullable=True)

    __table_args__ = (Index("ix_geo_anchor_type_ref", "type", "refId"),)


class MetroProfile(Base):
    __tablename__ = "metro_profile"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    metro_code: Mapped[str] = mapped_column(
        "metroCode", String, nullable=False, unique=True
    )
    facility_clusters: Mapped[dict] = mapped_column(
        "facilityClusters", JSON, nullable=False
    )
    resort_clusters: Mapped[dict] = mapped_column(
        "resortClusters", JSON, nullable=False
    )
    split_stay_default: Mapped[bool] = mapped_column(
        "splitStayDefault", Boolean, nullable=False, default=False
    )
    safety_weights: Mapped[dict] = mapped_column(
        "safetyWeights", JSON, nullable=False
    )


class StayPhase(Base):
    """One phase of a stay. A trip's stays are the ARRAY of these rows
    (schema-review criterion 1): per-phase check-in/check-out, per-phase
    occupancy — the trip itself carries no check-in/check-out pair."""

    __tablename__ = "stay_phase"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    trip_profile_id: Mapped[str] = mapped_column(
        "tripProfileId",
        String,
        ForeignKey("trip_profile.id"),
        nullable=False,
    )
    kind: Mapped[StayPhaseKind] = mapped_column(
        "kind", SAEnum(StayPhaseKind, name="stay_phase_kind"), nullable=False
    )
    property_ref: Mapped[str | None] = mapped_column(
        "propertyRef", String, nullable=True
    )
    check_in: Mapped[datetime] = mapped_column(
        "checkIn", DateTime(timezone=True), nullable=False
    )
    check_out: Mapped[datetime] = mapped_column(
        "checkOut", DateTime(timezone=True), nullable=False
    )
    occupants: Mapped[dict] = mapped_column("occupants", JSON, nullable=False)
    criteria: Mapped[dict] = mapped_column("criteria", JSON, nullable=False)
    seq: Mapped[int] = mapped_column("seq", Integer, nullable=False)

    trip_profile: Mapped["TripProfile"] = relationship(back_populates="stay_phases")

    __table_args__ = (Index("ix_stay_phase_trip_seq", "tripProfileId", "seq"),)


# ---------------------------------------------------------------------------
# Offer layer — the snapshot pattern (spec §4.1, §3.5)
# ---------------------------------------------------------------------------


class SearchSession(Base):
    __tablename__ = "search_session"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    trip_profile_id: Mapped[str] = mapped_column(
        "tripProfileId",
        String,
        ForeignKey("trip_profile.id"),
        nullable=False,
    )
    query: Mapped[dict] = mapped_column("query", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False, default=_now
    )

    candidates: Mapped[list["TripCandidate"]] = relationship(
        back_populates="search_session", cascade="all, delete-orphan"
    )


class TripCandidate(Base):
    __tablename__ = "trip_candidate"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    search_session_id: Mapped[str] = mapped_column(
        "searchSessionId",
        String,
        ForeignKey("search_session.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        "status", String, nullable=False, default="OPEN"  # OPEN | PARTIAL | FAILED
    )
    ranking_score: Mapped[float | None] = mapped_column(
        "rankingScore", Float, nullable=True
    )
    constraints: Mapped[dict] = mapped_column("constraints", JSON, nullable=False)

    search_session: Mapped["SearchSession"] = relationship(back_populates="candidates")
    offer_snapshots: Mapped[list["OfferSnapshot"]] = relationship(
        back_populates="trip_candidate", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_trip_candidate_session", "searchSessionId"),)


class OfferSnapshot(Base):
    """A quoted offer with price and terms frozen at quote time
    (spec §3.5 — non-negotiable). Kind-specific detail lives in
    `payload` (the OfferKind-discriminated union above), NOT in
    per-kind detail tables — the normalized contract is the payload.
    The `rail` column below remains the routing/dispatch rail; it is
    no longer the payload's discriminator (James's tap (c)).

    `sourceRef` is the supplier-side id in services/api (a Listing id,
    Ticket id, or Event id, per rail — R4 §3). It is a plain string
    REFERENCE, never a foreign key: no cross-database join is possible
    from this schema (criterion 8; R4 §8.1).

    IMMUTABILITY, by mechanism at three levels:
      1. DB — the migration's trigger permits exactly ONE post-insert
         write: the divergence annotation (divergenceCode +
         divergenceAt, from NULL, exactly once — the write that records
         an R4 §5 kill). Every other UPDATE and every DELETE raises.
      2. ORM — the guards below mirror the trigger for ORM writers.
      3. API types — the generated Pydantic model is frozen.
    A changed quote is always a NEW snapshot, never an edit (R4 §3.4).

    THE DIVERGENCE-ANNOTATION EXCEPTION — the one permitted write
    above — was ratified by the schema review on THREE TERMS:
      1. DERIVED, NOT INDEPENDENT. The EventLog entry is the
         authoritative record of a divergence; this row's
         divergenceCode / divergenceAt are its derived projection,
         materialized atomically in the same transaction by the
         mirror trigger (trg_offer_snapshot_divergence_mirror,
         Alembic revision 9d4c1f7a2b58). There is no annotation write
         that is not simultaneously an EventLog write, and no writer
         can bypass the mirror.
      2. NO WIDENING. The exception is one column-pair, one
         transition (NULL -> code), exactly once. Any future
         exception request goes to a new review — never to a
         widening of these triggers.
      3. NAMED IN THE RECORD. This docstring and SCHEMA-NOTES.md
         (criterion 5; Author's Choice 3) name the exception and
         these three terms, so a future reader of the triggers
         never needs archaeology to know why the exception exists.
    """

    __tablename__ = "offer_snapshot"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    trip_candidate_id: Mapped[str] = mapped_column(
        "tripCandidateId",
        String,
        ForeignKey("trip_candidate.id"),
        nullable=False,
    )
    rail: Mapped[Rail] = mapped_column(
        "rail", SAEnum(Rail, name="rail"), nullable=False
    )
    source_ref: Mapped[str] = mapped_column("sourceRef", String, nullable=False)
    commitment_class: Mapped[CommitmentClass] = mapped_column(
        "commitmentClass",
        SAEnum(CommitmentClass, name="commitment_class"),
        nullable=False,
    )
    price: Mapped[dict] = mapped_column("price", PriceJSON, nullable=False)
    terms: Mapped[dict] = mapped_column("terms", JSON, nullable=False)
    payload: Mapped[dict] = mapped_column("payload", OfferPayloadJSON, nullable=False)
    divergence_code: Mapped[DivergenceCode | None] = mapped_column(
        "divergenceCode",
        SAEnum(DivergenceCode, name="divergence_code"),
        nullable=True,
    )
    divergence_at: Mapped[datetime | None] = mapped_column(
        "divergenceAt", DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        "expiresAt", DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False, default=_now
    )
    retention_until: Mapped[datetime | None] = mapped_column(
        "retentionUntil", DateTime(timezone=True), nullable=True
    )

    trip_candidate: Mapped["TripCandidate"] = relationship(
        back_populates="offer_snapshots"
    )

    __table_args__ = (
        Index("ix_offer_snapshot_trip_rail", "tripCandidateId", "rail"),
        Index("ix_offer_snapshot_expires", "expiresAt"),
    )


# --- OfferSnapshot immutability guard (ORM level) ---------------------------
# Mirrors the DB trigger in the initial migration. The ONLY permitted
# update is the divergence annotation: divergenceCode/divergenceAt change,
# from divergenceCode NULL, to a non-NULL code, with nothing else touched.
# The trigger is the enforcement of record (it binds writers that bypass
# the ORM); this guard fails ORM writers earlier and louder.

_DIVERGENCE_ATTRS = frozenset({"divergence_code", "divergence_at"})


@event.listens_for(OfferSnapshot, "before_update")
def _offer_snapshot_update_guard(mapper, connection, target):
    state = sa_inspect(target)
    changed = {
        attr.key for attr in state.attrs if attr.history.has_changes()
    }
    if not changed:
        return
    row = connection.execute(
        OfferSnapshot.__table__.select()
        .with_only_columns(OfferSnapshot.__table__.c["divergenceCode"])
        .where(OfferSnapshot.__table__.c["id"] == target.id)
    ).first()
    already_annotated = row is not None and row[0] is not None
    if (
        changed <= _DIVERGENCE_ATTRS
        and not already_annotated
        and target.divergence_code is not None
    ):
        return  # the one permitted write: recording an R4 §5 kill
    raise RuntimeError(
        "OfferSnapshot is immutable: UPDATE refused. The only permitted "
        "post-insert write is the one-time divergence annotation "
        "(divergenceCode/divergenceAt). A changed quote is a new snapshot."
    )


@event.listens_for(OfferSnapshot, "before_delete")
def _offer_snapshot_delete_guard(mapper, connection, target):
    raise RuntimeError(
        "OfferSnapshot is immutable: DELETE refused (append-only record)."
    )


# ---------------------------------------------------------------------------
# Commitment + approval (spec §4.1)
# ---------------------------------------------------------------------------


class ApprovalRequest(Base):
    """The human approval gate's record. `status` keeps the spec's
    string vocabulary (PENDING | APPROVED | REJECTED | EXPIRED) — the
    spec declares enums only in its §4.1 enum block, and inventing
    enums it did not declare would be silent authoring."""

    __tablename__ = "approval_request"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    trip_profile_id: Mapped[str] = mapped_column(
        "tripProfileId",
        String,
        ForeignKey("trip_profile.id"),
        nullable=False,
    )
    commitment_class: Mapped[CommitmentClass] = mapped_column(
        "commitmentClass",
        SAEnum(CommitmentClass, name="commitment_class"),
        nullable=False,
    )
    summary: Mapped[dict] = mapped_column("summary", JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        "status", String, nullable=False, default="PENDING"
    )
    signed_by: Mapped[str | None] = mapped_column("signedBy", String, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        "resolvedAt", DateTime(timezone=True), nullable=True
    )

    commitments: Mapped[list["Commitment"]] = relationship(
        back_populates="approval_request", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_approval_request_trip_status", "tripProfileId", "status"),
    )


class Commitment(Base):
    """A settled (or settling) commitment against one OfferSnapshot.
    `chainTxRef` is the Solana transaction signature (null for
    off-chain settlement) — it RECORDS settlement against a services/api
    Ticket id (R4 §6.5); it is a chain reference, not a database FK."""

    __tablename__ = "commitment"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    approval_request_id: Mapped[str] = mapped_column(
        "approvalRequestId",
        String,
        ForeignKey("approval_request.id"),
        nullable=False,
    )
    offer_snapshot_id: Mapped[str] = mapped_column(
        "offerSnapshotId",
        String,
        ForeignKey("offer_snapshot.id"),
        nullable=False,
    )
    state: Mapped[str] = mapped_column("state", String, nullable=False)
    settled_at: Mapped[datetime | None] = mapped_column(
        "settledAt", DateTime(timezone=True), nullable=True
    )
    chain_tx_ref: Mapped[str | None] = mapped_column(
        "chainTxRef", String, nullable=True
    )

    approval_request: Mapped["ApprovalRequest"] = relationship(
        back_populates="commitments"
    )
    offer_snapshot: Mapped["OfferSnapshot"] = relationship()


# ---------------------------------------------------------------------------
# Infrastructure (spec §4.1)
# ---------------------------------------------------------------------------


class EventLog(Base):
    """Append-only audit surface (spec §3.7): agent transparency,
    disputes, compliance. Append-only is enforced at the DB level by
    trigger in the initial migration (UPDATE and DELETE raise), and
    mirrored by the ORM guards below. There is no update or delete
    path, ever (schema-review criterion 6)."""

    __tablename__ = "event_log"

    id: Mapped[int] = mapped_column(
        "id", BigInteger, primary_key=True, autoincrement=True
    )
    aggregate_type: Mapped[str] = mapped_column(
        "aggregateType", String, nullable=False
    )
    aggregate_id: Mapped[str] = mapped_column("aggregateId", String, nullable=False)
    event_type: Mapped[str] = mapped_column("eventType", String, nullable=False)
    actor: Mapped[str] = mapped_column(
        "actor", String, nullable=False  # "agent:{id}" | "human:{id}" | "system"
    )
    payload: Mapped[dict] = mapped_column("payload", JSON, nullable=False)
    ts: Mapped[datetime] = mapped_column(
        "ts", DateTime(timezone=True), nullable=False, default=_now
    )

    __table_args__ = (
        Index("ix_event_log_aggregate_ts", "aggregateType", "aggregateId", "ts"),
    )


@event.listens_for(EventLog, "before_update")
def _event_log_no_update(mapper, connection, target):
    raise RuntimeError("EventLog is append-only: UPDATE refused.")


@event.listens_for(EventLog, "before_delete")
def _event_log_no_delete(mapper, connection, target):
    raise RuntimeError("EventLog is append-only: DELETE refused.")


class IdempotencyKey(Base):
    """Postgres is the source of truth for idempotency (spec §6); Redis
    is a hot cache only. Enforcement is the PRIMARY KEY itself: the
    first writer inserts the row with status IN_FLIGHT (the in-flight
    marker), and any second writer of the same key hits the uniqueness
    constraint at the Postgres level (criterion 7)."""

    __tablename__ = "idempotency_key"

    key: Mapped[str] = mapped_column("key", String, primary_key=True)
    scope: Mapped[str] = mapped_column("scope", String, nullable=False)
    request_hash: Mapped[str] = mapped_column("requestHash", String, nullable=False)
    response_json: Mapped[dict | None] = mapped_column(
        "responseJson", JSON, nullable=True
    )
    status: Mapped[str] = mapped_column(
        "status", String, nullable=False, default="IN_FLIGHT"
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False, default=_now
    )

    __table_args__ = (Index("ix_idempotency_key_created", "createdAt"),)


class QuestionManifest(Base):
    """The intake question set as data (consolidation: slot-typed
    intake flow; scope modules are declared/confirmed, never inferred).

    SHAPE — AS TAPPED (James's tap (a), 2026-10-30; Author's Choice 1
    RESOLVED): `questions` is a typed list of QuestionSlot (see
    QuestionSlotListJSON): key (canonical string), type
    (QuestionSlotType), enumValues (string[], iff type = ENUM),
    required, deferrable, dependsOn (branching entries
    {slot, op, value}), moduleGate (ModuleType), validation
    (free-form constraint JSON), promptHuman, promptAgent. The
    enumValues-iff rule is enforced at the generated-Pydantic level
    by the slot union's structure and again at the DB level by
    revision d52f8b1a904c's validation trigger.

    TRACEABILITY DISCIPLINE (data-authoring rule, recorded with the
    tap): every slot either gates a module (moduleGate) or is
    deleted. moduleGate is the discipline's schema anchor; whether a
    given manifest's slots all carry one is an authoring review of
    the manifest data, not a schema constraint — moduleGate stays
    optional in the schema, exactly as tapped.
    """

    __tablename__ = "question_manifest"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column("key", String, nullable=False, unique=True)
    version: Mapped[int] = mapped_column("version", Integer, nullable=False)
    title: Mapped[str] = mapped_column("title", String, nullable=False)
    questions: Mapped[list] = mapped_column(
        "questions", QuestionSlotListJSON, nullable=False
    )
    active: Mapped[bool] = mapped_column(
        "active", Boolean, nullable=False, default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False, default=_now
    )


# ---------------------------------------------------------------------------
# Task rail (consolidation; spec §5 sprint 5) — a DIFFERENT state machine
# from offers; do not overload OfferSnapshot. Shared state lives on
# ServiceTask; per-kind detail hangs off it (joined-table inheritance).
# ---------------------------------------------------------------------------


class ServiceTask(Base):
    __tablename__ = "service_task"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    trip_profile_id: Mapped[str] = mapped_column(
        "tripProfileId",
        String,
        ForeignKey("trip_profile.id"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column("kind", String, nullable=False)
    state: Mapped[TaskState] = mapped_column(
        "state", SAEnum(TaskState, name="task_state"), nullable=False
    )
    details: Mapped[dict] = mapped_column("details", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", DateTime(timezone=True), nullable=False, default=_now
    )

    __mapper_args__ = {"polymorphic_on": kind, "polymorphic_identity": "SERVICE"}

    __table_args__ = (Index("ix_service_task_trip_state", "tripProfileId", "state"),)


class DiningTask(ServiceTask):
    __tablename__ = "dining_task"

    id: Mapped[str] = mapped_column(
        "id",
        String,
        ForeignKey("service_task.id"),
        primary_key=True,
    )
    geo_anchor_ref: Mapped[str | None] = mapped_column(
        "geoAnchorRef", String, nullable=True
    )
    requested_for: Mapped[datetime | None] = mapped_column(
        "requestedFor", DateTime(timezone=True), nullable=True
    )
    party_traveler_refs: Mapped[dict | None] = mapped_column(
        "partyTravelerRefs", JSON, nullable=True
    )

    __mapper_args__ = {"polymorphic_identity": "DINING"}


class TransferTask(ServiceTask):
    __tablename__ = "transfer_task"

    id: Mapped[str] = mapped_column(
        "id",
        String,
        ForeignKey("service_task.id"),
        primary_key=True,
    )
    from_anchor_ref: Mapped[str | None] = mapped_column(
        "fromAnchorRef", String, nullable=True
    )
    to_anchor_ref: Mapped[str | None] = mapped_column(
        "toAnchorRef", String, nullable=True
    )
    pickup_at: Mapped[datetime | None] = mapped_column(
        "pickupAt", DateTime(timezone=True), nullable=True
    )
    vehicle_class: Mapped[str | None] = mapped_column(
        "vehicleClass", String, nullable=True
    )

    __mapper_args__ = {"polymorphic_identity": "TRANSFER"}


class ConciergeBrief(Base):
    """The structured handoff when a flow escalates to a human
    concierge (consolidation: VIP_PAYG escalation with a structured
    ConciergeBrief handoff and pre-authorized metering — rate, cap,
    expiry). Shares the TaskState machine per the consolidation's
    grouping. `trigger` vocabulary (consolidation): party size,
    all-in value, multi-venue complexity, accessibility/dietary,
    international, "I want a person" — kept a string because the spec
    declares no enum for it (see ApprovalRequest.status note)."""

    __tablename__ = "concierge_brief"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    trip_profile_id: Mapped[str] = mapped_column(
        "tripProfileId",
        String,
        ForeignKey("trip_profile.id"),
        nullable=False,
    )
    state: Mapped[TaskState] = mapped_column(
        "state", SAEnum(TaskState, name="task_state"), nullable=False
    )
    trigger: Mapped[str] = mapped_column("trigger", String, nullable=False)
    brief: Mapped[dict] = mapped_column("brief", JSON, nullable=False)
    metering_rate_cents: Mapped[int | None] = mapped_column(
        "meteringRateCents", Integer, nullable=True
    )
    metering_cap_cents: Mapped[int | None] = mapped_column(
        "meteringCapCents", Integer, nullable=True
    )
    metering_expires_at: Mapped[datetime | None] = mapped_column(
        "meteringExpiresAt", DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False, default=_now
    )


# ---------------------------------------------------------------------------
# Dormant health tables (spec §4.1) — created in Sprint 0, populated in
# the month 4–5 conditional sprint. Present and UNUSED: nothing in the
# event vertical references them, and adding the health vertical must
# require no migration touching event tables (spec §2, §5 sprint 7).
# ---------------------------------------------------------------------------


class FacilityProfile(Base):
    __tablename__ = "facility_profile"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    geo_anchor_id: Mapped[str] = mapped_column("geoAnchorId", String, nullable=False)
    accreditation: Mapped[dict] = mapped_column(
        "accreditation", JSON, nullable=False
    )
    languages: Mapped[list] = mapped_column(
        "languages", ARRAY(String), nullable=False
    )
    metro_id: Mapped[str | None] = mapped_column("metroId", String, nullable=True)


class PackageTemplate(Base):
    __tablename__ = "package_template"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    facility_id: Mapped[str] = mapped_column("facilityId", String, nullable=False)
    procedure_class_band: Mapped[str] = mapped_column(
        "procedureClassBand", String, nullable=False
    )
    phase_template: Mapped[dict] = mapped_column(
        "phaseTemplate", JSON, nullable=False
    )
    inclusions: Mapped[dict] = mapped_column("inclusions", JSON, nullable=False)
    deposit_terms: Mapped[dict] = mapped_column("depositTerms", JSON, nullable=False)


class ProcedureClassBand(Base):
    """Fit-to-fly bands as data (consolidation): the composer reads
    minDaysPostOpBeforeReturn and refuses to quote inside the window."""

    __tablename__ = "procedure_class_band"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    band: Mapped[str] = mapped_column("band", String, nullable=False, unique=True)
    min_days_post_op_before_return: Mapped[int] = mapped_column(
        "minDaysPostOpBeforeReturn", Integer, nullable=False
    )
    cabin_comfort_min: Mapped[str | None] = mapped_column(
        "cabinComfortMin", String, nullable=True
    )


# ---------------------------------------------------------------------------
# Restricted namespace — Postgres schema `health_restricted`
# (config.RESTRICTED_SCHEMA), consent-gated (spec §3.6, §4.1).
#
# Isolation law:
# - These two tables live in their own schema, apart from every other
#   table in this database.
# - NOTHING in the public schema references them, and they reference
#   nothing in the public schema. `subjectId` is an opaque subject
#   reference carried by value — deliberately NOT a foreign key — so
#   the one-way dependency of the spec holds structurally: Traveler
#   never references HealthAttribute; health data joins a trip only
#   through ConsentRecord and the facility rail's PackageTemplate.
# - RLS enablement on this schema is a month 4–5 sprint item (spec §5
#   sprint 7); the namespace separation itself ships now.
# ---------------------------------------------------------------------------


class ConsentRecord(Base):
    __tablename__ = "consent_record"
    __table_args__ = {"schema": RESTRICTED_SCHEMA}

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    subject_id: Mapped[str] = mapped_column("subjectId", String, nullable=False)
    purpose: Mapped[str] = mapped_column("purpose", String, nullable=False)
    version: Mapped[str] = mapped_column("version", String, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        "grantedAt", DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        "revokedAt", DateTime(timezone=True), nullable=True
    )

    health_attributes: Mapped[list["HealthAttribute"]] = relationship(
        back_populates="consent_record", cascade="all, delete-orphan"
    )


class HealthAttribute(Base):
    __tablename__ = "health_attribute"
    __table_args__ = {"schema": RESTRICTED_SCHEMA}

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    subject_id: Mapped[str] = mapped_column("subjectId", String, nullable=False)
    consent_id: Mapped[str] = mapped_column(
        "consentId",
        String,
        ForeignKey(f"{RESTRICTED_SCHEMA}.consent_record.id"),
        nullable=False,
    )
    attr_key: Mapped[str] = mapped_column("attrKey", String, nullable=False)
    attr_value: Mapped[dict] = mapped_column("attrValue", JSON, nullable=False)
    retention_until: Mapped[datetime] = mapped_column(
        "retentionUntil", DateTime(timezone=True), nullable=False
    )

    consent_record: Mapped["ConsentRecord"] = relationship(
        back_populates="health_attributes"
    )


# ---------------------------------------------------------------------------
# Sprint 1.5 (NEAR Hackathon, Nov 2026) — the CRE intent marketplace.
# Additive only: four new tables + their enums; no Sprint 0/1 table is
# touched. Authored from docs/hackathon/nov-2026/intent-schema.md and
# the ratified decisions D1–D3 (04-DECISIONS-LOG.md): income commercial
# real estate, two service lines (advisory, then placement against the
# advisory's spec), micro-region as the analytical unit. IntentStatus
# carries Diagram 4's lifecycle states (docs/diagrams/
# 04-intent-lifecycle.md); the NEAR contract enforces the same states.
# ---------------------------------------------------------------------------


class IntentKind(enum.Enum):
    AVAILABILITY = "availability"
    DEMAND = "demand"


class PosterKind(enum.Enum):
    HUMAN = "human"
    AGENT = "agent"
    INTERNAL_AGENT = "internal_agent"
    PARTNER = "partner"


class IntentDomain(enum.Enum):
    CRE_EXPENSE_ANALYSIS = "cre_expense_analysis"
    CRE_PROPERTY_MANAGEMENT = "cre_property_management"
    CRE_MARKET_SURVEY = "cre_market_survey"
    CRE_INCOME_ANALYSIS = "cre_income_analysis"


class WorkProduct(enum.Enum):
    OPERATING_BUDGET = "operating_budget"
    PM_SPEC = "pm_spec"
    COST_MODEL = "cost_model"
    BENCHMARK_ANALYSIS = "benchmark_analysis"
    PLACEMENT = "placement"


class PropertyType(enum.Enum):
    BRANDED_HOTEL = "branded_hotel"
    RESIDENTIAL_RENTAL = "residential_rental"
    RESIDENTIAL_CONDO = "residential_condo"
    HOSPITALITY = "hospitality"
    MEDICAL_RECOVERY = "medical_recovery"


class AcquisitionStage(enum.Enum):
    UNDERWRITING = "underwriting"
    POST_CLOSE = "post_close"
    OPERATING = "operating"


class IntentTier(enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    ANY = "ANY"


class IntentStatus(enum.Enum):
    POSTED = "POSTED"
    BIDDING = "BIDDING"
    SELECTED = "SELECTED"
    SETTLING = "SETTLING"
    SETTLED = "SETTLED"
    SETTLE_FAILED = "SETTLE_FAILED"
    DELIVERED = "DELIVERED"
    EXPIRED = "EXPIRED"


class BidStatus(enum.Enum):
    SUBMITTED = "SUBMITTED"
    SELECTED = "SELECTED"
    NOT_SELECTED = "NOT_SELECTED"
    WITHDRAWN = "WITHDRAWN"


class AssetSubclass(enum.Enum):
    """The HIADR taxonomy (Addendum A, ratified 2026-11-08 via
    DeepSeek, relayed by James): the marketplace's five tracks.
    H/I are operating CRE — target area may be a radius or a
    polygon. A/D/R are raw land / subterranean — a GeoJSON polygon
    is required, and subterranean context is mandatory for A, D
    and R (Addendum A §§2-3; the D inclusion resolved by DeepSeek
    2026-11-08 — data centers need water rights and soil/bedrock
    data to be underwritable). Enforcement lives in intents.py."""

    H = "H"  # Hospitality (resorts, hotels)
    I = "I"  # Income (multifamily, residential, condos)
    A = "A"  # Agriculture (farms, agricultural raw land)
    D = "D"  # Development (industrial, data centers, raw land)
    R = "R"  # Resource (subterranean exploration / extraction)


class AgReferralState(enum.Enum):
    """The evidence-gated ladder for Tracks A/D/R
    (docs/specifications/06-EVIDENCE-GATED-ARCHITECTURE.md).
    Transitions are evidence- and consent-gated; no state is
    reached automatically beyond INPUT_VALIDATED at intake."""

    INTENT_RECEIVED = "intent_received"
    INPUT_VALIDATED = "input_validated"
    SPATIAL_ASSESSMENT_PENDING = "spatial_assessment_pending"
    SPATIAL_ASSESSMENT_COMPLETED = "spatial_assessment_completed"
    PROVIDER_ELIGIBILITY_PENDING = "provider_eligibility_pending"
    PROVIDER_PROPOSAL_RECEIVED = "provider_proposal_received"
    FARMER_APPROVAL_PENDING = "farmer_approval_pending"
    SERVICE_AUTHORIZED = "service_authorized"
    SERVICE_REPORTED_ACTIVE = "service_reported_active"
    OBSERVATIONS_COLLECTED = "observations_collected"
    OUTCOME_ASSESSED = "outcome_assessed"
    FINANCING_REVIEW = "financing_review"
    SALE_ELIGIBILITY_REVIEW = "sale_eligibility_review"
    LISTING_APPROVAL_PENDING = "listing_approval_pending"
    AUCTION_ADAPTER = "auction_adapter"


class CountryCode(enum.Enum):
    """The intent's country — the dynamic-extension axis
    (2026-11-08, Paraguay extension): new markets are added as
    enum members, not new schemas. PY enters first alongside the
    founding BR/US footprint and UY."""

    BR = "BR"
    PY = "PY"
    UY = "UY"
    US = "US"


class ExecutionEnvironment(enum.Enum):
    """Where an intent's execution runs (James's stack clarification,
    2026-11-08): NEAR intents / multi-party matching, or Arcium
    sealed-bid auctions (TEE/REE)."""

    NEAR_INTENTS = "near_intents"
    ARCIUM_AUCTION = "arcium_auction"


class AgentAttestation(enum.Enum):
    """How the acting party's identity is attested on an intent:
    a human (trust-layer attestation), or an agent acting on behalf
    of an Entity under x401 (James's stack clarification,
    2026-11-08; the x401 stub lives in metering.py, the real
    verification path is the trust-layer work mapped in
    docs/audit/assurative-v2-gap-analysis.md)."""

    HUMAN = "human"
    AGENT_X401 = "agent_x401"


class MicroRegion(Base):
    """Reference table: the analytical unit of the CRE marketplace
    (D3). Ids are authored slugs (\"miami-brickell\", \"bethesda-cbd\",
    \"baltimore-nw\"); every Intent benchmarks against exactly one."""

    __tablename__ = "micro_region"

    id: Mapped[str] = mapped_column("id", String, primary_key=True)
    label: Mapped[str] = mapped_column("label", String, nullable=False)
    metro: Mapped[str] = mapped_column("metro", String, nullable=False)
    region: Mapped[str] = mapped_column("region", String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False, default=_now
    )
    # Addendum A §4: the HIADR Content Desk data layer — period
    # aggregates the Desk publishes (prior 30d / 90d, 18m / 36m
    # lookbacks). Null until the data pipeline populates it; the
    # /pulse endpoint serves what is real and says so.
    pulse_data: Mapped[dict | None] = mapped_column(
        "pulseData", JSON, nullable=True
    )

    intents: Mapped[list["Intent"]] = relationship(back_populates="micro_region")


class Intent(Base):
    """A posted specification (kind=demand) or availability offer
    (kind=availability) on the CRE marketplace. The compose row is the
    system of record; `chainIntentRef` records the NEAR contract's
    reference for the same intent — a chain reference, never a FK
    (the R4 rule: references out of this database are plain strings)."""

    __tablename__ = "intent"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    kind: Mapped[IntentKind] = mapped_column(
        "kind", SAEnum(IntentKind, name="intent_kind"), nullable=False
    )
    poster_kind: Mapped[PosterKind] = mapped_column(
        "posterKind", SAEnum(PosterKind, name="poster_kind"), nullable=False
    )
    poster_account: Mapped[str] = mapped_column(
        "posterAccount", String, nullable=False
    )
    domain: Mapped[IntentDomain] = mapped_column(
        "domain", SAEnum(IntentDomain, name="intent_domain"), nullable=False
    )
    work_product: Mapped[WorkProduct] = mapped_column(
        "workProduct", SAEnum(WorkProduct, name="work_product"), nullable=False
    )
    deliverable: Mapped[dict] = mapped_column("deliverable", JSON, nullable=False)
    micro_region_id: Mapped[str] = mapped_column(
        "microRegionId",
        String,
        ForeignKey("micro_region.id"),
        nullable=False,
    )
    asset_context: Mapped[dict] = mapped_column(
        "assetContext", JSON, nullable=False
    )
    # Addendum A (HIADR): the track, its spatial target, and — for
    # the land/resource tracks — the subterranean data layer. All
    # nullable: pre-HIADR rows stay valid (additive only); the API
    # enforces the track rules on new specs (see intents.py).
    asset_subclass: Mapped[AssetSubclass | None] = mapped_column(
        "assetSubclass", SAEnum(AssetSubclass, name="asset_subclass"),
        nullable=True,
    )
    target_area: Mapped[dict | None] = mapped_column(
        "targetArea", JSON, nullable=True
    )
    subterranean_context: Mapped[dict | None] = mapped_column(
        "subterraneanContext", JSON, nullable=True
    )
    # Trust-layer references (James's stack clarification,
    # 2026-11-08): the Assurative V2 Entity this intent belongs to
    # and the Affiliate acting within it. Plain strings carrying
    # UUID values — NEVER foreign keys: Assurative is a separate
    # database (Scope Tenet 01), and cross-database references are
    # plain strings under the filed R4 rule (the chainIntentRef
    # precedent). Resolution lives in the trust layer; the gap
    # analysis is docs/audit/assurative-v2-gap-analysis.md.
    entity_id: Mapped[str | None] = mapped_column(
        "entityId", String, nullable=True
    )
    affiliate_id: Mapped[str | None] = mapped_column(
        "affiliateId", String, nullable=True
    )
    execution_environment: Mapped[ExecutionEnvironment | None] = mapped_column(
        "executionEnvironment",
        SAEnum(ExecutionEnvironment, name="execution_environment"),
        nullable=True,
    )
    agent_attestation: Mapped[AgentAttestation | None] = mapped_column(
        "agentAttestation",
        SAEnum(AgentAttestation, name="agent_attestation"),
        nullable=True,
    )
    # Market extension (Paraguay, 2026-11-08): the intent's
    # country, and the dual-track macro-distress flag — the owner
    # is simultaneously optimizing the asset (the Hold) and
    # preparing its liquidation route (the Exit: Arcium sealed-bid
    # auction into USDC). The routing rules these fields drive are
    # filed in the HIADR addenda; the data-science router that
    # acts on them is Sprint 2 work, not built here.
    country_code: Mapped[CountryCode | None] = mapped_column(
        "countryCode",
        SAEnum(CountryCode, name="country_code"),
        nullable=True,
    )
    macro_distress_exit: Mapped[bool | None] = mapped_column(
        "macroDistressExit", Boolean, nullable=True
    )
    on_site_days: Mapped[int | None] = mapped_column(
        "onSiteDays", Integer, nullable=True
    )
    remote_days: Mapped[int | None] = mapped_column(
        "remoteDays", Integer, nullable=True
    )
    budget_min_usdc: Mapped[int] = mapped_column(
        "budgetMinUsdc", BigInteger, nullable=False
    )
    budget_max_usdc: Mapped[int] = mapped_column(
        "budgetMaxUsdc", BigInteger, nullable=False
    )
    available_from: Mapped[int] = mapped_column(
        "availableFrom", BigInteger, nullable=False
    )
    available_until: Mapped[int] = mapped_column(
        "availableUntil", BigInteger, nullable=False
    )
    tier: Mapped[IntentTier] = mapped_column(
        "tier", SAEnum(IntentTier, name="intent_tier"), nullable=False
    )
    referring_partner: Mapped[str | None] = mapped_column(
        "referringPartner", String, nullable=True
    )
    status: Mapped[IntentStatus] = mapped_column(
        "status",
        SAEnum(IntentStatus, name="intent_status"),
        nullable=False,
        default=IntentStatus.POSTED,
    )
    chain_intent_ref: Mapped[str | None] = mapped_column(
        "chainIntentRef", String, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False, default=_now
    )

    micro_region: Mapped["MicroRegion"] = relationship(back_populates="intents")
    bids: Mapped[list["Bid"]] = relationship(back_populates="intent")
    matches: Mapped[list["Match"]] = relationship(back_populates="intent")


class Bid(Base):
    """One executor's bid against an Intent — human specialist or AI
    agent, competing on the same specification (D2). `payload` is
    free-form by design (narrative, terms; from Day 4, the NEAR AI
    attestation receipt for agent bids)."""

    __tablename__ = "bid"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    intent_id: Mapped[str] = mapped_column(
        "intentId", String, ForeignKey("intent.id"), nullable=False
    )
    bidder_account: Mapped[str] = mapped_column(
        "bidderAccount", String, nullable=False
    )
    bidder_kind: Mapped[PosterKind] = mapped_column(
        "bidderKind", SAEnum(PosterKind, name="poster_kind"), nullable=False
    )
    amount_usdc: Mapped[int] = mapped_column(
        "amountUsdc", BigInteger, nullable=False
    )
    eta_hours: Mapped[int | None] = mapped_column(
        "etaHours", Integer, nullable=True
    )
    on_site_days: Mapped[int | None] = mapped_column(
        "onSiteDays", Integer, nullable=True
    )
    remote_days: Mapped[int | None] = mapped_column(
        "remoteDays", Integer, nullable=True
    )
    payload: Mapped[dict] = mapped_column("payload", JSON, nullable=False)
    status: Mapped[BidStatus] = mapped_column(
        "status",
        SAEnum(BidStatus, name="bid_status"),
        nullable=False,
        default=BidStatus.SUBMITTED,
    )
    chain_bid_ref: Mapped[str | None] = mapped_column(
        "chainBidRef", String, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False, default=_now
    )

    intent: Mapped["Intent"] = relationship(back_populates="bids")
    matches: Mapped[list["Match"]] = relationship(back_populates="bid")


class Match(Base):
    """The pairing record: one Intent, one selected Bid. Created at
    selection (Day 3's settle flow); `state` follows the Commitment
    precedent (plain string, values documented here): SELECTED ->
    SETTLING -> SETTLED -> DELIVERED, SETTLE_FAILED on failure.
    `settlementRef` records the settlement receipt reference (a chain
    reference, never a FK)."""

    __tablename__ = "match"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    intent_id: Mapped[str] = mapped_column(
        "intentId", String, ForeignKey("intent.id"), nullable=False
    )
    bid_id: Mapped[str] = mapped_column(
        "bidId", String, ForeignKey("bid.id"), nullable=False
    )
    matched_by: Mapped[str] = mapped_column("matchedBy", String, nullable=False)
    state: Mapped[str] = mapped_column(
        "state", String, nullable=False, default="SELECTED"
    )
    settlement_ref: Mapped[str | None] = mapped_column(
        "settlementRef", String, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False, default=_now
    )

    intent: Mapped["Intent"] = relationship(back_populates="matches")
    bid: Mapped["Bid"] = relationship(back_populates="matches")


class AgReferral(Base):
    """An agriculture referral intake (Tracks A/D/R) under the
    evidence-gated architecture
    (docs/specifications/06-EVIDENCE-GATED-ARCHITECTURE.md).

    Deliberately NOT an Intent: the Intent table summarizes
    marketplace requests; a referral enters its own state ladder
    and accumulates evidence in linked records (SpatialAssessment /
    ProviderProposal / Observation / AIAssessment). The webhook
    creates the referral and validates its input — and stops.
    No provider is called, nothing is authorized, and a macro
    signal recorded here (macroDistressExit) is a flag, never a
    trigger (the Iron Rule).

    The idempotency key is unique: a replayed webhook returns the
    original referral instead of creating a duplicate.
    """

    __tablename__ = "ag_referral"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    idempotency_key: Mapped[str] = mapped_column(
        "idempotencyKey", String, nullable=False, unique=True, index=True
    )
    state: Mapped[AgReferralState] = mapped_column(
        "state",
        SAEnum(AgReferralState, name="ag_referral_state"),
        nullable=False,
        default=AgReferralState.INTENT_RECEIVED,
    )
    payload: Mapped[dict] = mapped_column("payload", JSON, nullable=False)
    country_code: Mapped[CountryCode | None] = mapped_column(
        "countryCode",
        SAEnum(CountryCode, name="country_code"),
        nullable=True,
    )
    macro_distress_exit: Mapped[bool | None] = mapped_column(
        "macroDistressExit", Boolean, nullable=True
    )
    created_at: Mapped[int] = mapped_column(
        "createdAt", BigInteger, nullable=False
    )


class SpatialAssessment(Base):
    """Evidence record for a referral's spatial review.

    Kept separate from AgReferral: a GeoJSON/CAR match is evidence,
    not a state change by itself, and it never establishes land
    ownership.
    """

    __tablename__ = "spatial_assessment"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    referral_id: Mapped[str] = mapped_column(
        "referralId", String, ForeignKey("ag_referral.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column("provider", String, nullable=False)
    status: Mapped[str] = mapped_column("status", String, nullable=False)
    geometry: Mapped[dict] = mapped_column("geometry", JSON, nullable=False)
    registry_matches: Mapped[list] = mapped_column(
        "registryMatches", JSON, nullable=False, default=list
    )
    confidence_score: Mapped[float | None] = mapped_column(
        "confidenceScore", Float, nullable=True
    )
    ownership_established: Mapped[bool] = mapped_column(
        "ownershipEstablished", Boolean, nullable=False, default=False
    )
    created_at: Mapped[int] = mapped_column(
        "createdAt", BigInteger, nullable=False
    )


class ProviderProposal(Base):
    """Evidence record for what a provider proposes.

    A proposal can move a referral to FARMER_APPROVAL_PENDING; it
    cannot authorize execution.
    """

    __tablename__ = "provider_proposal"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    referral_id: Mapped[str] = mapped_column(
        "referralId", String, ForeignKey("ag_referral.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column("provider", String, nullable=False)
    status: Mapped[str] = mapped_column("status", String, nullable=False)
    proposal: Mapped[dict] = mapped_column("proposal", JSON, nullable=False)
    execution_authorized: Mapped[bool] = mapped_column(
        "executionAuthorized", Boolean, nullable=False, default=False
    )
    created_at: Mapped[int] = mapped_column(
        "createdAt", BigInteger, nullable=False
    )


class Observation(Base):
    """Evidence record for an observed agricultural outcome."""

    __tablename__ = "observation"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    referral_id: Mapped[str] = mapped_column(
        "referralId", String, ForeignKey("ag_referral.id"), nullable=False, index=True
    )
    metric: Mapped[str] = mapped_column("metric", String, nullable=False)
    value: Mapped[float] = mapped_column("value", Float, nullable=False)
    unit: Mapped[str] = mapped_column("unit", String, nullable=False)
    method: Mapped[str] = mapped_column("method", String, nullable=False)
    source: Mapped[str] = mapped_column("source", String, nullable=False)
    created_at: Mapped[int] = mapped_column(
        "createdAt", BigInteger, nullable=False
    )


class AIAssessment(Base):
    """AI calculation kept separate from scientific review.

    `signed` records that an assessment was signed/attested. It is
    deliberately independent from `scientifically_verified`: a
    signature does not certify a yield result. `review_status`
    carries the review state separately from both booleans.
    """

    __tablename__ = "ai_assessment"

    id: Mapped[str] = mapped_column("id", String, primary_key=True, default=_uuid)
    referral_id: Mapped[str] = mapped_column(
        "referralId", String, ForeignKey("ag_referral.id"), nullable=False, index=True
    )
    model_version: Mapped[str] = mapped_column(
        "modelVersion", String, nullable=False
    )
    input_evidence_refs: Mapped[list] = mapped_column(
        "inputEvidenceRefs", JSON, nullable=False, default=list
    )
    calculation: Mapped[dict] = mapped_column(
        "calculation", JSON, nullable=False
    )
    estimated_difference_value: Mapped[float | None] = mapped_column(
        "estimatedDifferenceValue", Float, nullable=True
    )
    estimated_difference_unit: Mapped[str | None] = mapped_column(
        "estimatedDifferenceUnit", String, nullable=True
    )
    signed: Mapped[bool] = mapped_column(
        "signed", Boolean, nullable=False, default=False
    )
    scientifically_verified: Mapped[bool] = mapped_column(
        "scientificallyVerified", Boolean, nullable=False, default=False
    )
    review_status: Mapped[str] = mapped_column(
        "reviewStatus", String, nullable=False, default="PENDING_REVIEW"
    )
    created_at: Mapped[int] = mapped_column(
        "createdAt", BigInteger, nullable=False
    )
