"""suggest_slots() — the directive-4 seam: proposals are validated
by the classifier, invalid ones dropped and counted, and nothing is
ever applied to the answers. Pure unit tests: no database, no LLM —
the providers are the slice's deterministic local implementations.
"""

from __future__ import annotations

from classify import classify
from questionmanifest_pydantic import QuestionManifest
from seed import SEED_MANIFEST
from suggest import (
    NullSuggestionProvider,
    StaticSuggestionProvider,
    suggest_slots,
)


def seed_manifest() -> QuestionManifest:
    return QuestionManifest(
        key=SEED_MANIFEST["key"],
        version=SEED_MANIFEST["version"],
        title=SEED_MANIFEST["title"],
        questions=SEED_MANIFEST["questions"],
    )


def test_proposals_are_validated_and_never_applied():
    manifest = seed_manifest()
    answers = {"event.city": "Miami", "party.seats": 2, "stay.needed": False}
    result = classify(answers, manifest)
    provider = StaticSuggestionProvider(
        [
            {"slot": "tickets.tier", "value": "gold"},      # not in enumValues
            {"slot": "tickets.tier", "value": "vip"},       # valid — accepted
            {"slot": "tickets.tier", "value": "premium"},   # duplicate slot
            {"slot": "event.city", "value": "Tampa"},       # already satisfied
            {"slot": "stay.checkin", "value": "2026-11-06"},  # branch not open
            {"slot": "ghost.slot", "value": 1},             # unknown slot
        ]
    )
    out = suggest_slots(result, answers, manifest, provider)
    assert [(p.slot, p.value) for p in out.proposals] == [("tickets.tier", "vip")]
    assert out.dropped == 5
    assert out.droppedSlots == [
        "tickets.tier", "tickets.tier", "event.city", "stay.checkin",
        "ghost.slot",
    ]
    # Proposals are proposals: the answers the caller holds are
    # untouched, and the accepted value was NOT written anywhere.
    assert answers == {"event.city": "Miami", "party.seats": 2,
                       "stay.needed": False}
    assert "tickets.tier" not in answers


def test_null_provider_and_default_propose_nothing():
    manifest = seed_manifest()
    answers: dict = {}
    result = classify(answers, manifest)
    out = suggest_slots(result, answers, manifest, NullSuggestionProvider())
    assert out.proposals == [] and out.dropped == 0
    default = suggest_slots(result, answers, manifest)
    assert default.proposals == [] and default.dropped == 0


def test_proposal_can_fix_an_invalid_answer():
    manifest = seed_manifest()
    answers = {"event.city": "Miami", "party.seats": 99, "stay.needed": False}
    result = classify(answers, manifest)
    assert result.invalid == {"party.seats": "max"}
    provider = StaticSuggestionProvider(
        [{"slot": "party.seats", "value": 4}]
    )
    out = suggest_slots(result, answers, manifest, provider)
    assert [(p.slot, p.value) for p in out.proposals] == [("party.seats", 4)]
    assert out.dropped == 0
