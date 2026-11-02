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
- `src/classify.py` — Sprint 1: the deterministic intake classifier
  (directive 4 — no LLM, structurally; its docstring files the
  dependsOn semantics, the honored validation subset, and the precise
  module-readiness rule).
- `src/suggest.py` — Sprint 1: suggest_slots(), the ONLY seam where
  an LLM may be consulted (directive 4). Providers are deterministic
  and local in this slice; every proposal is validated back through
  classify() and never auto-applied.
- `src/app.py` + `src/intakes.py` + `src/db.py` — Sprint 1: the
  intake service (FastAPI): `GET /health` (DB connectivity + schema
  head revision), `POST /intakes`, `GET /intakes/{id}`,
  `POST /intakes/{id}/answers`.
- `src/upstream.py` — Sprint 1 slice 2: the reconciliation reader.
  Exactly two reads (Ticket by id, Listing by id) behind one
  interface: the direct HTTP reader (post-redeploy drop-in), the
  interim listing-read proxy (pre-redeploy stand-in, tests/dev
  only), and an honest unavailable reader when no upstream is
  configured. Scoped to commit-path reconciliation only.
- `src/readthrough.py` — Sprint 1 slice 2: the R4 §6 reconciliation
  evaluator — TTL first (TTL dominance), the eight §5 codes wired
  to the filed firing map, EventLog recording of every raised code,
  the divergence annotation for killing codes, and the SEAT_TAKEN
  `reason` (MODERATION | DOUBLE_SETTLEMENT) on the record and in
  the result.
- `src/snapshots.py` — Sprint 1 slice 2: `POST
  /snapshots/{snapshot_id}/reconcile` (200 CLEAN / 409 DIVERGED /
  503 BLOCKED).
- `src/approvals.py` — Sprint 1 slice 3: the human approval gate.
  `POST /approvals` (a PENDING ApprovalRequest for one ticket-kind
  snapshot; trip + commitment class derived from the snapshot),
  `GET /approvals/{id}` (read-through: reconciles at request time
  and carries the snapshot's freshness/staleness state), and
  `POST /approvals/{id}/decision` (APPROVE | REJECT, gated by a
  fresh reconciliation — a diverged snapshot cannot be approved,
  expiry refuses as SNAPSHOT_EXPIRED, upstream failure blocks
  without killing the request). Commitment recording is the
  remaining Sprint 1 slice and is not mounted.
- `src/seed.py` + `scripts/seed_manifest.py` — the Sprint 1 seed
  QuestionManifest (six slots exercising every classifier path),
  loaded idempotently by manifest key.
- `tests/` — pytest for the runtime (substrate: the same real local
  PostgreSQL as the demo — see `tests/conftest.py`).
- `requirements-runtime.txt` — the runtime pins (FastAPI service +
  tests), kept separate from the codegen toolchain's
  `requirements.txt`.

## Commands

Toolchain lives outside the repo (pinned in `requirements.txt`):
`~/workspace/tools/codegenvenv` (Python) and `~/workspace/tools/ts-tools`
(TypeScript). The Makefile defaults point there. The Sprint 1 runtime
has its own venv — `~/workspace/tools/composevenv`, pinned in
`requirements-runtime.txt`.

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
- `make test` — the Sprint 1 runtime tests (pytest, composevenv):
  classifier determinism + the directive-4 no-LLM import proof, the
  intake flow end-to-end (readiness flips), suggest_slots()
  validation, and the slice-2 read-through reconciliation suite
  (all eight divergence codes, the moderated-listing fixture,
  TTL dominance, block-without-kill) — against the same real
  PostgreSQL substrate, with the upstream source of record served
  by the interim listing-read proxy.
- Run the intake service:
  `PYTHONPATH=src:src/generated ~/workspace/tools/composevenv/bin/uvicorn app:app --port 8100`
  (seed first with `scripts/seed_manifest.py` under the same venv).

## Standing constraints

- Do not add codegen flags or change the chain without a review decision.
- Migrations are additive-only; never edit a shipped revision.
- Nothing here references services/api tables — the boundary is the
  Read-Through Contract (R4): references by value (`sourceRef`), typed
  divergence, commit-time reconciliation only.
