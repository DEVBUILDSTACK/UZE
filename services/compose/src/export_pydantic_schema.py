"""Export a GENERATED Pydantic model's JSON Schema.

This is the input to the TypeScript step, so the TS types are generated
from the same Pydantic models the agent/API side uses — one projection
chain, no parallel hand-written schema. (Same tool as the reviewed
round-trip; the only change is where generated modules live.)

Usage: python export_pydantic_schema.py [ModuleStem] [ClassName]
  ModuleStem: file stem inside src/generated (e.g. offersnapshot_pydantic)
  ClassName:  the model class (e.g. OfferSnapshot)
Writes src/generated/<modulestem>.schema.json.

Branded DateTime (Sprint 1 slice 3 — the criterion-3 caveat's tracked
item, discharged here): TypeScript renders datetimes as plain
`string`, which lets any string flow into a datetime field at the
approval surface. For the approval-facing modules named in
BRANDED_DATETIME_STEMS, this step rewrites every date-time property
in the exported schema into a reference to a branded `DateTime`
definition BEFORE json-schema-to-typescript sees it:

  - the schema gains `$defs/DateTime` carrying a `tsType` override,
    which json-schema-to-typescript emits verbatim, so the
    generated module declares
        export type DateTime = string & {readonly __brand: "DateTime"};
  - a non-nullable date-time property becomes
    {"$ref": "#/$defs/DateTime"}; a nullable one (an anyOf with a
    null branch) becomes anyOf [$ref, {"type": "null"}] and renders
    as `DateTime | null`.

The brand is a literal-tag intersection: a plain string is NOT
assignable to DateTime, so datetime fields cannot silently receive
arbitrary strings; DateTime remains a string at runtime (the API
renders ISO strings — the brand is asserted once, at the surface's
data boundary). This tool is a chain INPUT: no generated file is
hand-edited, regeneration reproduces the branded artifacts, and the
step FAILS THE BUILD if a branded module's schema carries no
date-time properties — the brand must never silently disappear.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEN_DIR = HERE / "generated"
sys.path.insert(0, str(HERE))  # for `base` (the generated models' base class)
sys.path.insert(0, str(GEN_DIR))

# The approval-facing modules: the gate's own record (ApprovalRequest,
# with Commitment inlined) and its subject (OfferSnapshot — the
# createdAt/expiresAt the staleness display renders).
BRANDED_DATETIME_STEMS = {"approvalrequest_pydantic", "offersnapshot_pydantic"}

BRANDED_DATETIME_DEF = {
    "title": "DateTime",
    "type": "string",
    "tsType": 'string & { readonly __brand: "DateTime" }',
}

_DATETIME_REF = {"$ref": "#/$defs/DateTime"}


def _branded_property(prop: object) -> dict | None:
    """The branded replacement for a date-time property schema, or
    None if `prop` is not a date-time property. Detection is by the
    `date-time` format marker, wherever the property carries it:
    directly, or on a branch of its anyOf/oneOf (the nullable
    rendering)."""
    if not isinstance(prop, dict):
        return None
    if prop.get("format") == "date-time":
        return dict(_DATETIME_REF)
    for key in ("anyOf", "oneOf"):
        branches = prop.get(key)
        if isinstance(branches, list) and any(
            isinstance(b, dict) and b.get("format") == "date-time"
            for b in branches
        ):
            nullable = any(
                isinstance(b, dict) and b.get("type") == "null" for b in branches
            )
            if nullable:
                return {"anyOf": [dict(_DATETIME_REF), {"type": "null"}]}
            return dict(_DATETIME_REF)
    return None


def _brand_datetimes(schema: dict) -> int:
    """Rewrite every date-time property in the schema, in place;
    return how many were rewritten."""
    count = 0

    def walk(node: object) -> None:
        nonlocal count
        if isinstance(node, dict):
            props = node.get("properties")
            if isinstance(props, dict):
                for name, prop in list(props.items()):
                    branded = _branded_property(prop)
                    if branded is not None:
                        props[name] = branded
                        count += 1
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    return count


def main() -> None:
    module_name = sys.argv[1] if len(sys.argv) > 1 else "offersnapshot_pydantic"
    class_name = sys.argv[2] if len(sys.argv) > 2 else "OfferSnapshot"
    module = importlib.import_module(module_name)
    model_cls = getattr(module, class_name)
    schema = model_cls.model_json_schema()
    if module_name in BRANDED_DATETIME_STEMS:
        rewritten = _brand_datetimes(schema)
        if rewritten == 0:
            raise SystemExit(
                f"export: {module_name} is a branded-datetime module but "
                "its schema carries no date-time properties — refusing "
                "to export an unbranded schema (the brand must not "
                "silently disappear)"
            )
        schema.setdefault("$defs", {})["DateTime"] = BRANDED_DATETIME_DEF
        print(
            f"export: branded {rewritten} date-time properties "
            f"in {module_name} as DateTime"
        )
    out = GEN_DIR / f"{module_name}.schema.json"
    out.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"export: wrote {out.name} from {module_name}.{class_name}")


if __name__ == "__main__":
    main()
