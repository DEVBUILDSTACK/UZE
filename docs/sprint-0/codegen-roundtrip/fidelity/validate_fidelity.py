"""Runnable fidelity checks (run via `make validate`).

Against the GENERATED artifacts only (nothing hand-written here mirrors
the model — if generation breaks, this fails). What is being measured:

  1. The generated Pydantic union is a TRUE discriminated union: the
     RailPayload RootModel's root field carries discriminator='rail',
     and each member's rail is a Literal.
  2. A valid payload per rail validates and lands in the RIGHT member.
  3. Mislabeled payloads are rejected: a ticket SHAPE tagged rail='stay'
     and a stay SHAPE tagged rail='ticket' — the pair of cases that
     separates a discriminated union from a shape-guessing one.
  4. Unknown rail and merged-superset payloads are rejected.
  5. Optional fields: PayloadOwner.note omitted, and TicketPayload.gate
     omitted, both validate; gate present keeps its value.
  6. A member missing a required field is rejected.

Exit code 0 = all checks passed.
"""

from __future__ import annotations

import sys
import typing
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


import payloadowner_pydantic as gen  # noqa: E402


def structure() -> None:
    from pydantic import RootModel

    assert issubclass(gen.RailPayload, RootModel), "RailPayload is not a RootModel"
    root_field = gen.RailPayload.model_fields["root"]
    assert root_field.discriminator == "rail", (
        f"root field discriminator is {root_field.discriminator!r}, not 'rail' "
        "— the union is NOT discriminated in the generated Pydantic"
    )
    members = typing.get_args(root_field.annotation)
    assert len(members) == 2, f"union has {len(members)} members, expected 2"
    rails = set()
    for member in members:
        ann = member.model_fields["rail"].annotation
        args = typing.get_args(ann)
        assert len(args) == 1 and isinstance(args[0], str), (
            f"{member.__name__}.rail annotation is {ann!r}, not a single Literal"
        )
        rails.add(args[0])
    assert rails == {"ticket", "stay"}, f"member rail literals are {rails!r}"


check("generated union is discriminated (discriminator='rail', Literal member tags)", structure)


def owner(payload, **extra):
    return gen.PayloadOwner.model_validate({"label": "fidelity", "payload": payload, **extra})


def valid_ticket() -> None:
    inst = owner({"rail": "ticket", "seat": "7", "tier": "GA"})
    member = inst.payload.root
    assert type(member).__name__ == "RailPayload1", f"landed in {type(member).__name__}"
    assert member.seat == "7" and member.tier == "GA"
    assert member.gate is None, "omitted optional gate should default to None"


check("valid ticket payload validates into the ticket member (gate omitted)", valid_ticket)


def valid_stay() -> None:
    inst = owner({"rail": "stay", "phaseKind": "RECOVERY", "nights": 6})
    member = inst.payload.root
    assert type(member).__name__ == "RailPayload2", f"landed in {type(member).__name__}"
    assert member.phaseKind == "RECOVERY" and member.nights == 6


check("valid stay payload validates into the stay member", valid_stay)


def gate_present() -> None:
    inst = owner({"rail": "ticket", "seat": "7", "tier": "GA", "gate": "B12"})
    assert inst.payload.root.gate == "B12"


check("optional gate present keeps its value", gate_present)


def expect_rejected(label: str, payload, note_text: str) -> None:
    def fn() -> None:
        from pydantic import ValidationError

        try:
            owner(payload)
        except ValidationError:
            return
        raise AssertionError(f"{note_text} was ACCEPTED")

    check(label, fn)


expect_rejected(
    "ticket SHAPE tagged rail='stay' is rejected",
    {"rail": "stay", "seat": "7", "tier": "GA"},
    "mislabeled ticket shape",
)
expect_rejected(
    "stay SHAPE tagged rail='ticket' is rejected",
    {"rail": "ticket", "phaseKind": "RECOVERY", "nights": 6},
    "mislabeled stay shape",
)
expect_rejected(
    "unknown rail value is rejected",
    {"rail": "flight", "seat": "7", "tier": "GA"},
    "unknown-rail payload",
)
expect_rejected(
    "merged superset of both shapes is rejected",
    {"rail": "ticket", "seat": "7", "tier": "GA", "phaseKind": "RECOVERY", "nights": 6},
    "superset payload",
)
expect_rejected(
    "ticket payload missing required tier is rejected",
    {"rail": "ticket", "seat": "7"},
    "incomplete ticket payload",
)


def optionals() -> None:
    inst = owner({"rail": "stay", "phaseKind": "PRE_OP", "nights": 2})
    assert inst.note is None
    inst2 = owner({"rail": "stay", "phaseKind": "PRE_OP", "nights": 2}, note="window seat")
    assert inst2.note == "window seat"


check("optional owner.note omitted validates; present keeps its value", optionals)


print()
if failures:
    print(f"FIDELITY VALIDATION: {len(failures)} check(s) FAILED")
    sys.exit(1)
print("FIDELITY VALIDATION: all checks passed")
