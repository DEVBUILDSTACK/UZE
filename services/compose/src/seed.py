"""Sprint 1 seed data: the seed QuestionManifest.

ONE manifest, six slots, authored to exercise every classifier path
slice 1 depends on:

  event.city     STRING, required                -> moduleGate TICKETS
  party.seats    INT, required, min/max          -> moduleGate TICKETS
  tickets.tier   ENUM, deferrable                -> moduleGate TICKETS
  stay.needed    BOOL, required                  -> moduleGate STAY
  stay.checkin   DATE, required, dependsOn stay.needed == true
                                                 -> moduleGate STAY
  stay.checkout  DATE, deferrable, dependsOn stay.needed == true
                                                 -> moduleGate STAY

Required slots, a deferrable slot, an ENUM slot, a dependsOn branch,
and two different module gates — the full tapped QuestionSlot shape
in miniature. This is Sprint 1 SEED DATA, clearly marked: a real
manifest set is authored data that arrives through review, not code.

seed() is idempotent by manifest key: an existing row with the seed
key is returned unchanged, never duplicated or overwritten.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

import models

SEED_MANIFEST: dict = {
    "key": "intake.core",
    "version": 1,
    "title": "Core intake — Sprint 1 seed",
    "questions": [
        {
            "key": "event.city",
            "type": "STRING",
            "required": True,
            "deferrable": False,
            "moduleGate": "TICKETS",
            "validation": {"minLength": 1},
            "promptHuman": "Which city is the event in?",
            "promptAgent": "Ask for the event city as free text.",
        },
        {
            "key": "party.seats",
            "type": "INT",
            "required": True,
            "deferrable": False,
            "moduleGate": "TICKETS",
            "validation": {"min": 1, "max": 20},
            "promptHuman": "How many seats do you need?",
            "promptAgent": "Ask for the seat count as an integer, 1 to 20.",
        },
        {
            "key": "tickets.tier",
            "type": "ENUM",
            "enumValues": ["general", "premium", "vip"],
            "required": False,
            "deferrable": True,
            "moduleGate": "TICKETS",
            "promptHuman": "Which ticket tier?",
            "promptAgent": "Offer the enumerated ticket tiers.",
        },
        {
            "key": "stay.needed",
            "type": "BOOL",
            "required": True,
            "deferrable": False,
            "moduleGate": "STAY",
            "promptHuman": "Do you need a place to stay?",
            "promptAgent": "Ask whether the trip needs accommodation.",
        },
        {
            "key": "stay.checkin",
            "type": "DATE",
            "required": True,
            "deferrable": False,
            "dependsOn": [
                {"slot": "stay.needed", "op": "eq", "value": True}
            ],
            "moduleGate": "STAY",
            "promptHuman": "What is your check-in date?",
            "promptAgent": "Ask for the check-in date (ISO 8601).",
        },
        {
            "key": "stay.checkout",
            "type": "DATE",
            "required": False,
            "deferrable": True,
            "dependsOn": [
                {"slot": "stay.needed", "op": "eq", "value": True}
            ],
            "moduleGate": "STAY",
            "promptHuman": "What is your check-out date?",
            "promptAgent": "Ask for the check-out date (ISO 8601).",
        },
    ],
}


def seed(session: Session) -> models.QuestionManifest:
    """Insert the seed manifest if its key is absent; return the row."""
    existing = (
        session.query(models.QuestionManifest)
        .filter_by(key=SEED_MANIFEST["key"])
        .one_or_none()
    )
    if existing is not None:
        return existing
    row = models.QuestionManifest(
        key=SEED_MANIFEST["key"],
        version=SEED_MANIFEST["version"],
        title=SEED_MANIFEST["title"],
        questions=SEED_MANIFEST["questions"],
        active=True,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row
