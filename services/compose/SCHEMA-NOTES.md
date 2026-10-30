# Sprint 0 Schema — Author's Notes & Self-Grade

**Deliverable:** the UZEMARKETS composition-layer schema, authored once in
`src/models.py` (SQLAlchemy 2.0), migrated by Alembic into the database
**`uzemarkets-compose`**, projected to Pydantic + TypeScript by the reviewed
codegen chain, unchanged.

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

## Model inventory (23 models, 8 enums)

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
CANCELLED) · `DivergenceCode` (the 8 R4 codes).

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
committed `Makefile`, no added flags. Verified reproducibility: a scratch
copy re-ran `make all` and reproduced every committed artifact
**byte-for-byte except the generator's timestamp header line** (0
non-timestamp diff lines across all 92 artifacts). `make check-ts` passes
(`tsc --strict`). Destructive-by-default is stated on the Makefile and
holds: every generator overwrites wholesale; `make clean` deletes all
generated artifacts.

**11. Database name uzemarkets-compose in the connection config — PASS.**
`src/config.py`: `DATABASE_NAME = "uzemarkets-compose"`, `database_url()`
with a `COMPOSE_DATABASE_URL` override; `.env.example` carries the same
name; the Alembic env takes its URL from that config; the demo migrated a
database of exactly that name (D1).

---

## AUTHOR'S CHOICES — every under-specified point, for ratification or overturn

1. **QuestionManifest field shape.** The spec names the model and files
   no shape for it. Authored narrow: `key` (unique), `version`, `title`,
   `questions` (JSON list of {slot, prompt, type, required, module?}),
   `active`, `createdAt`. **This one most needs an explicit tap** — it
   will harden fastest once intake work starts.
2. **RailPayload members beyond the ticket core.** Only the ticket
   member's core is ratified content (seat, tier + mintRef/ticketRef/
   listingRef per R4 §6). The other six members carry minimal binding
   identifiers only: Stay {phaseKind, nights, propertyRef?}, Flight
   {itineraryRef, carrier?, departAt?}, Facility {facilityRef, packageRef,
   procedureClassBand?}, Parking {anchorRef, spotRef?}, Transfer
   {taskRef, pickupAt?}, Dining {taskRef, reservationAt?}. Every field
   here beyond the spec's words is a choice.
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
13. **Union member naming (RailPayload1…7) is NOT resolved here.** The
    chain was used unchanged — no `--use-title-as-name` — per the
    standing instruction. The schema review takes this decision
    explicitly (adopt the flag, adopt bridge-emitted named $defs, or
    accept numbered names), as filed at the fidelity check's close.
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
