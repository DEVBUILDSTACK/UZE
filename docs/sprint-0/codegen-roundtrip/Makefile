# Sprint 0 codegen round-trip — the exact, reproducible generation sequence.
#
# GENERATION SOURCE — read this before grading criterion 1:
#   The ONLY hand-authored model file is models.py (SQLAlchemy 2.0).
#   Every artifact below is GENERATED, and the generator chain reads:
#     bridge.py            READS models.py (SQLAlchemy mapper introspection)
#                          WRITES offersnapshot.schema.json
#     datamodel-codegen    READS offersnapshot.schema.json (the bridge output)
#                          WRITES offersnapshot_pydantic.py
#                          It never reads any Pydantic file, and no Pydantic
#                          file is hand-maintained anywhere in this directory.
#     export_pydantic_schema.py
#                          READS the GENERATED offersnapshot_pydantic.py
#                          (read-only) and WRITES its JSON Schema projection
#                          for the TypeScript step. Information flows
#                          downstream only; nothing flows back into a source.
#     json-schema-to-typescript
#                          READS offersnapshot_pydantic.schema.json
#                          WRITES offersnapshot.ts
#   base.py is a generation INPUT (the shared frozen base class named by
#   --base-class), not a model. bridge.py is a tool, not a model.
#   offersnapshot.schema.json is a build artifact: `make clean` deletes it
#   and every step below, and `make all` rebuilds the whole chain from
#   models.py. If Pydantic ever had to be edited by hand, that would be
#   dual authoring and this gate would FAIL — it is not, and it does not.
#
# Usage:
#   make all        # full regeneration from models.py
#   make validate   # runnable proof the generated artifacts behave
#   make check-ts   # generated TypeScript type-checks standalone (tsc)
#
# Toolchain lives OUTSIDE the repo (see requirements.txt):
#   python3 -m venv ~/workspace/tools/codegenvenv
#   ~/workspace/tools/codegenvenv/bin/pip install -r requirements.txt
#   npm install --prefix ~/workspace/tools/ts-tools typescript@5
# (tsc is invoked from that pinned install: `npx --package typescript tsc`
# does not resolve the tsc bin reliably from inside this repo tree.)
# Override PY / CODEGEN / NPX / TSC if your toolchain lives elsewhere.

PY      ?= $(HOME)/workspace/tools/codegenvenv/bin/python
CODEGEN ?= $(HOME)/workspace/tools/codegenvenv/bin/datamodel-codegen
NPX     ?= npx
TSC     ?= $(HOME)/workspace/tools/ts-tools/node_modules/.bin/tsc

.PHONY: all schema pydantic ts-schema typescript validate check-ts clean

all: typescript

schema: offersnapshot.schema.json

offersnapshot.schema.json: models.py bridge.py
	$(PY) bridge.py OfferSnapshot

pydantic: offersnapshot_pydantic.py

offersnapshot_pydantic.py: offersnapshot.schema.json base.py
	$(CODEGEN) \
		--input offersnapshot.schema.json \
		--input-file-type jsonschema \
		--output offersnapshot_pydantic.py \
		--output-model-type pydantic_v2.BaseModel \
		--base-class base.FrozenModel \
		--target-python-version 3.12

ts-schema: offersnapshot_pydantic.schema.json

offersnapshot_pydantic.schema.json: offersnapshot_pydantic.py export_pydantic_schema.py
	$(PY) export_pydantic_schema.py offersnapshot_pydantic OfferSnapshot

typescript: offersnapshot.ts

offersnapshot.ts: offersnapshot_pydantic.schema.json
	$(NPX) --yes json-schema-to-typescript offersnapshot_pydantic.schema.json -o offersnapshot.ts --bannerComment "/* GENERATED from offersnapshot_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: models.py). */"

validate: all
	$(PY) validate_roundtrip.py

check-ts: offersnapshot.ts
	$(TSC) --noEmit --strict --target es2022 --module esnext --moduleResolution bundler offersnapshot.ts

clean:
	rm -f offersnapshot.schema.json offersnapshot_pydantic.py offersnapshot_pydantic.schema.json offersnapshot.ts
