"""classify() — the DETERMINISTIC intake classifier (directive 4).

Directive 4 (ratified 2026-10-30): classify() is deterministic and
contains no LLM. This module is the enforcement of that rule, not just
its statement: it imports nothing but the standard library, pydantic,
and the GENERATED QuestionManifest types. It never imports the suggest
module, and no LLM or HTTP client appears anywhere in its dependency
set — tests/test_classify.py proves that by importing this module in a
clean interpreter and inspecting sys.modules. suggest_slots() is the
only place an LLM may ever be consulted, and it lives in suggest.py,
downstream of this module, validating its proposals back through
answer_violation() below. The dependency arrow points one way.

WHAT classify() DOES
--------------------
classify(answers, manifest) walks the manifest's slots IN MANIFEST
ORDER and sorts each slot into exactly one bucket:

  satisfied      applicable, answered, and the answer is valid
  invalid        applicable, answered, but the answer fails validation
                 (the bucket value is the violation reason, see below)
  deferred       applicable, unanswered, and the slot is deferrable
  missing        applicable, unanswered, required, and NOT deferrable
  optional       applicable, unanswered, neither required nor deferrable
  notApplicable  the slot's dependsOn conditions do not all hold
                 against the current answers — the branch that would
                 ask it was never taken, so it is not owed

A null answer is no answer: null-valued keys are treated as absent
everywhere (satisfaction, dependsOn, readiness).

DEPENDSON SEMANTICS
-------------------
Each dependsOn entry is {slot, op, value}, evaluated against the
CURRENT answers for the referenced slot. Supported ops (the tap filed
no op vocabulary; this set is the classifier's documented one — the
Sprint 0 demo's manifest data already uses "answered"):

  eq / neq       JSON equality (bool only ever equals bool; numbers
                 compare numerically across int/float)
  in             the referenced answer equals one of the entry's
                 value list (a non-list value never matches)
  gt/lt/gte/lte  ordering — numbers with numbers, strings with
                 strings; anything else never matches
  answered       the referenced slot has a non-null answer
                 (the entry's value is ignored)
  not_answered   the referenced slot has no non-null answer

A comparison (eq/neq/in/gt/lt/gte/lte) against a MISSING referenced
answer is False — neq included: "not yet answered" is not "different".
An unknown op is False: a branch with an unrecognised op never opens.
A slot is applicable iff ALL its dependsOn entries hold; a slot with
no dependsOn is always applicable.

ANSWER VALIDATION — answer_violation(slot, value) -> reason | None
------------------------------------------------------------------
Checks run in a fixed order and the FIRST violation is the reason (a
short stable string), so the same bad answer always yields the same
reason: "type" (wrong JSON type for the slot's type — note bool is
never an INT), "enum" (ENUM answer not in enumValues), then the
honored `validation` constraint subset: INT min/max, STRING
minLength/maxLength/pattern (re.fullmatch), ARRAY minItems/maxItems,
reported as "min"/"max"/"minLength"/"maxLength"/"pattern"/
"minItems"/"maxItems". DATE answers must be ISO-8601 date or datetime
strings. `validation` keys outside the honored subset, and constraints
whose own values are mistyped, are ignored — classify() never raises
on answer or manifest data; a malformed manifest SHAPE is the one
loud failure (duplicate slot keys raise ValueError: that is an
authoring bug, not user data).

READINESS RULE (precise, as filed for Sprint 1 slice 1)
-------------------------------------------------------
For a module M, consider every slot whose moduleGate == M. A gated
slot is SETTLED when it is satisfied, deferred, or notApplicable. M
is READY iff every slot gated to M is settled; a missing, invalid, or
optional (unanswered, non-deferrable) gated slot makes M NOT_READY.
Modules with no gated slots do not appear. Slots with moduleGate None
gate nothing: they classify into the buckets above but affect no
module's readiness. `modules` lists every module the manifest gates
at least one slot to, sorted by module value; moduleReadiness carries
the same keys in the same order. All slot-key lists are in manifest
order; the answers dict's own ordering never affects the output —
same input, identical output.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Mapping, Union

from pydantic import BaseModel, ConfigDict

from questionmanifest_pydantic import (
    EnumQuestionSlot,
    QuestionManifest,
    StandardQuestionSlot,
)

Slot = Union[EnumQuestionSlot, StandardQuestionSlot]

READY = "READY"
NOT_READY = "NOT_READY"


class ClassifyResult(BaseModel):
    """The classifier's output — small, typed, frozen, deterministic."""

    model_config = ConfigDict(frozen=True)

    satisfied: list[str]
    missing: list[str]
    deferred: list[str]
    invalid: dict[str, str]
    notApplicable: list[str]
    optional: list[str]
    modules: list[str]
    moduleReadiness: dict[str, str]


# ---------------------------------------------------------------------------
# Answer validation (also the gate suggest.py's proposals must pass)
# ---------------------------------------------------------------------------

def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return _is_int(value) or isinstance(value, float)


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        pass
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


