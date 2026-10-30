# services/compose — UZEMARKETS composition layer

The composition layer of the UZEMARKETS commerce platform: it composes
offers over the services/api catalog (which it consumes — it owns no
catalog entities), freezes quotes as OfferSnapshots, runs the human
approval gate, and records commitments. Database: **`uzemarkets-compose`**
(its own Postgres database, per the ratified data-core decision).

## Layout

- `src/models.py` — the SINGLE authoring source (SQLAlchemy 2.0). Every
  other model artifact is generated from it.
- `src/config.py` — connection config; names the database
  `uzemarkets-compose` (`COMPOSE_DATABASE_URL` overrides the URL, never
  silently the name's meaning). `.env.example` mirrors it. No secrets.
- `src/bridge.py`, `src/export_pydantic_schema.py`, `src/base.py` — the
  reviewed codegen chain (see the Makefile header for the discipline).
- `src/generated/` — GENERATED Pydantic + TypeScript + schemas. Never
  hand-edit: regeneration is destructive-by-default.
- `alembic/` + `alembic.ini` — migration authority (SQLAlchemy + Alembic,
  the ratified (C) pattern). Additive-only from the initial revision
  forward. The initial revision also carries the hand-written
  enforcement DDL: the OfferSnapshot immutability trigger and the
  EventLog append-only trigger.
- `scripts/demo_schema.py` — the Sprint 0 demonstration (see below).
- `evidence/demo_run.log` — its committed output.
- `SCHEMA-NOTES.md` — self-grade against the eleven pre-committed
  schema-review criteria + every AUTHOR'S CHOICE awaiting ratification.

## Commands

Toolchain lives outside the repo (pinned in `requirements.txt`):
`~/workspace/tools/codegenvenv` (Python) and `~/workspace/tools/ts-tools`
(TypeScript). The Makefile defaults point there.

- `make all` — regenerate every artifact from `src/models.py`
  (the chain invocation is exactly the reviewed round-trip's — no added
  flags; the union member-naming question is a schema-review decision,
  see SCHEMA-NOTES choice 13).
- `make check-ts` — generated TypeScript type-checks standalone.
- `make validate` — run the demonstration: resets a throwaway local
  database named `uzemarkets-compose` (guard enforced in the script),
  migrates it with Alembic, and exercises the mechanisms — OfferSnapshot
  immutability, EventLog append-only, idempotency uniqueness, payload
  union + typed divergence validation, sourceRef-as-reference, dormant
  namespace isolation. Output is tee'd to `evidence/demo_run.log`.
  The substrate is a real local PostgreSQL (see SCHEMA-NOTES).

## Standing constraints

- Do not add codegen flags or change the chain without a review decision.
- Migrations are additive-only; never edit a shipped revision.
- Nothing here references services/api tables — the boundary is the
  Read-Through Contract (R4): references by value (`sourceRef`), typed
  divergence, commit-time reconciliation only.
