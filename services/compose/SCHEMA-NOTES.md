# Sprint 0 Schema — Author's Notes & Self-Grade

**Deliverable:** the UZEMARKETS composition-layer schema, authored once in
`src/models.py` (SQLAlchemy 2.0), migrated by Alembic into the database
**`uzemarkets-compose`**, projected to Pydantic + TypeScript by the reviewed
codegen chain (plus the one naming flag adopted at James's tap (c) — see
Author's Choice 13, resolved).

**Sources of truth followed:** the Data-First spec
(`docs/UZEMARKETS-DATA-FIRST-BUILD-PLAN-IMPORTED-DRAFT-v0.1.md`, incl. the
ratified sections — ORM (C), inventory = consumer of services/api, DB name
`uzemarkets-compose`, seat placement in `OfferSnapshot.payload`), the
Read-Through Contract R4 DRAFT v0.2 (`docs/sprint-0/READ-THROUGH-CONTRACT-v0.1.md`),
and the codegen round-trip + fidelity artifacts
(`docs/sprint-0/codegen-roundtrip/`).

**Demonstration substrate — stated honestly:** every DB-level demonstration
ran on **real PostgreSQL 16.2** (the pgserver-bundled PostgreSQL binaries,
run as a local instance on this VM; database reset fresh by the demo script
and migrated by Alembic). Nothing in the evidence ran on SQLite. The demo
database is a throwaway local instance, not staging — the schema has not
been applied anywhere else.

---

## Model inventory (23 models, 10 enums)

Intake & trip: `IntakeDraft`, `TripProfile`, `Traveler`, `GeoAnchor`,
`MetroProfile`, `StayPhase`.
Offer layer: `SearchSession`, `TripCandidate`, `OfferSnapshot`,
`ApprovalRequest`, `Commitment`.
System: `EventLog`, `IdempotencyKey`, `QuestionManifest`.
Task rail: `ServiceTask` (joined-table inheritance) + `DiningTask`,
`TransferTask`, `ConciergeBrief`.
Dormant health (Sprint 0, unused): `FacilityProfile`, `PackageTemplate`,
`ProcedureClassBand` (public schema); `ConsentRecord`, `HealthAttribute`
(Postgres schema **`health_restricted`**).

Enums: `GeoAnchorType` (VENUE, FACILITY, ADDRESS, METRO) · `TravelerRole`
(PATIENT, COMPANION, PRIMARY, GUEST) · `StayPhaseKind` (PRE_EVENT, EVENT,
POST_EVENT, PRE_OP, INPATIENT, RECOVERY) · `ModuleType` (TICKETS, STAY,
FLIGHT, PARKING, TRANSIT, DINING, TRANSFER, VIP_CONCIERGE, FACILITY) ·
`CommitmentClass` (IRREVERSIBLE_ON_CHAIN, CANCELLABLE_UNTIL_WINDOW,
CHANGEABLE_WITH_FEE, APPOINTMENT, MEDICAL_PACKAGE) · `Rail` (SOLANA_NFT,
HOTEL_AGGREGATOR, FLIGHT_SEARCH, FACILITY, PARKING, TRANSFER, DINING_TASK) ·
`TaskState` (REQUESTED, QUOTED, DEPOSIT_PENDING, CONFIRMED, FAILED,
CANCELLED) · `DivergenceCode` (the 8 R4 codes) · `OfferKind` (ticket, stay,
flight, facility, parking, transfer — the OfferSnapshot payload
discriminator since revision A; James's tap (c)) · `QuestionSlotType`
(STRING, INT, DATE, BOOL, ENUM, OBJECT, ARRAY — the QuestionSlot
`type` vocabulary since revision B; James's tap (a)).

Column names carry the contract's camelCase (`buyerId`, `sourceRef`,
`divergenceCode`); Python attributes are snake_case.

---

## Self-grade against the eleven pre-committed criteria

**1. StayPhase[] array-typed; no trip-level checkIn/checkOut — PASS.**
StayPhase is a row set related to TripProfile (ordered by `seq`), and the
generated surface is array-typed: `stayPhases: list[StayPhase]` in
`src/generated/tripprofile_pydantic.py`, likewise `travelers` and the
`modules` Postgres ARRAY column. TripProfile's table has no checkIn /
checkOut columns — asserted in the demo (D8); each phase row carries its
own per-phase checkIn/checkOut, which is where they belong.
Evidence: `evidence/demo_run.log` D8.

**2. Traveler as rows with roles; no partySize on TripProfile — PASS.**
Travelers are rows with a `TravelerRole`; `partySize` does not exist on
TripProfile (asserted, D8). Evidence: demo D8.

**3. Dormant tables present and unused — PASS.**
FacilityProfile, PackageTemplate, ProcedureClassBand, and the restricted
namespace (ConsentRecord, HealthAttribute in `health_restricted`) are
created by the initial migration and are empty; nothing in the event
vertical references them (zero cross-schema FKs — D7/D9). Evidence: demo
D2, D9.

**4. Enums complete including dormant members — PASS.**
Full sets listed in the inventory above, including the dormant members:
CommitmentClass APPOINTMENT + MEDICAL_PACKAGE, Rail FACILITY,
StayPhaseKind PRE_OP / INPATIENT / RECOVERY. The generated Pydantic
carries the same sets (e.g. `DivergenceCode` has exactly 8 members — D6).

**5. OfferSnapshot immutability demonstrated by mechanism — PASS, with
one disclosed exception (see Author's Choice 3).**
Three mechanisms, all demonstrated: (a) a **Postgres trigger**
(`trg_offer_snapshot_immutable`, in the initial migration) refusing
UPDATE/DELETE from any writer; (b) an **ORM guard** (before_update /
before_delete) with the same rule; (c) **frozen Pydantic** on the
generated surface. The trigger permits exactly one post-insert write —
the divergence annotation (choice 3). Evidence: demo D3 (raw-SQL price
UPDATE refused, DELETE refused, annotation applies exactly once, second
annotation refused) and D6 (frozen mutation refused).

**Post-review fix (2026-10-30):** the schema review ratified the
exception on three terms (named in full under Author's Choice 3
below). Term 1 — the annotation is a derived projection of the
authoritative EventLog entry — is now a mechanism, not a convention:
additive revision `9d4c1f7a2b58` adds the mirror trigger
(`trg_offer_snapshot_divergence_mirror`), which inserts the
SNAPSHOT_DIVERGED EventLog row in the same transaction as the
annotation, for every writer, unbypassably. Demo D3 now also asserts
exactly one mirrored EventLog row with the matching code.

**6. EventLog append-only, enforced at DB level, demonstrated — PASS.**
Trigger `trg_event_log_append_only` raises on UPDATE and DELETE
unconditionally; an ORM guard mirrors it. Evidence: demo D4.

**7. IdempotencyKey enforcement at Postgres — PASS.**
The key IS the primary key: the first writer inserts the row with status
`IN_FLIGHT` (the in-flight marker); a second writer of the same key hits
the uniqueness constraint at the Postgres level. No surrogate id, no
application-level check. Redis appears nowhere in this service — it is a
hot cache only by the spec's architecture, and the schema neither needs
nor uses it. Evidence: demo D5 (duplicate insert → IntegrityError, the
IN_FLIGHT row stands).

**8. sourceRef typed as a reference, not a FK — PASS.**
`sourceRef` is a plain string column with no foreign key (mapper
inspection, D7); `offer_snapshot`'s only FK is the internal
`tripCandidateId`. Zero cross-schema FKs exist in the database, and no
cross-database join is expressible from this schema. GeoAnchor.refId
follows the same law. Evidence: demo D7.

**9. Divergence codes typed as an enum on OfferSnapshot — PASS.**
`divergenceCode` is a Postgres enum column (the 8 R4 codes) on
OfferSnapshot itself, projected to a StrEnum in the generated Pydantic
and present in the TypeScript artifact. Bogus codes are rejected at
validation (D6); the annotation write in D3 is typed by the column.

**10. Codegen round-trip regenerated cleanly, destructive-by-default,
both surfaces re-generated — PASS.**
All 23 models regenerate from `src/models.py` through the reviewed chain
(bridge → datamodel-code-generator → Pydantic → json-schema-to-typescript),
committed `Makefile`. Verified reproducibility: a scratch
copy re-ran `make all` and reproduced every committed artifact
**byte-for-byte except the generator's timestamp header line** (0
non-timestamp diff lines across all 92 artifacts). `make check-ts` passes
(`tsc --strict`). Destructive-by-default is stated on the Makefile and
holds: every generator overwrites wholesale; `make clean` deletes all
generated artifacts. **Close-out amendment (revision A, 2026-10-30):**
the invocation now carries ONE added flag, `--use-title-as-name`,
adopted when James's tap (c) resolved the member-naming decision
(Author's Choice 13); reproducibility was re-verified for the new
artifacts in the same change (two from-clean generations, 0
non-timestamp diff lines).

**11. Database name uzemarkets-compose in the connection config — PASS.**
`src/config.py`: `DATABASE_NAME = "uzemarkets-compose"`, `database_url()`
with a `COMPOSE_DATABASE_URL` override; `.env.example` carries the same
name; the Alembic env takes its URL from that config; the demo migrated a
database of exactly that name (D1).

---

## Close-out revisions (James's taps (a) and (c), 2026-10-30)

**Revision A — OfferKind (tap (c)) — Alembic `b3d91c7e5a02`.**
OfferKind (ticket | stay | flight | facility | parking | transfer) is
now the OfferSnapshot payload discriminator; the payload tag property
is renamed `rail` → `kind`; union members are named
TicketOfferDetail … TransferOfferDetail in BOTH generated surfaces;
the Dining member is deleted (a task rail produces no offer); Rail is
retained for routing and dispatch; the ONE mapping is
`offer_kind_for_rail()` in `src/models.py` (DINING_TASK → None).
DB-level presence: CHECK `ck_offer_snapshot_payload_kind` on
offer_snapshot (downgrade verified symmetric). Member-naming route:
the chain's `--use-title-as-name` flag — Author's Choice 13 is
RESOLVED (below). One mechanical consequence, disclosed: the class
rename would have broken from-empty replay, because the initial
migration instantiates `models.RailPayloadJSON()` for the payload
column's DDL; `models.py` therefore carries a one-line historical
alias (`RailPayloadJSON = OfferPayloadJSON`, commented; new code uses
OfferPayloadJSON only) rather than editing a filed migration.
**That alias is itself now RESOLVED — removed 2026-10-30 by the
frozen-artifact inline (final section of these notes): the migration
inlines the two types it needs, so the alias had nothing left to
serve, and schema-dump equality proved the inline changed nothing.**
Evidence: demo **11/11 from empty** at the new head — D11 proves the
split on the generated surfaces, the mapping, and the CHECK; D1–D10
pass unchanged in substance.

**Revision B — QuestionManifest slot shape (tap (a)) — Alembic
`d52f8b1a904c`.** `QuestionManifest.questions` is now a typed list of
QuestionSlot, exactly as tapped: key, type (QuestionSlotType),
enumValues (string[], iff type = ENUM), required, deferrable,
dependsOn ({slot, op, value} entries), moduleGate (ModuleType),
validation, promptHuman, promptAgent — camelCase keys, vocabularies
built from the enums in the authoring source. The one conditional
rule (enumValues iff ENUM) is enforced WITHOUT any hand-written
validator in generated code: the slot is a two-member union split on
that condition (EnumQuestionSlot requires enumValues;
StandardQuestionSlot, closed, forbids it). DB-level presence:
validation trigger `trg_question_manifest_validate_slots` enforcing
the same shape for raw-SQL writers (downgrade verified symmetric).
The traceability discipline is recorded on the model: every slot
gates a module or is deleted — a data-authoring rule whose schema
anchor is moduleGate (optional in the schema, as tapped). Author's
Choice 1 is RESOLVED (below). Evidence: demo **12/12 from empty** at
the final head (D12 proves dispatch, all four rejection cases, and
the trigger's refusals); regeneration reproducibility re-verified
(two from-clean generations, 0 non-timestamp diff lines);
`make check-ts` clean.

---

## AUTHOR'S CHOICES — every under-specified point, for ratification or overturn

1. **QuestionManifest field shape — RESOLVED by James's tap (a),
   2026-10-30.** The spec named the model and filed no shape for it;
   as authored in Sprint 0 it was narrow and flagged as most needing
   a tap. The tap supplied the shape, and revision B (`d52f8b1a904c`)
   replaced the placeholder: `questions` is a typed list of
   QuestionSlot {key, type (QuestionSlotType), enumValues (string[],
   iff type = ENUM), required, deferrable, dependsOn, moduleGate
   (ModuleType), validation, promptHuman, promptAgent}; the manifest
   row itself keeps `key` (unique), `version`, `title`, `active`,
   `createdAt`. One implementation choice inside the tap, labeled:
   the enumValues-iff rule is enforced structurally (a two-member
   slot union) rather than by a validator, because generated files
   are never hand-edited — see the QuestionSlotListJSON docstring and
   the close-out section above.
2. **Payload members beyond the ticket core.** Only the ticket
   member's core is ratified content (seat, tier + mintRef/ticketRef/
   listingRef per R4 §6). The other members carry minimal binding
   identifiers only: Stay {phaseKind, nights, propertyRef?}, Flight
   {itineraryRef, carrier?, departAt?}, Facility {facilityRef, packageRef,
   procedureClassBand?}, Parking {anchorRef, spotRef?}, Transfer
   {taskRef, pickupAt?}. Every field here beyond the spec's words is a
   choice. (As originally authored these were the RailPayload members;
   at revision A they were re-homed unchanged under their OfferKind
   member names, and the seventh member — Dining {taskRef,
   reservationAt?} — was DELETED under James's tap (c): a task rail
   is not an offer.)
3. **The divergence annotation is a permitted UPDATE on an immutable
   table.** Criteria 5 + 9 and R4 §5 together require the kill to be
   recorded ON the snapshot (typed code + timestamp), so the trigger and
   the ORM guard permit exactly that one transition: divergenceCode from
   NULL to a code, divergenceAt alongside, every other column
   byte-identical, exactly once. Any other reading (a separate annotation
   table; snapshots re-issued) is the review's to substitute.

   **Ratified by the schema review on three terms** (also named in the
   OfferSnapshot docstring in `src/models.py` — term 3):
   (1) **Derived, not independent** — the EventLog entry is the
   authoritative record of the divergence; the divergenceCode /
   divergenceAt columns are its derived projection, materialized
   atomically in the same transaction by the mirror trigger
   (`trg_offer_snapshot_divergence_mirror`, Alembic revision
   `9d4c1f7a2b58`). There is no annotation write that is not
   simultaneously an EventLog write, and no writer can bypass the
   mirror. (2) **No widening** — the exception is one column-pair, one
   transition (NULL → code), exactly once; any future exception
   request goes to a new review, never to a widening of these
   triggers. (3) **Named in the record** — this text and the model
   docstring name the exception and these terms, so the triggers'
   reason is never archaeology.
4. **Status vocabularies kept as strings where the spec's enum block
   declares no enum:** ApprovalRequest.status (PENDING | APPROVED |
   REJECTED | EXPIRED), TripCandidate.status (OPEN | PARTIAL | FAILED),
   Commitment.state, ServiceTask.kind discriminator values
   (SERVICE / DINING / TRANSFER), ConciergeBrief.trigger (the
   consolidation's vocabulary, verbatim in the model docstring). Where
   the spec DID declare an enum (TaskState), the column is the enum.
5. **Internal foreign keys are real FKs** (Traveler/StayPhase →
   TripProfile, TripCandidate → SearchSession, SearchSession →
   TripProfile, OfferSnapshot → TripCandidate, Commitment →
   ApprovalRequest + OfferSnapshot, HealthAttribute → ConsentRecord
   inside the namespace). The boundary law (R4) governs references OUT of
   this database; inside it, referential integrity is enforced, not
   simulated. SearchSession → TripProfile as a real FK is the
   composition-internal reading of the consolidation's flow.
6. **Traveler carries no name/identity columns** — role, origin,
   nationality, utilityWeights only (spec §3.2: a traveler is an object
   with a role and utility weights). If the review wants a display name,
   it is one additive column later.
7. **ConsentRecord.subjectId is an opaque string, deliberately NOT a
   foreign key** — the restricted namespace must not be joinable from the
   traveler side; the reference runs one way only, by value.
8. **IdempotencyKey shape:** `key` is the PK itself; plus `scope`,
   `requestHash`, `responseJson`, `status`, `createdAt`. In-flight
   handling = first-writer IN_FLIGHT row (criterion 7's wording).
9. **StayPhase.propertyRef is a plain string reference** (boundary law),
   as is GeoAnchor.refId; GeoAnchor itself is a table with a polymorphic
   `type`, per spec §3.3.
10. **Enum member sets** for ModuleType, TravelerRole, GeoAnchorType are
    the author's reading of the spec §4.1 + consolidation text — the spec
    names these enums; where its member lists are prose, the sets above
    are what was authored. Overturn by naming the set.
11. **OfferSnapshot.terms is plain JSON** — price is the typed structure
    (PriceJSON); terms are rail-dependent and the spec prototypes no
    terms shape, so no fragment was invented for them.
12. **ConciergeBrief metering** is three nullable integer-cent fields
    (rate, cap, expiry) from the consolidation's "pre-authorized
    metering — rate, cap, expiry"; nullable because a brief can exist
    before metering terms are set.
13. **Union member naming — RESOLVED by James's tap (c), 2026-10-30.**
    As filed at the fidelity check's close, this was left to the
    schema review; the review's OfferKind finding decided it: member
    names match OfferKind. Route adopted: the chain gains ONE flag,
    `--use-title-as-name` (Makefile), so the generated members carry
    their titled names (TicketOfferDetail … TransferOfferDetail) in
    Pydantic and TypeScript; the positional names (RailPayload1…7)
    are gone (demo D11 asserts their absence). The rest of the chain's
    invocation is unchanged from the reviewed round-trip.
14. **Migration downgrade leaves Postgres enum types behind** (Postgres
    does not drop enum types with their tables). Documented in the
    revision itself; a base downgrade is a development action, and
    production teardown drops the database. Noted here so it is a known
    property, not a surprise.

## Known tracked items carried from R4 (unchanged by this deliverable)

- The 501 race (two compose transactions could both pass reconciliation
  and both mint while services/api buy is 501) — protections decision
  (compose-layer lock keyed on Ticket ID vs accept risk) is Sprint 1
  horizon, per R4's filing.
- The single-ticket read (`GET /tickets/{ticket_id}`) is a cross-repo
  dependency on services/api needing an owner + target sprint before
  Sprint 1's commit path; the initial migration + contract assume it
  lands as a proposed additive read. Schema authoring does not depend on
  the runtime endpoint.

## Notes on the working

- One early downgrade attempt against the pre-reset dev database errored
  once (SQLAlchemy f405) and was not reproduced: from a clean reset,
  upgrade → downgrade → upgrade cycles pass, and the committed demo
  follows the clean path (it resets its database itself).
- TypeScript renders datetimes as `string` (format retained in the JSON
  Schemas) — the standing caveat from the round-trip review; the branded
  datetime type stays tracked against Sprint 1's approval-gate UI.

## RLS on health_restricted — DEFERRED, not dropped (recorded 2026-10-30, schema review)

The spec describes the restricted namespace as "RLS-gated." As built in Sprint 0, `health_restricted` is enforced by **schema-namespace isolation only** — separate Postgres schema, no foreign keys into or out of it, consent-gated at the model layer — with **no row-level security policies and no role/grant constructs anywhere in the migration chain** (verified by grep across all revisions). That is the correct Sprint 0 posture: the tables are dormant, hold no data, and have no runtime touch until the health vertical activates. **RLS is deferred to the health sprint (sprints 10–12), not dropped and not decided-against.** When the health vertical is built, RLS policies + the role model for the restricted namespace are designed and migrated then, as part of that sprint's own review. No reader of this schema should inherit "namespace-only" as the settled design: the settled design is namespace isolation now, RLS at health activation.

## Standing standard — from-empty replay (adopted 2026-10-30, schema review)

Every future revision gets a **from-empty replay at its head before filing**: the demo harness drops and recreates the database and applies the full chain in a single `alembic upgrade head` pass, and the revision is not filed until that replay passes. This discipline caught the RailPayloadJSON rename break during the Sprint 0 close-out; it is the standard, not a one-off.

## Frozen-artifact inline — the alias fragility RESOLVED (2026-10-30, Sprint 1 first-week follow-on)

The schema review named the deeper coupling in the close-out's
historical alias: as filed, the initial migration
(`cd548e517e5e`) did `import models` and instantiated
`models.PriceJSON()` / `models.RailPayloadJSON()`. The migration ran
standalone, but its behavior was a function of live application
source — any future refactor of `models.py` (rename, split, package
move) would break the filed chain at replay time. That inverts the
Alembic principle: **migrations are frozen artifacts — point-in-time
schema state, independent of current models.** At James's direction
(on the review's recommendation), the coupling is removed, not
worked around:

- **Inlined.** The initial migration now defines the two types
  locally (`PriceJSON`, `OfferPayloadJSON` — TypeDecorators with
  `impl = sa.JSON`, `cache_ok = True`, exactly their DDL-relevant
  content; the `json_schema` fragments are a codegen-bridge concern,
  not DDL, and are not copied). The `import models` is gone from the
  migration; no version file references application source.
- **env.py guarded.** The application-source import in
  `alembic/env.py` (autogenerate's `target_metadata` + the
  config-managed URL) is wrapped so an upgrade run proceeds without
  it — `target_metadata = None`, URL from `COMPOSE_DATABASE_URL` /
  the .ini — while autogenerate from the repo still gets the
  authoring source's metadata.
- **Alias removed.** `RailPayloadJSON = OfferPayloadJSON` and its
  comment block are deleted from `src/models.py`; zero code
  references to the old name remain anywhere.

**Proofs (all against the unchanged head `d52f8b1a904c` — this is a
source fix to a filed migration, not a schema change, so no new
revision):** (1) from-empty demo **12/12 PASS** post-fix; (2)
`pg_dump --schema-only` of the post-fix from-empty build is
**byte-identical** to the pre-fix baseline dump — the inline produces
exactly the filed schema; (3) **standalone run**: the `alembic/`
tree + `alembic.ini` copied alone (no `src/` present or importable,
PYTHONPATH unset, URL via `COMPOSE_DATABASE_URL`) applied the full
chain cleanly to a fresh database — head `d52f8b1a904c`, all three
enforcement triggers present, and its schema dump likewise
byte-identical to the baseline; (4) regeneration (`make all`) after
the alias removal: **0 non-timestamp diff lines**, so the committed
generated artifacts stand unchanged. The "commented alias" pattern
is closed: if a future replay ever seems to need one, that is the
signal to inline, not to alias.

## Sprint 1 Slice 2 — R4 read-through integration (filed 2026-11-01)

**What was built** (no schema changes; Alembic head unchanged at
`d52f8b1a904c`; `models.py` untouched by this slice):

- `src/upstream.py` — the reconciliation reader. ONE interface
  (`ReconciliationReader`) exposing exactly two reads — the
  referenced Ticket by id and its fulfilling Listing by id — and
  nothing else. Three implementations: `HttpReconciliationReader`
  (the direct reads: `GET /tickets/{id}` narrowed shape +
  `GET /listings/{id}`, envelope unwrapped; 404 ->
  `UpstreamNotFound`, transport/timeout/5xx ->
  `UpstreamUnavailable`, never collapsed into one another);
  `ListingReadProxy` (the interim read the firing map names —
  an in-process stand-in over a supplied dataset shaped like
  services/api rows, with per-id transport-failure simulation and
  an attempted-read log); `UnavailableReader` (selected when
  `COMPOSE_UPSTREAM_BASE_URL` is unset: every read is honestly
  unobservable). The factory (`build_reader`) is the ONE place the
  choice is made; the proxy is never selected implicitly.
- `src/readthrough.py` — the §6 reconciliation evaluator +
  recording service (see the firing map as implemented, below).
- `src/snapshots.py` — `POST /snapshots/{snapshot_id}/reconcile`:
  200 CLEAN / 409 DIVERGED / 503 BLOCKED (UPSTREAM_UNAVAILABLE) /
  404 unknown snapshot / 422 non-ticket kind. One field set for
  every surface (R4 §2.3 parity): snapshotId, outcome, code,
  reason, killsSnapshot, observed, evaluatedAt.

**The firing map as implemented** (evaluation order is part of the
implementation, and is the contract's): (1) already-annotated
snapshot -> its recorded outcome, no new reads or records;
(2) TTL — `now >= expiresAt` -> SNAPSHOT_EXPIRED, refused BEFORE
any upstream read (the TTL test asserts the proxy recorded zero
read attempts, with the proxy configured to fail every read:
dominance over UPSTREAM_UNAVAILABLE, per R4 §5); (3) re-reads —
404 on either reference -> SOURCE_NOT_FOUND; transport failure ->
UPSTREAM_UNAVAILABLE (recorded, never annotated, retryable);
(4) ticket `transferred` -> TICKET_TRANSFERRED (the status branch;
the narrowed read returns no ownerId by design and the firing
map's note 1 + the owner-guard trigger retire the owner branch);
ticket `redeemed` -> TICKET_REDEEMED (no-writer stub branch —
fires on observed state; revisit trigger: a redeem endpoint lands
in services/api); (5) the seat's mintRef already carrying a
settlement (a Commitment with a recorded chainTxRef) under a
DIFFERENT snapshot -> SEAT_TAKEN / DOUBLE_SETTLEMENT;
(6) listing `sold` -> LISTING_GONE; listing `cancelled`/`flagged`
with the ticket still `listed` -> SEAT_TAKEN / MODERATION (seat
trigger (i): moderation removed the fulfillment path without
resetting the ticket); listing `cancelled`/`flagged` with the
ticket NOT `listed` -> LISTING_GONE; listing active with
priceCents/feeCents differing from the frozen price/terms ->
PRICE_MOVED (no-writer stub branch; revisit triggers per Post-Map
item 3: a price-update endpoint or moderation price-change path
in services/api, or supplier-side price reads entering this
layer); (7) otherwise CLEAN.

**Recording.** Every raised code writes an EventLog record from
this service (eventType `DIVERGENCE_DETECTED`, actor
`system:read-through`, payload: divergenceCode, reason, surface,
ticketRef, listingRef, sourceRef, observed current state) — the
R4 §5(d) record. Killing codes then apply the divergence
annotation in the same transaction; the mirror trigger writes the
authoritative SNAPSHOT_DIVERGED row alongside it. The two records
are distinct and both are named here so neither is mistaken for
the other: the mirror's payload (fixed by the frozen migration)
carries code/at/sourceRef/rail; the reason and the observed state
live on this service's record — which is where filing item 3
(SEAT_TAKEN reason populated on the EventLog divergence row) is
discharged, the frozen trigger being unchangeable under this
slice's no-schema-change constraint.

**The moderated-listing fixture** (filing item 4) is implemented
as an end-to-end test against the proxy
(`test_moderated_listing_flagged_is_seat_taken_moderation`, plus
its cancelled variant): ticket `listed`, listing `flagged` ->
409 SEAT_TAKEN, reason MODERATION in the result AND on the
EventLog record, snapshot annotated, exactly one mirror row. It
runs without a live services/api because the proxy is the interim
read by design; it does NOT discharge the post-redeploy live gate
(the same fixture against the redeployed services/api remains the
gate for "Sprint 1's commit path works end-to-end", per the
redeploy filing).

**Evidence (this filing's runs, real PostgreSQL 16.2 substrate):**
`make test` — **44 passed** (29 pre-existing, unregressed; 15 new
in tests/test_readthrough.py covering every branch above, the
already-killed short-circuit, and the surface discipline cases).
`make validate` — **12/12 from empty**, head `d52f8b1a904c`.
`make check-ts` — clean. Zero DDL change: the slice adds no
migration and touches no generated artifact (regeneration diff
from the verification runs was timestamp-only and was reverted).

**Author's choices in this slice** (for review; overturn by naming
the alternative): (a) the response status mapping 200/409/503 —
divergence is a typed refusal, transport blockage is retryable,
and neither is a server fault; (b) reference resolution — payload
ticketRef/listingRef first, sourceRef as fallback (R4 §3 names
sourceRef as a Ticket id OR a Listing id per rail; the payload is
the ratified seat record); (c) the already-annotated short-circuit
returns the recorded outcome (including its reason, recovered from
the service's EventLog record) rather than re-evaluating a dead
snapshot; (d) the frozen fee comparison reads `terms.feeCents`
(terms is the free-form JSON the quote flow records fees in);
(e) deliberately NOT evaluated: tier mismatch and a listing whose
ticketId names a different ticket — R4 §5 and the firing map name
no code for either, and inventing codes is out of bounds.

**Stated limits.** `HttpReconciliationReader` has NOT been run
against a live services/api (the ticket read is not deployed; the
Prisma engine blockage in this sandbox is separately on record).
Its behavior is code-reviewed against the routers' source, and its
error mapping mirrors the proxy's, which the suite exercises. The
approval gate and commitment recording remain later Sprint 1
slices; this slice's evaluator is the shared core both will call.
