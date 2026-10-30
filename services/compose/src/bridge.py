"""Bridge: SQLAlchemy models -> JSON Schema (mechanical introspection).

The reviewed chain's link tool (docs/sprint-0/codegen-roundtrip/bridge.py),
carried into the service unchanged in discipline and extended with the two
mapping rules full-schema authoring was always going to need (both were
named in advance: the round-trip README's ARRAY note, and relationships):

- datamodel-code-generator does not read SQLAlchemy models directly; its
  input is JSON Schema. This bridge walks the SQLAlchemy mapper and emits
  a JSON Schema deterministically. It contains NO per-field hand-maintained
  copies of any model. models.py remains the single authoring source.

Mapping rules (demo rules, unchanged):
- Property names are the column (contract) names — the spec's camelCase.
- A column is "required" iff it is non-nullable AND has no default.
- Enum columns -> $defs entry {title: <EnumClassName>, type: string,
  enum: [values]}, property is a $ref. Enums stay enums downstream.
- A column type carrying a `json_schema` attribute -> the fragment is
  placed in $defs under its title and the property is a $ref (typed JSON).
- DateTime -> {"type": "string", "format": "date-time"}.
- Plain JSON (no fragment) -> {"type": "object"} (free-form by design).
- Nullable -> anyOf [<schema>, {"type": "null"}].

Mapping rules (added for the full schema):
- ARRAY columns -> {"type": "array", "items": <item schema>}; an enum
  item type becomes a $ref to the enum's $defs entry. This is what keeps
  TripProfile.modules and IntakeDraft.missingSlots array-typed through
  the projection (and StayPhase[] array-typed at the model level, below).
- One-to-many relationships (uselist) -> an array property named by the
  camelCase relationship key, items a $ref to the child's $defs entry.
  The child def is the child's COLUMN shape only (depth 1: the child's
  own relationships are not expanded, so the projection cannot cycle).
  This is what makes TripProfile.stayPhases / .travelers arrays of rows
  in the generated surface, not counts and not a collapsed single stay.
  Many-to-one relationships are NOT emitted: the FK id column already
  carries the reference.

Usage: python bridge.py [ModelClassName]  (default: OfferSnapshot)
Writes generated/<modelname>.schema.json under this file's directory.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import class_mapper

import models

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "generated"


def _camel(snake: str) -> str:
    head, *tail = snake.split("_")
    return head + "".join(part.title() for part in tail)


def _type_schema(t, defs: dict) -> dict:
    """Schema for a bare SQLAlchemy type (column type or ARRAY item type)."""
    fragment = getattr(t, "json_schema", None)
    if fragment is not None:
        title = fragment["title"]
        defs[title] = {k: v for k, v in fragment.items()}
        return {"$ref": f"#/$defs/{title}"}

    if isinstance(t, SAEnum) and t.enum_class is not None:
        title = t.enum_class.__name__
        defs[title] = {
            "title": title,
            "type": "string",
            "enum": [member.value for member in t.enum_class],
        }
        return {"$ref": f"#/$defs/{title}"}

    if isinstance(t, ARRAY):
        return {"type": "array", "items": _type_schema(t.item_type, defs)}
    if isinstance(t, DateTime):
        return {"type": "string", "format": "date-time"}
    if isinstance(t, Boolean):
        return {"type": "boolean"}
    if isinstance(t, Integer):
        return {"type": "integer"}
    if isinstance(t, Float):
        return {"type": "number"}
    if isinstance(t, JSON):
        return {"type": "object"}
    if isinstance(t, (String, Text)):
        schema: dict = {"type": "string"}
        if getattr(t, "length", None):
            schema["maxLength"] = t.length
        return schema

    raise TypeError(f"bridge: unmapped type {t!r}")


def column_schema(col, defs: dict) -> dict:
    try:
        return _type_schema(col.type, defs)
    except TypeError:
        raise TypeError(
            f"bridge: unmapped column type {col.type!r} on column {col.name!r}"
        ) from None


def _object_schema(model_cls, defs: dict, include_relationships: bool) -> dict:
    mapper = class_mapper(model_cls)
    properties: dict = {}
    required: list[str] = []

    for col in mapper.columns:
        schema = column_schema(col, defs)
        if col.nullable:
            schema = {"anyOf": [schema, {"type": "null"}]}
        properties[col.name] = schema
        if not col.nullable and col.default is None and col.server_default is None:
            required.append(col.name)

    if include_relationships:
        for rel in mapper.relationships:
            if not rel.uselist:
                continue  # many-to-one: the FK id column already carries it
            child_cls = rel.mapper.class_
            child_title = child_cls.__name__
            if child_title not in defs:
                defs[child_title] = _object_schema(child_cls, defs, False)
            properties[_camel(rel.key)] = {
                "type": "array",
                "items": {"$ref": f"#/$defs/{child_title}"},
            }

    return {
        "title": model_cls.__name__,
        "type": "object",
        "properties": properties,
        "required": required,
    }


def model_to_json_schema(model_cls) -> dict:
    defs: dict = {}
    body = _object_schema(model_cls, defs, include_relationships=True)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **body,
        "$defs": defs,
    }


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "OfferSnapshot"
    model_cls = getattr(models, name)
    schema = model_to_json_schema(model_cls)
    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"{name.lower()}.schema.json"
    out.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"bridge: wrote {out.name} from models.{name}")


if __name__ == "__main__":
    main()
