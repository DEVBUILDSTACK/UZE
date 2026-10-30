# Codegen Fidelity Check — Discriminated Unions + Optionals (Criterion 6)

**Why this exists.** The round-trip in the parent directory passed review
on a flat model. The R4 review added criterion 6: before schema authoring
writes `OfferSnapshot.payload` per rail, the chain must be tested on the
case it has not met — a **discriminated union**. R4 specifies payload
structure per rail, which is a discriminated union by design (the `rail`
field selects the shape). If the chain dropped the discriminator, schema
authoring would discover it in the schema instead of in a test.

**Verdict: the chain is VALIDATED for per-rail payload authoring.**
The discriminator survives the full chain and validation behaves
correctly (see per-check results). One gap, cosmetic not semantic:
generated member types are numbered (`RailPayload1/2`), not named
(`TicketPayload/StayPayload`) — with a probe-verified generation-side fix
named in Finding 1 for the schema review. Nothing was hand-patched.

## What was tested

Authoring source: `fidelity_models.py` — a demo carrier, `PayloadOwner`:

- `payload` — a JSON column via `RailPayloadJSON`, a `TypeDecorator`
  carrying the union as a `json_schema` fragment in the authoring source
  (the parent round-trip's Price pattern, so it survives regeneration).
  The fragment declares `oneOf` over two inline member schemas and the
  `discriminator: {propertyName: "rail"}` keyword:
  - **TicketPayload** — `rail: const "ticket"`, `seat` + `tier` required,
    **`gate` optional** (the optional field inside a member),
    `additionalProperties: false`.
  - **StayPayload** — `rail: const "stay"`, `phaseKind` + `nights`
    required, `additionalProperties: false`.
- `note` — a nullable column (the optional top-level field).
- Members are inline in the fragment because the bridge lifts exactly one
  fragment per column type into `$defs`; the fragment is self-contained.

## The chain (unchanged from the reviewed round-trip)

```
fidelity_models.py  (SQLAlchemy 2.0.40 — single authoring source)
  -> bridge.py            mapper introspection -> payloadowner.schema.json
  -> datamodel-code-generator 0.87.0
                          -> payloadowner_pydantic.py  (Pydantic 2.14.2)
  -> export_pydantic_schema.py   model_json_schema()
                          -> payloadowner_pydantic.schema.json
  -> json-schema-to-typescript -> payloadowner.ts
```

`bridge.py`, `base.py`, `export_pydantic_schema.py` are copies of the
parent tools (the bridge copy differs only in which authoring module it
reads; mapping logic identical). The parent directory's reviewed
artifacts are untouched.

## Commands (committed in the Makefile)

```
make all        # full regeneration from fidelity_models.py
make validate   # validate_fidelity.py — 10 behavior checks
make check-ts   # tsc --strict on the generated TypeScript
make clean      # deletes every generated artifact
```

Generation is destructive-by-default, as in the parent: every step
overwrites its output file in full; no generated file is an input to its
own generation; nothing here was edited after generation. Toolchain
pinned in `requirements.txt` (same pins as the parent). Full run
transcript: `evidence/fidelity_run.log`.

## Results, check by check

**1. Discriminator — PRESERVED, as a true discriminated union.**
datamodel-code-generator honored the fragment's `discriminator` keyword
and emitted:

```python
class RailPayload(RootModel[RailPayload1 | RailPayload2]):
    root: RailPayload1 | RailPayload2 = Field(..., discriminator='rail', ...)
```

Each member's `rail` is a `Literal` (`Literal['ticket']` /
`Literal['stay']`). `validate_fidelity.py` asserts the discriminator
programmatically (`model_fields['root'].discriminator == 'rail'`), not
just by reading the file. Behavior evidence (all in the run log):

- Valid ticket payload lands in the ticket member; valid stay payload in
  the stay member.
- **Ticket SHAPE tagged `rail='stay'` — rejected.** **Stay SHAPE tagged
  `rail='ticket'` — rejected.** This pair is the discriminating evidence:
  dispatch is by tag, so a mislabeled payload cannot validate against the
  member its shape matches.
- Unknown rail (`'flight'`), a merged superset of both shapes, and a
  member missing a required field — all rejected (closed shapes:
  `additionalProperties: false` in the fragment, `extra='forbid'` via the
  shared frozen base class).

**2. Optionals — PRESERVED at both levels.**
`gate` (inside the ticket member) and `note` (owner column) generate as
`str | None = None` in Pydantic and as optional properties (`gate?:`,
`note?:`) in TypeScript. Omitting either validates; supplying either
keeps its value (checked).

**3. TypeScript union — a real union of member interfaces.**
`export type RailPayload = RailPayload1 | RailPayload2`, and each member
interface carries its rail as a literal type (`rail: "ticket"` /
`rail: "stay"` via the `Rail`/`Rail1` aliases), so TypeScript narrowing
on `.rail` works — the TS union is itself discriminated, not `any`, not
`object`, not a merged interface. `make check-ts` passes under
`tsc --strict` with zero hand edits.

**4. Validation suite — 10/10 PASS** (`evidence/fidelity_run.log`).

## Finding 1 — member names are numbered, not named (cosmetic; fix named)

The fragment's member `title`s (`TicketPayload`, `StayPayload`) are NOT
used as class/interface names by datamodel-code-generator for inline
`oneOf` members under the reviewed invocation: the members generate as
`RailPayload1` / `RailPayload2` (parent-union title + index) in both
Pydantic and TypeScript. Semantics are unaffected — discrimination,
literals, and validation are all correct — but at full-schema scale,
numbered per-rail types hurt contract readability and diff stability
(inserting a member renumbers nothing, but reordering members would
rename types).

Restoration mechanism, **probe-verified but NOT applied** (applying it
changes the reviewed chain invocation — a schema-review decision, not
this check's): adding `--use-title-as-name` to the datamodel-codegen
invocation produced `class TicketPayload` / `class StayPayload` with
`discriminator='rail'` intact. (Probe output was inspected and deleted;
it is not a committed artifact.) The alternative generation-side
mechanism is a bridge change — emit union members as named top-level
`$defs` entries instead of inline fragment members. Either fix is
generation-side; hand-renaming generated files would violate
destructive-by-default and was not done.

## Notes

- The fragment uses `oneOf` (the canonical discriminated-union form);
  the exported Pydantic schema re-expresses the union via `$defs` +
  `$ref`, which is what json-schema-to-typescript consumed.
- The parent round-trip's cosmetic alias-casing quirk on the TS side
  persists here (`Phasekind`, `Createdat` type aliases; interface
  property names remain exact contract camelCase). Same standing note as
  the parent README: do not hand-"fix" generated files.
- Scope: demo models only. No schema was authored, and nothing outside
  this directory was changed.
