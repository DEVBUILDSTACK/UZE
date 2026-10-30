"""Runnable proof for the codegen round-trip (run via `make validate`).

Checks, against the GENERATED artifacts only (nothing hand-written here
mirrors the model — if generation breaks, this fails):
  1. Generated Pydantic model imports; enums are real Enum classes;
     price is a real nested model (not Any/dict); timestamps are datetime.
  2. A well-formed sample payload validates end-to-end.
  3. A malformed price (missing currency) is rejected.
  4. An unknown enum value is rejected.
  5. Frozen: mutating a validated instance (and its nested price) raises.
  6. ORM guard: OfferSnapshot inserts fine, but an UPDATE or DELETE flush
     against the SQLAlchemy model raises (immutability at the ORM level).

Exit code 0 = all checks passed.
"""

from __future__ import annotations

import enum
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

failures: list[str] = []


def check(label: str, fn) -> None:
    try:
        fn()
    except AssertionError as exc:
        failures.append(label)
        print(f"FAIL  {label}: {exc}")
    else:
        print(f"PASS  {label}")


# --- 1. Structure of the generated model ----------------------------------
import offersnapshot_pydantic as gen  # noqa: E402


def structure() -> None:
    assert issubclass(gen.Rail, enum.Enum), "Rail is not an Enum"
    assert issubclass(gen.CommitmentClass, enum.Enum), "CommitmentClass is not an Enum"
    assert gen.Rail.SOLANA_NFT.value == "SOLANA_NFT"
    price_field = gen.OfferSnapshot.model_fields["price"]
    assert price_field.annotation is gen.Price, (
        f"price annotation is {price_field.annotation!r}, not the generated Price model"
    )
    import typing

    from pydantic import AwareDatetime

    def is_datetime_ann(ann) -> bool:
        # AwareDatetime is pydantic's annotated datetime (tz-aware); the raw
        # `datetime` class is also acceptable. A plain `str` is not. Optional
        # fields wrap the type in a Union, so unwrap one level.
        if ann is datetime or ann is AwareDatetime:
            return True
        return any(a is datetime or a is AwareDatetime for a in typing.get_args(ann))

    for fname in ("expiresAt", "createdAt"):
        ann = gen.OfferSnapshot.model_fields[fname].annotation
        assert is_datetime_ann(ann), f"{fname} annotation is {ann!r}, not a datetime type"


check("generated model: enums are enums, price is a typed model, timestamps are datetime", structure)


SAMPLE = {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "tripCandidateId": "cand_123",
    "rail": "SOLANA_NFT",
    "sourceRef": "supplier-ticket-987",
    "commitmentClass": "IRREVERSIBLE_ON_CHAIN",
    "price": {"amount": 149.5, "currency": "USDC", "taxesIncluded": True},
    "terms": {"cancellationWindowHours": 0, "transferPolicy": "NFT-transferable", "dateShiftRights": "none"},
    "payload": {"seat": {"section": "GA", "row": "12", "seat": "7"}, "mintRef": "mint_abc"},
    "expiresAt": "2026-11-15T20:00:00Z",
    "createdAt": "2026-10-30T17:45:00Z",
}

instance = None


def valid_sample() -> None:
    global instance
    instance = gen.OfferSnapshot.model_validate(SAMPLE)
    assert instance.rail is gen.Rail.SOLANA_NFT
    assert isinstance(instance.price, gen.Price) and instance.price.amount == 149.5
    assert isinstance(instance.expiresAt, datetime) and instance.expiresAt.tzinfo is not None


check("well-formed sample validates (enum member, typed price, aware datetime)", valid_sample)


def bad_price() -> None:
    from pydantic import ValidationError

    bad = {**SAMPLE, "price": {"amount": 10.0, "taxesIncluded": False}}  # currency missing
    try:
        gen.OfferSnapshot.model_validate(bad)
    except ValidationError:
        return
    raise AssertionError("malformed price was accepted")


check("malformed price (missing currency) is rejected", bad_price)


def bad_enum() -> None:
    from pydantic import ValidationError

    bad = {**SAMPLE, "rail": "PIGEON_COURIER"}
    try:
        gen.OfferSnapshot.model_validate(bad)
    except ValidationError:
        return
    raise AssertionError("unknown rail value was accepted")


check("unknown enum value is rejected", bad_enum)


def frozen() -> None:
    from pydantic import ValidationError

    assert instance is not None, "no validated instance (earlier check failed)"
    for mutate in (
        lambda: setattr(instance, "sourceRef", "tampered"),
        lambda: setattr(instance.price, "amount", 0.01),
    ):
        try:
            mutate()
        except ValidationError:
            continue
        raise AssertionError("mutation of a frozen snapshot was allowed")


check("frozen: validated snapshot and nested price refuse mutation", frozen)


# --- 2. ORM-level immutability guard ---------------------------------------

def orm_guard() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    import models

    engine = create_engine("sqlite://")
    models.Base.metadata.create_all(engine)
    snap = models.OfferSnapshot(
        trip_candidate_id="cand_123",
        rail=models.Rail.SOLANA_NFT,
        source_ref="supplier-ticket-987",
        commitment_class=models.CommitmentClass.IRREVERSIBLE_ON_CHAIN,
        price={"amount": 149.5, "currency": "USDC", "taxesIncluded": True},
        terms={},
        payload={},
        expires_at=datetime(2026, 11, 15, 20, 0, 0),
    )
    with Session(engine) as session:
        session.add(snap)
        session.commit()  # INSERT is the one allowed write
        snap.source_ref = "tampered"
        try:
            session.flush()
        except RuntimeError as exc:
            assert "immutable" in str(exc)
            session.rollback()
        else:
            raise AssertionError("UPDATE flush was not refused by the ORM guard")
        session.delete(snap)
        try:
            session.flush()
        except RuntimeError as exc:
            assert "immutable" in str(exc)
            session.rollback()
        else:
            raise AssertionError("DELETE flush was not refused by the ORM guard")


check("ORM guard: insert allowed, UPDATE and DELETE flushes raise", orm_guard)


print()
if failures:
    print(f"ROUND-TRIP VALIDATION: {len(failures)} check(s) FAILED")
    sys.exit(1)
print("ROUND-TRIP VALIDATION: all checks passed")
