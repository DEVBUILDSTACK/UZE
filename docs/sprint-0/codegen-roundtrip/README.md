# Sprint 0 — Codegen Round-Trip Gate: DEMONSTRATED

**Gate (ratified by James, 2026-10-30):** ORM (C) — SQLAlchemy 2.0 + Alembic
end-to-end — with the prerequisite that the codegen tool be NAMED and one
round-trip (SQLAlchemy model → Pydantic → TypeScript) DEMONSTRATED before
any schema authoring begins. This directory is that demonstration, run on
the single model **OfferSnapshot**. It is a proof, not the build: no other
model is authored here.

## The named codegen path

```
models.py  (SQLAlchemy 2.0.40 declarative — THE single authoring source)
  │  bridge.py — mapper introspection, emits JSON Schema mechanically
  ▼
offersnapshot.schema.json            (generated; deleted by `make clean`)
  │  datamodel-code-generator 0.87.0 (--output-model-type pydantic_v2.BaseModel,
  │                                   --base-class base.FrozenModel)
  ▼
offersnapshot_pydantic.py            (generated Pydantic v2 — agent manifest side)
  │  export_pydantic_schema.py — dumps the generated model's model_json_schema()
  ▼
offersnapshot_pydantic.schema.json   (generated)
  │  json-schema-to-typescript (via npx)
  ▼
offersnapshot.ts                     (generated TypeScript — human client side)
```

Versions match the Assurative V2 pattern: SQLAlchemy 2.0.40, Pydantic v2
(2.14.2), Python 3.12. SQLModel was **not** used and was not needed — the
primary path worked, so no fallback was taken and no validation was loosened
anywhere (no `Any` where the spec fixes a shape).

### Who reads what (criterion 1 — single authoring source)

| Step | Reads | Writes |
|---|---|---|
| `bridge.py` | `models.py` (SQLAlchemy mapper, introspected) | `offersnapshot.schema.json` |
| `datamodel-codegen` | `offersnapshot.schema.json` (bridge output only) | `offersnapshot_pydantic.py` |
| `export_pydantic_schema.py` | the GENERATED `offersnapshot_pydantic.py` (read-only) | `offersnapshot_pydantic.schema.json` |
| `json-schema-to-typescript` | `offersnapshot_pydantic.schema.json` | `offersnapshot.ts` |

No Pydantic or TypeScript file is hand-maintained, and nothing flows back
upstream. `base.py` is a generation *input* (the shared frozen base class),
`bridge.py` is a *tool*; neither is a model. The exact sequence is the
committed `Makefile`: `make all` (regenerate), `make validate` (proof),
`make check-ts` (strict tsc). Toolchain: `requirements.txt` (venv at
`~/workspace/tools/codegenvenv`) + pinned TypeScript 5.9.3
(`npm install --prefix ~/workspace/tools/ts-tools typescript@5`).

The demo model's field shape is faithful to the imported spec
(`docs/UZEMARKETS-DATA-FIRST-BUILD-PLAN-IMPORTED-DRAFT-v0.1.md`):
`id, tripCandidateId, rail, sourceRef, commitmentClass, price, terms,
payload, expiresAt, createdAt` + the propagation field `retentionUntil`
(see below). Two stated demo-scope reductions: `tripCandidateId` carries its
spec index but not the FK (single-table demo; the FK lands when the full
schema is authored), and no Alembic revision is generated — migrations are
DDL, not part of the type-projection gate; they begin with Sprint 0 schema
authoring against the `uzemarkets-compose` database.

## Hard cases (criterion 3) — how each is handled

**Typed JSON (`price`).** The spec fixes the shape
`{ amount, currency, taxesIncluded }`, so `Any`/`dict` would be a fail.
Mechanism: the SQLAlchemy type for the column is a `TypeDecorator`
(`PriceJSON` in `models.py`) that *carries its JSON Schema fragment on the
type, in the authoring source*. The bridge lifts the fragment into the JSON
Schema `$defs`; datamodel-codegen then emits a real nested model
(`class Price(FrozenModel)` with `amount: float, currency: str,
taxesIncluded: bool`, `extra='forbid'`), and the TS step emits a matching
`Price` interface. Because the fragment lives in `models.py`, it survives
every regeneration — nothing is patched into a generated file. Validation
proves it behaviorally: a price missing `currency` is rejected
(`validate_roundtrip.py`). Free-form JSON columns (`terms`, `payload`) stay
`dict[str, Any]` **by design** — the spec leaves their shape rail-specific —
and get the same TypeDecorator treatment the day a rail fixes their shape.

**Enums.** `Rail` and `CommitmentClass` are Python enums in `models.py` →
named `$defs` in the bridge schema → `StrEnum` classes in the generated
Pydantic (values byte-identical) → string **union types** in TS
(`type Rail = "SOLANA_NFT" | "HOTEL_AGGREGATOR" | …`). Never stringly-typed;
an unknown rail value is rejected at validation (proven in the check run).

