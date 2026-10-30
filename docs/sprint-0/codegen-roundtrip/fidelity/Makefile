# Sprint 0 codegen FIDELITY CHECK (R4 review criterion 6) — generation sequence.
#
# Same chain as the reviewed round-trip in the parent directory; the ONLY
# hand-authored model file here is fidelity_models.py (SQLAlchemy 2.0).
# Every artifact below is GENERATED, and the generator chain reads:
#   bridge.py            READS fidelity_models.py (mapper introspection)
#                        WRITES payloadowner.schema.json
#   datamodel-codegen    READS payloadowner.schema.json (the bridge output)
#                        WRITES payloadowner_pydantic.py
#                        It never reads any Pydantic file, and no generated
#                        file is hand-edited anywhere in this directory —
#                        generation is destructive-by-default (full-file
#                        overwrite on every run), exactly as in the parent.
#   export_pydantic_schema.py
#                        READS the GENERATED payloadowner_pydantic.py
#                        (read-only) and WRITES its JSON Schema projection
#                        for the TypeScript step.
#   json-schema-to-typescript
#                        READS payloadowner_pydantic.schema.json
#                        WRITES payloadowner.ts
# base.py is a generation INPUT (shared frozen base class), not a model.
# bridge.py is a tool, not a model (a copy of the parent tool, pointed at
# the fidelity authoring module; mapping logic unchanged).
#
# Usage:
#   make all        # full regeneration from fidelity_models.py
#   make validate   # runnable fidelity checks against generated artifacts
#   make check-ts   # generated TypeScript type-checks standalone (tsc)
#
# Toolchain: same pinned installs as the parent round-trip
# (~/workspace/tools/codegenvenv, ~/workspace/tools/ts-tools).

PY      ?= $(HOME)/workspace/tools/codegenvenv/bin/python
CODEGEN ?= $(HOME)/workspace/tools/codegenvenv/bin/datamodel-codegen
NPX     ?= npx
TSC     ?= $(HOME)/workspace/tools/ts-tools/node_modules/.bin/tsc

.PHONY: all schema pydantic ts-schema typescript validate check-ts clean

all: typescript

schema: payloadowner.schema.json

payloadowner.schema.json: fidelity_models.py bridge.py
	$(PY) bridge.py PayloadOwner

pydantic: payloadowner_pydantic.py

payloadowner_pydantic.py: payloadowner.schema.json base.py
	$(CODEGEN) \
		--input payloadowner.schema.json \
		--input-file-type jsonschema \
		--output payloadowner_pydantic.py \
		--output-model-type pydantic_v2.BaseModel \
		--base-class base.FrozenModel \
		--target-python-version 3.12

ts-schema: payloadowner_pydantic.schema.json

payloadowner_pydantic.schema.json: payloadowner_pydantic.py export_pydantic_schema.py
	$(PY) export_pydantic_schema.py payloadowner_pydantic PayloadOwner

typescript: payloadowner.ts

payloadowner.ts: payloadowner_pydantic.schema.json
	$(NPX) --yes json-schema-to-typescript payloadowner_pydantic.schema.json -o payloadowner.ts --bannerComment "/* GENERATED from payloadowner_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: fidelity_models.py). */"

validate: all
	$(PY) validate_fidelity.py

check-ts: payloadowner.ts
	$(TSC) --noEmit --strict --target es2022 --module esnext --moduleResolution bundler payloadowner.ts

clean:
	rm -f payloadowner.schema.json payloadowner_pydantic.py payloadowner_pydantic.schema.json payloadowner.ts