def answer_violation(slot: Slot, value: Any) -> str | None:
    """None if `value` is a valid answer for `slot`, else the reason.

    The reason is the FIRST violation in the fixed check order
    documented in the module docstring — deterministic by construction.
    """
    slot_type = slot.type.value if hasattr(slot.type, "value") else str(slot.type)

    if slot_type == "ENUM":
        if not isinstance(value, str):
            return "type"
        if value not in (slot.enumValues or []):
            return "enum"
        return None

    type_ok = {
        "STRING": lambda v: isinstance(v, str),
        "INT": _is_int,
        "BOOL": lambda v: isinstance(v, bool),
        "DATE": _is_date,
        "OBJECT": lambda v: isinstance(v, dict),
        "ARRAY": lambda v: isinstance(v, list),
    }[slot_type](value)
    if not type_ok:
        return "type"

    validation = slot.validation or {}
    if slot_type == "INT":
        minimum, maximum = validation.get("min"), validation.get("max")
        if _is_number(minimum) and value < minimum:
            return "min"
        if _is_number(maximum) and value > maximum:
            return "max"
    elif slot_type == "STRING":
        min_len = validation.get("minLength")
        max_len = validation.get("maxLength")
        pattern = validation.get("pattern")
        if _is_int(min_len) and len(value) < min_len:
            return "minLength"
        if _is_int(max_len) and len(value) > max_len:
            return "maxLength"
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            return "pattern"
    elif slot_type == "ARRAY":
        min_items = validation.get("minItems")
        max_items = validation.get("maxItems")
        if _is_int(min_items) and len(value) < min_items:
            return "minItems"
        if _is_int(max_items) and len(value) > max_items:
            return "maxItems"
    return None


# ---------------------------------------------------------------------------
# dependsOn evaluation
# ---------------------------------------------------------------------------

def _json_eq(a: Any, b: Any) -> bool:
    """JSON equality: bool only equals bool; numbers compare across
    int/float; everything else uses ==."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if _is_number(a) and _is_number(b):
        return a == b
    return a == b


def _ordered(op: str, a: Any, b: Any) -> bool:
    if not ((_is_number(a) and _is_number(b))
            or (isinstance(a, str) and isinstance(b, str))):
        return False
    return {"gt": a > b, "lt": a < b, "gte": a >= b, "lte": a <= b}[op]


def _condition_holds(dep: Any, answers: Mapping[str, Any]) -> bool:
    present = dep.slot in answers and answers[dep.slot] is not None
    if dep.op == "answered":
        return present
    if dep.op == "not_answered":
        return not present
    if not present:
        return False
    answer = answers[dep.slot]
    if dep.op == "eq":
        return _json_eq(answer, dep.value)
    if dep.op == "neq":
        return not _json_eq(answer, dep.value)
    if dep.op == "in":
        return isinstance(dep.value, list) and any(
            _json_eq(answer, item) for item in dep.value
        )
    if dep.op in ("gt", "lt", "gte", "lte"):
        return _ordered(dep.op, answer, dep.value)
    return False  # unknown op: the branch never opens


def _applicable(slot: Slot, answers: Mapping[str, Any]) -> bool:
    return all(_condition_holds(dep, answers) for dep in (slot.dependsOn or []))


# ---------------------------------------------------------------------------
# The classifier
# ---------------------------------------------------------------------------

def classify(answers: Mapping[str, Any], manifest: QuestionManifest) -> ClassifyResult:
    """Classify `answers` against `manifest` — pure and deterministic.

    No I/O, no clock, no randomness, no LLM: the same (answers,
    manifest) pair always produces an identical ClassifyResult.
    """
    slots: list[Slot] = [entry.root for entry in manifest.questions.root]

    keys = [slot.key for slot in slots]
    if len(set(keys)) != len(keys):
        raise ValueError("manifest carries duplicate slot keys")

    satisfied: list[str] = []
    missing: list[str] = []
    deferred: list[str] = []
    invalid: dict[str, str] = {}
    not_applicable: list[str] = []
    optional: list[str] = []
    bucket: dict[str, str] = {}

    for slot in slots:
        if not _applicable(slot, answers):
            bucket[slot.key] = "notApplicable"
            not_applicable.append(slot.key)
        elif slot.key in answers and answers[slot.key] is not None:
            reason = answer_violation(slot, answers[slot.key])
            if reason is None:
                bucket[slot.key] = "satisfied"
                satisfied.append(slot.key)
            else:
                bucket[slot.key] = "invalid"
                invalid[slot.key] = reason
        elif slot.deferrable:
            bucket[slot.key] = "deferred"
            deferred.append(slot.key)
        elif slot.required:
            bucket[slot.key] = "missing"
            missing.append(slot.key)
        else:
            bucket[slot.key] = "optional"
            optional.append(slot.key)

    modules = sorted(
        {slot.moduleGate.value for slot in slots if slot.moduleGate is not None}
    )
    readiness: dict[str, str] = {}
    for module in modules:
        settled = all(
            bucket[slot.key] in ("satisfied", "deferred", "notApplicable")
            for slot in slots
            if slot.moduleGate is not None and slot.moduleGate.value == module
        )
        readiness[module] = READY if settled else NOT_READY

    return ClassifyResult(
        satisfied=satisfied,
        missing=missing,
        deferred=deferred,
        invalid=invalid,
        notApplicable=not_applicable,
        optional=optional,
        modules=modules,
        moduleReadiness=readiness,
    )