**Timestamps.** SQLAlchemy `DateTime(timezone=True)` → bridge
`{"format": "date-time"}` → Pydantic `AwareDatetime` (a real, tz-aware
`datetime` — proven in the check run). **Caveat, stated plainly:** on the
TypeScript side the fields are `string`. JSON has no datetime type;
`json-schema-to-typescript` emits plain `string` and does not surface the
`date-time` format (the format *is* retained in both JSON Schemas). TS
consumers therefore handle ISO-8601 strings — the normal Next.js wire
reality — while the domain/API side (SQLAlchemy → Pydantic) is fully
datetime-typed. If a branded TS datetime type is ever wanted, it is a
post-generation wrapper decision for Sprint 0, not something to fake here.

**Immutability.** OfferSnapshot is semantically insert-only (price/terms
frozen at quote). The round-trip carries it at three levels:
1. **Generated Pydantic is frozen** — `datamodel-codegen` runs with
   `--base-class base.FrozenModel` (`ConfigDict(frozen=True,
   extra="forbid")`), so the frozen config is a generation input that
   survives regeneration, and it applies to nested models (`Price`) too.
   Proven: mutation of a validated snapshot *and* its nested price raises
   `ValidationError`.
2. **ORM guard (in `models.py`, demonstrated)** — `before_update` /
   `before_delete` mapper events raise `RuntimeError` on any UPDATE/DELETE
   flush. Proven against SQLite: insert commits, update flush raises,
   delete flush raises.
3. **DB level (stated mechanism, for writers that bypass the ORM)** — in
   the `uzemarkets-compose` Postgres, belt-and-braces:
   ```sql
   CREATE OR REPLACE FUNCTION offer_snapshot_immutable() RETURNS trigger AS $$
   BEGIN RAISE EXCEPTION 'offer_snapshot is append-only'; END;
   $$ LANGUAGE plpgsql;
   CREATE TRIGGER trg_offer_snapshot_no_update
     BEFORE UPDATE OR DELETE ON offer_snapshot
     FOR EACH ROW EXECUTE FUNCTION offer_snapshot_immutable();
   ```
   (Not executed in this gate — no Postgres in the demo environment; the
   ORM guard above is the demonstrated layer.)

## Change propagation (criterion 2) — evidence

`evidence/reproduce_propagation.sh` runs the whole proof in one transcript
(`evidence/propagation_transcript.log`):

- **Phase 1:** `models.py` = `evidence/models_before.py` (no
  `retentionUntil`) → full regeneration → the field is **absent** from both
  generated artifacts (snapshotted in `evidence/before/`).
- **The edit:** `evidence/models_after.py` — byte-identical except the
  `retentionUntil` column (the edit itself:
  `evidence/propagation_models.diff`). The field is additive/nullable and on
  the spec's own roadmap ("OfferSnapshot retention columns").
- **Phase 2:** same `make all`, zero hand edits to generated files → the
  field appears in both artifacts (`evidence/after/`):
  `retentionUntil: AwareDatetime | None = None` (Pydantic) and
  `retentionUntil?: Retentionuntil` (TS interface). Artifact diff:
  `evidence/propagation.diff`.
- Validation + strict `tsc` then run against the regenerated artifacts:
  all checks pass.

`evidence/run_v1.log` is the initial v1 pipeline run (generate + validate +
tsc) from the first build of this demo.

## TypeScript consumability (criterion 5)

`offersnapshot.ts` is plain interfaces + union types with no imports and no
runtime code — it drops into the Next.js + shadcn human UI as-is, and
`make check-ts` compiles it under `tsc --strict --noEmit` with **zero hand
edits**. `extra="forbid"` on the Pydantic side propagates
`additionalProperties: false`, so the root interface is strict (no
index-signature loosening). One cosmetic caveat: json-schema-to-typescript
derives the top-level scalar alias *names* from Pydantic's field titles and
flattens their casing (`Tripcandidateid`, `Sourceref`, `Taxesincluded`);
the interface *property* names are the exact contract camelCase, and no
hand-editing is needed or permitted — noted so nobody "fixes" a generated
file by hand.

## Caveats / limits of this path (honest list)

- **Bridge coverage.** `bridge.py` maps the SQLAlchemy types this schema
  uses (String, Enum, DateTime, JSON + typed-JSON TypeDecorators, Boolean,
  Integer, Float). An unmapped type raises `TypeError` loudly rather than
  guessing — extending the bridge is a one-rule change per new type when
  Sprint 0 schema authoring hits one (e.g. ARRAY for StayPhase[], PG
  `UUID`/`JSONB` variants). This is the one piece of bespoke tooling in the
  path; it is ~100 lines, deterministic, and model-agnostic.
- **Generated-file churn.** datamodel-codegen stamps a timestamp header, so
  the generated `.py` differs byte-wise across runs; content is otherwise
  deterministic. (Visible in `evidence/propagation.diff`.)
- **TS datetime = string** — see Timestamps above.
- **`npx` tsc resolution.** `npx --package typescript tsc` does not resolve
  the `tsc` bin reliably from inside this repo tree ("could not determine
  executable to run" / "tsc: not found"); the TS *generation* step via npx
  works fine. `make check-ts` therefore uses the pinned TypeScript install
  (see requirements.txt) — deterministic either way.
- **Enum flavour.** datamodel-codegen emits `StrEnum` (Python ≥ 3.11) for
  string enums; values are preserved exactly. If a future consumer needs
  classic `(str, Enum)`, that is a generator flag decision, not an edit.
