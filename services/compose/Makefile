# UZEMARKETS composition layer — codegen for the full Sprint 0 schema.
#
# GENERATION SOURCE — the discipline is the reviewed round-trip's, verbatim:
#   The ONLY hand-authored model file is src/models.py (SQLAlchemy 2.0).
#   Every artifact under src/generated/ is GENERATED, and the chain reads:
#     src/bridge.py            READS src/models.py (mapper introspection)
#                              WRITES src/generated/<model>.schema.json
#     datamodel-codegen        READS src/generated/<model>.schema.json
#                              WRITES src/generated/<model>_pydantic.py
#                              (never reads a Pydantic file; no Pydantic
#                              file is hand-maintained anywhere here)
#     src/export_pydantic_schema.py
#                              READS the GENERATED <model>_pydantic.py
#                              (read-only) and WRITES its JSON Schema
#                              projection for the TypeScript step.
#     json-schema-to-typescript
#                              READS <model>_pydantic.schema.json
#                              WRITES src/generated/<model>.ts
#   Generation is DESTRUCTIVE-BY-DEFAULT: each tool overwrites its output
#   file wholesale on every run; `make clean` deletes every generated
#   artifact and `make all` rebuilds the entire chain from models.py.
#   src/base.py is a generation INPUT (the frozen base class named by
#   --base-class), not a model. bridge.py is a tool, not a model.
#   The codegen invocation is EXACTLY the reviewed chain's — no added
#   flags (the union member-naming question, e.g. --use-title-as-name,
#   is a schema-review decision, not a silent change).
#
# Usage:
#   make all        # full regeneration of every model from src/models.py
#   make validate   # Sprint 0 demo: migration + mechanism demonstrations
#   make check-ts   # generated TypeScript type-checks standalone (tsc)
#
# Toolchain lives OUTSIDE the repo (see requirements.txt):
#   ~/workspace/tools/codegenvenv (sqlalchemy / pydantic / datamodel-codegen
#   / alembic / psycopg) and ~/workspace/tools/ts-tools (typescript).

PY      ?= $(HOME)/workspace/tools/codegenvenv/bin/python
CODEGEN ?= $(HOME)/workspace/tools/codegenvenv/bin/datamodel-codegen
NPX     ?= npx
TSC     ?= $(HOME)/workspace/tools/ts-tools/node_modules/.bin/tsc

GEN := src/generated

# ClassName:filestem for every model in src/models.py.
MODELS := IntakeDraft:intakedraft TripProfile:tripprofile Traveler:traveler \
  GeoAnchor:geoanchor MetroProfile:metroprofile StayPhase:stayphase \
  SearchSession:searchsession TripCandidate:tripcandidate \
  OfferSnapshot:offersnapshot ApprovalRequest:approvalrequest \
  Commitment:commitment EventLog:eventlog IdempotencyKey:idempotencykey \
  QuestionManifest:questionmanifest ServiceTask:servicetask \
  DiningTask:diningtask TransferTask:transfertask \
  ConciergeBrief:conciergebrief FacilityProfile:facilityprofile \
  PackageTemplate:packagetemplate ProcedureClassBand:procedureclassband \
  ConsentRecord:consentrecord HealthAttribute:healthattribute

.PHONY: all pydantic typescript validate check-ts clean

all: typescript

pydantic:
	@set -e; for pair in $(MODELS); do \
	  cls=$${pair%%:*}; stem=$${pair##*:}; \
	  PYTHONPATH=src $(PY) src/bridge.py $$cls; \
	  $(CODEGEN) \
	    --input $(GEN)/$$stem.schema.json \
	    --input-file-type jsonschema \
	    --output $(GEN)/$$stem\_pydantic.py \
	    --output-model-type pydantic_v2.BaseModel \
	    --base-class base.FrozenModel \
	    --target-python-version 3.12; \
	done

typescript: pydantic
	@set -e; for pair in $(MODELS); do \
	  cls=$${pair%%:*}; stem=$${pair##*:}; \
	  PYTHONPATH=src $(PY) src/export_pydantic_schema.py $$stem\_pydantic $$cls; \
	  $(NPX) --yes json-schema-to-typescript $(GEN)/$$stem\_pydantic.schema.json -o $(GEN)/$$stem.ts --bannerComment "/* GENERATED from $$stem\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */"; \
	done

validate:
	@set -o pipefail; $(PY) scripts/demo_schema.py 2>&1 | tee evidence/demo_run.log

check-ts: typescript
	$(TSC) --noEmit --strict --target es2022 --module esnext --moduleResolution bundler $(GEN)/*.ts

clean:
	rm -f $(GEN)/*.schema.json $(GEN)/*_pydantic.py $(GEN)/*.ts
