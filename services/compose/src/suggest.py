"""suggest_slots() — the ONLY seam where an LLM may be consulted
(directive 4, ratified 2026-10-30).

The rule: classify() is deterministic and LLM-free; an LLM's output
may enter the intake flow ONLY here, as PROPOSALS, and every proposal
is validated by the classifier (classify.answer_violation) before it
is returned. A proposal that fails validation is dropped and counted,
never applied. Proposals are never written to a draft by this module:
accepting a proposal is a separate, explicit act by the caller (in
this slice, nothing accepts them automatically at all).

This slice wires NO live LLM. The seam's shape is real — a provider
protocol, proposal validation, drop accounting — but the providers
below are deterministic and local: NullSuggestionProvider (proposes
nothing) and StaticSuggestionProvider (a fixed list, for tests and
demos). Wiring a live provider behind SuggestionProvider is a later,
separately-gated step; nothing in this module imports an LLM or HTTP
client either, so the gate is visible in the import graph.

PROPOSAL VALIDATION (in provider order — deterministic):
  - the proposal must name a slot that exists in the manifest;
  - the slot must be applicable against the current answers and not
    already satisfied (proposing for a satisfied, not-applicable, or
    unknown slot is dropped);
  - the candidate value must pass classify.answer_violation();
  - the first valid proposal for a slot wins; later proposals for
    the same slot are dropped.
Dropped proposals are counted, with their slot keys listed in the
order the provider emitted them (a key may repeat there if the
provider repeated itself).
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Protocol

from pydantic import BaseModel, ConfigDict

from classify import ClassifyResult, Slot, answer_violation
from questionmanifest_pydantic import QuestionManifest


class SlotProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    slot: str
    value: Any


class SuggestResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposals: list[SlotProposal]
    dropped: int
    droppedSlots: list[str]


class SuggestionProvider(Protocol):
    """The provider seam. A live LLM implementation belongs behind
    this protocol and nowhere else in the service."""

    def propose(
        self, *, result: ClassifyResult, answers: Mapping[str, Any]
    ) -> Iterable[Mapping[str, Any]]:
        """Return raw proposals as {"slot": key, "value": candidate}
        mappings. Raw is deliberate: validation is the seam's job,
        not the provider's."""
        ...


class NullSuggestionProvider:
    """The no-op provider: proposes nothing. The default until a live
    provider is separately gated in."""

    def propose(
        self, *, result: ClassifyResult, answers: Mapping[str, Any]
    ) -> Iterable[Mapping[str, Any]]:
        return []


class StaticSuggestionProvider:
    """A deterministic local provider returning a fixed proposal
    list — for tests, demos, and offline development of the seam."""

    def __init__(self, proposals: Iterable[Mapping[str, Any]]) -> None:
        self._proposals = list(proposals)

    def propose(
        self, *, result: ClassifyResult, answers: Mapping[str, Any]
    ) -> Iterable[Mapping[str, Any]]:
        return list(self._proposals)


def suggest_slots(
    result: ClassifyResult,
    answers: Mapping[str, Any],
    manifest: QuestionManifest,
    provider: SuggestionProvider | None = None,
) -> SuggestResult:
    """Ask `provider` for proposals and validate every one through
    the classifier. Pure with respect to persistence: `answers` is
    read, never mutated, and nothing is written anywhere."""
    provider = provider if provider is not None else NullSuggestionProvider()
    slots: dict[str, Slot] = {
        entry.root.key: entry.root for entry in manifest.questions.root
    }
    satisfied = set(result.satisfied)
    not_applicable = set(result.notApplicable)

    accepted: list[SlotProposal] = []
    accepted_keys: set[str] = set()
    dropped_slots: list[str] = []

    for raw in provider.propose(result=result, answers=answers):
        key = raw.get("slot") if isinstance(raw, Mapping) else None
        slot = slots.get(key) if isinstance(key, str) else None
        if (
            slot is None
            or key in satisfied
            or key in not_applicable
            or key in accepted_keys
            or "value" not in raw
            or answer_violation(slot, raw["value"]) is not None
        ):
            dropped_slots.append(key if isinstance(key, str) else "<malformed>")
            continue
        accepted.append(SlotProposal(slot=key, value=raw["value"]))
        accepted_keys.add(key)

    return SuggestResult(
        proposals=accepted,
        dropped=len(dropped_slots),
        droppedSlots=dropped_slots,
    )
