"""Bridge: SQLAlchemy model -> JSON Schema (mechanical introspection).

datamodel-code-generator does not read SQLAlchemy models directly; its
input is JSON Schema. This bridge is the mechanical link: it walks the
SQLAlchemy mapper and emits a JSON Schema deterministically. It is a TOOL,
authored once and applied to any model — it contains no per-field
hand-maintained copies of the model. The model in models.py remains the
single authoring source.

Mapping rules:
- Property names are the column (contract) names — the spec's camelCase.
- A column is "required" iff it is non-nullable AND has no default.
- Enum columns -> $defs entry {title: <EnumClassName>, type: string,
  enum: [values]}, property is a $ref. Enums stay enums downstream.
- A column type carrying a `json_schema` attribute (see PriceJSON in
  models.py) -> the fragment is placed in $defs under its title and the
  property is a $ref. This is how typed JSON is projected.
- DateTime -> {"type": "string", "format": "date-time"}.
- Plain JSON (no fragment) -> {"type": "object"} (free-form by design).
- Nullable -> anyOf [<schema>, {"type": "null"}].

Usage: python bridge.py [ModelClassName]  (default: OfferSnapshot)
Writes <modelname>.schema.json next to this file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, Integer, JSON, String
from sqlalchemy.orm import class_mapper

import models

HERE = Path(__file__).resolve().parent


def column_schema(col, defs: dict) -> dict:
    t = col.type

    # Typed JSON (or any type carrying a schema fragment): lift into $defs.
    fragment = getattr(t, "json_schema", None)
    if fragment is not None:
        title = fragment["title"]
        defs[title] = {k: v for k, v in fragment.items()}
        return {"$ref": f"#/$defs/{title}"}

    # Enums: named $defs entry so generators emit a named enum type.
    if isinstance(t, SAEnum) and t.enum_class is not None:
        title = t.enum_class.__name__
        defs[title] = {
            "title": title,
            "type": "string",
            "enum": [member.value for member in t.enum_class],
        }
        return {"$ref": f"#/$defs/{title}"}

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
    if isinstance(t, String):
        schema: dict = {"type": "string"}
        if t.length:
            schema["maxLength"] = t.length
        return schema

    raise TypeError(f"bridge: unmapped column type {t!r} on column {col.name!r}")


def model_to_json_schema(model_cls) -> dict:
    mapper = class_mapper(model_cls)
    defs: dict = {}
    properties: dict = {}
    required: list[str] = []

    for col in mapper.columns:
        schema = column_schema(col, defs)
        if col.nullable:
            schema = {"anyOf": [schema, {"type": "null"}]}
        properties[col.name] = schema
        if not col.nullable and col.default is None and col.server_default is None:
            required.append(col.name)

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": model_cls.__name__,
        "type": "object",
        "properties": properties,
        "required": required,
        "$defs": defs,
    }


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "OfferSnapshot"
    model_cls = getattr(models, name)
    schema = model_to_json_schema(model_cls)
    out = HERE / f"{name.lower()}.schema.json"
    out.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"bridge: wrote {out.name} from models.{name}")


if __name__ == "__main__":
    main()
