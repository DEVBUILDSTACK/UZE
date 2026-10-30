"""Export the GENERATED Pydantic model's JSON Schema.

This is the input to the TypeScript step, so the TS types are generated
from the same Pydantic model the agent/API side uses — one projection
chain, no parallel hand-written schema.

Usage: python export_pydantic_schema.py [ModuleName] [ClassName]
Defaults: offersnapshot_pydantic / OfferSnapshot
Writes <module>.schema.json next to this file.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def main() -> None:
    module_name = sys.argv[1] if len(sys.argv) > 1 else "offersnapshot_pydantic"
    class_name = sys.argv[2] if len(sys.argv) > 2 else "OfferSnapshot"
    module = importlib.import_module(module_name)
    model_cls = getattr(module, class_name)
    schema = model_cls.model_json_schema()
    out = HERE / f"{module_name}.schema.json"
    out.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"export: wrote {out.name} from {module_name}.{class_name}")


if __name__ == "__main__":
    main()
