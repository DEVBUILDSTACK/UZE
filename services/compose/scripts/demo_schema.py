#!/usr/bin/env python
"""Sprint 0 schema demonstration — services/compose.

WHAT THIS PROVES (against a REAL PostgreSQL — see the substrate banner;
nothing here is claimed for a substrate it did not run on):
  D1  the Alembic initial revision applies cleanly to a fresh database
      named uzemarkets-compose
  D2  all 23 tables exist (21 public + 2 in health_restricted)
  D3  OfferSnapshot immutability fires at DB level (raw SQL): price
      UPDATE refused, DELETE refused, ordinary UPDATE refused, the ONE
      permitted write — the divergence annotation — succeeds exactly
      once, a second annotation is refused; the ORM guard fires too.
      The annotation's EventLog mirror is asserted: exactly one
      SNAPSHOT_DIVERGED row (actor system:divergence-annotation,
      matching code), written atomically by the mirror trigger
  D4  EventLog is append-only at DB level: UPDATE and DELETE refused
      (raw SQL), and the ORM guard refuses a delete
  D5  IdempotencyKey uniqueness is enforced by Postgres: a duplicate
      key insert raises IntegrityError (the IN_FLIGHT row stands)
  D6  the generated Pydantic validates one full OfferSnapshot with a
      per-rail payload; mislabeled payloads and bogus divergence codes
      are rejected; the divergence enum is typed end-to-end (Pydantic +
      TypeScript artifact)
  D7  sourceRef is a plain reference: no FK on the column (mapper
      inspection) and no cross-namespace FK in the database
  D8  TripProfile carries travelers as rows and stay phases as an
      array-structured relation — no checkIn/checkOut, no partySize
  D9  the dormant health set exists, is empty, and is namespace-isolated
  D10 NEGATIVE atomicity of the divergence mirror: with a temporary
      BEFORE INSERT blocker on event_log forcing the mirror's insert
      to fail, the annotation on a fresh snapshot errors out and
      rolls back WITH it (divergenceCode still NULL, zero mirror
      rows) — co-occurrence is not enough; the pair is one
      transaction. The blocker is then dropped and the positive path
      on the same snapshot succeeds with exactly one mirror row

The script RESETS the target database (drop + create) before migrating:
the target must be a throwaway database named exactly
"uzemarkets-compose" (guard below). Run via `make validate`; output is
tee'd to evidence/demo_run.log.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
COMPOSE_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(COMPOSE_DIR, "src"))
sys.path.insert(0, os.path.join(COMPOSE_DIR, "src", "generated"))

# The demo database on this VM: pgserver-bundled PostgreSQL binaries run
# as a local instance (see SCHEMA-NOTES "Demonstration substrate").
# Override with COMPOSE_DATABASE_URL to point at any other Postgres.
DEMO_URL = os.environ.get(
    "COMPOSE_DATABASE_URL",
    "postgresql+psycopg://postgres@127.0.0.1:55433/uzemarkets-compose",
)

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> None:
    try:
        evidence = fn()
        RESULTS.append((name, True, evidence or ""))
        print(f"PASS {name} — {evidence}")
    except Exception as exc:  # noqa: BLE001 — a demo reports, never hides
        RESULTS.append((name, False, f"{type(exc).__name__}: {exc}"))
        print(f"FAIL {name} — {type(exc).__name__}: {exc}")


def expect_refused(conn, sql: str, params: dict, needle: str) -> str:
    """Run a write that MUST be refused; return the refusal message."""
    from sqlalchemy import text

    try:
        conn.execute(text(sql), params)
        conn.commit()
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        assert needle in str(exc), f"refused, but not by the expected mechanism: {exc}"
        return str(exc).splitlines()[0][:110]
    raise AssertionError("write was ACCEPTED but must be refused")


def main() -> int:
    import sqlalchemy
    from sqlalchemy import text

    assert DEMO_URL.rsplit("/", 1)[-1].split("?")[0] == "uzemarkets-compose", (
        "guard: the demo resets its target database; it must be named "
        "uzemarkets-compose"
    )

    # ---------- bootstrap: fresh database + real migration ----------
    admin_url = DEMO_URL.rsplit("/", 1)[0] + "/postgres"
    admin = sqlalchemy.create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        version = c.execute(text("SHOW server_version")).scalar()
        c.exec_driver_sql('DROP DATABASE IF EXISTS "uzemarkets-compose"')
        c.exec_driver_sql('CREATE DATABASE "uzemarkets-compose"')
    print("=" * 72)
    print("UZEMARKETS composition layer — Sprint 0 schema demonstration")
    print(f"Substrate: REAL PostgreSQL (server_version {version}) — local")
    print("instance from the pgserver-bundled PostgreSQL 16.2 binaries,")
    print("database reset fresh by this script, migrated by Alembic.")
    print("This is a PostgreSQL demonstration, not a SQLite one.")
    print("=" * 72)

    env = dict(os.environ, COMPOSE_DATABASE_URL=DEMO_URL)
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=COMPOSE_DIR, env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"alembic upgrade failed: {proc.stderr[-400:]}"

    import models
    from sqlalchemy.orm import sessionmaker

    engine = sqlalchemy.create_engine(DEMO_URL)
    Session = sessionmaker(bind=engine)
    now = datetime.now(timezone.utc)

    def d1() -> str:
        with engine.connect() as c:
            rev = c.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert rev, "no alembic revision recorded"
        return f"alembic at head revision {rev} on database uzemarkets-compose"

    def d2() -> str:
        expected_public = {
            "intake_draft", "trip_profile", "traveler", "geo_anchor",
            "metro_profile", "stay_phase", "search_session",
            "trip_candidate", "offer_snapshot", "approval_request",
            "commitment", "event_log", "idempotency_key",
            "question_manifest", "service_task", "dining_task",
            "transfer_task", "concierge_brief", "facility_profile",
            "package_template", "procedure_class_band",
        }
        with engine.connect() as c:
            pub = {r[0] for r in c.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public'"))}
            res = {r[0] for r in c.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='health_restricted'"))}
        missing = expected_public - pub
        assert not missing, f"missing public tables: {missing}"
        assert res == {"consent_record", "health_attribute"}, f"restricted: {res}"
        return (f"{len(pub)} public tables (incl. alembic_version), "
                f"2 health_restricted tables — full 23-model inventory present")

    # Shared fixture: a candidate + one full snapshot.
    ids: dict[str, str] = {}

    def make_snapshot() -> None:
        with Session() as s:
            trip = models.TripProfile(
                buyer_id="buyer-1", tier="standard",
                authorization={"method": "card_hold", "status": "AUTHORIZED"},
                modules=[models.ModuleType.TICKETS])
            s.add(trip)
            s.flush()
            sess = models.SearchSession(trip_profile_id=trip.id,
                                        query={"q": "miami event weekend"})
            s.add(sess)
            s.flush()
            cand = models.TripCandidate(
                search_session_id=sess.id, status="OPEN",
                constraints={"legs": ["ticket"]})
            s.add(cand)
            s.flush()
            snap = models.OfferSnapshot(
                trip_candidate_id=cand.id,
                rail=models.Rail.SOLANA_NFT,
                source_ref="ticket:T-1001/listing:L-77",
                commitment_class=models.CommitmentClass.IRREVERSIBLE_ON_CHAIN,
                price={"amount": 120.50, "currency": "USD", "taxesIncluded": True},
                terms={"cancellation": "none"},
                payload={"rail": "ticket", "seat": "GA-114", "tier": "general",
                         "gate": "Gate B", "mintRef": "MINT-XYZ",
                         "ticketRef": "T-1001", "listingRef": "L-77"},
                expires_at=now + timedelta(hours=1),
                retention_until=now + timedelta(days=30),
            )
            s.add(snap)
            s.commit()
            ids["snapshot"] = snap.id
            ids["candidate"] = cand.id

    def d3() -> str:
        make_snapshot()
        sid = ids["snapshot"]
        with engine.connect() as c:
            msg1 = expect_refused(
                c, 'UPDATE offer_snapshot SET price = :p WHERE id = :i',
                {"p": '{"amount": 1, "currency": "USD", "taxesIncluded": true}',
                 "i": sid}, "immutable")
            expect_refused(
                c, 'UPDATE offer_snapshot SET "sourceRef" = :v WHERE id = :i',
                {"v": "ticket:OTHER", "i": sid}, "immutable")
            expect_refused(
                c, 'UPDATE offer_snapshot SET "divergenceCode" = :dc, '
                   'price = :p WHERE id = :i',
                {"dc": "SEAT_TAKEN",
                 "p": '{"amount": 1, "currency": "USD", "taxesIncluded": true}',
                 "i": sid}, "immutable")
            expect_refused(
                c, "DELETE FROM offer_snapshot WHERE id = :i",
                {"i": sid}, "immutable")
            # The ONE permitted write: the divergence annotation itself.
            c.execute(text(
                'UPDATE offer_snapshot SET "divergenceCode" = :dc, '
                '"divergenceAt" = :t WHERE id = :i'),
                {"dc": "SEAT_TAKEN", "t": now, "i": sid})
            c.commit()
            got = c.execute(text(
                'SELECT "divergenceCode" FROM offer_snapshot WHERE id = :i'),
                {"i": sid}).scalar()
            assert got == "SEAT_TAKEN", f"annotation not recorded: {got}"
            # TERM 1 (schema review): the annotation is a DERIVED
            # projection of an EventLog entry. The mirror trigger must
            # have written exactly one SNAPSHOT_DIVERGED row in the
            # same transaction as the annotation above.
            def mirror_rows():
                return c.execute(text(
                    'SELECT actor, payload FROM event_log '
                    'WHERE "aggregateType" = :at AND "aggregateId" = :ai '
                    'AND "eventType" = :et ORDER BY id'),
                    {"at": "OfferSnapshot", "ai": sid,
                     "et": "SNAPSHOT_DIVERGED"}).fetchall()
            rows = mirror_rows()
            assert len(rows) == 1, f"mirror EventLog rows: {len(rows)}"
            assert rows[0][0] == "system:divergence-annotation", rows[0][0]
            payload = rows[0][1]
            if isinstance(payload, str):
                import json
                payload = json.loads(payload)
            assert payload["divergenceCode"] == "SEAT_TAKEN", payload
            expect_refused(
                c, 'UPDATE offer_snapshot SET "divergenceCode" = :dc WHERE id = :i',
                {"dc": "PRICE_MOVED", "i": sid}, "immutable")
            # The refused second annotation must not have mirrored.
            assert len(mirror_rows()) == 1, "refused annotation mirrored"
        # ORM guard: mutate a mapped attribute and flush.
        with Session() as s:
            snap = s.get(models.OfferSnapshot, ids["snapshot"])
            snap.source_ref = "ticket:HACKED"
            try:
                s.flush()
                raise AssertionError("ORM guard did not fire on attribute mutation")
            except Exception as exc:
                s.rollback()
                assert "immutable" in str(exc), f"ORM guard message: {exc}"
        return ("DB trigger refuses price/sourceRef/combined UPDATEs and "
                f"DELETE ({msg1}); divergence annotation applies exactly "
                "once and the mirror trigger wrote exactly one "
                "SNAPSHOT_DIVERGED EventLog row (actor "
                "system:divergence-annotation, matching code); ORM guard "
                "fires on attribute mutation")

    def d4() -> str:
        with Session() as s:
            row = models.EventLog(aggregate_type="OfferSnapshot",
                                  aggregate_id=ids.get("snapshot", "x"),
                                  event_type="SNAPSHOT_DIVERGED",
                                  actor="compose-service",
                                  payload={"code": "SEAT_TAKEN"})
            s.add(row)
            s.commit()
            log_id = row.id
        with engine.connect() as c:
            expect_refused(
                c, "UPDATE event_log SET actor = 'x' WHERE id = :i",
                {"i": log_id}, "append-only")
            expect_refused(
                c, "DELETE FROM event_log WHERE id = :i",
                {"i": log_id}, "append-only")
        with Session() as s:
            row = s.get(models.EventLog, log_id)
            s.delete(row)
            try:
                s.flush()
                raise AssertionError("ORM guard did not fire on EventLog delete")
            except Exception as exc:
                s.rollback()
                assert "append-only" in str(exc), f"ORM guard message: {exc}"
        return "UPDATE/DELETE refused by DB trigger; ORM delete refused by guard"

    def d5() -> str:
        from sqlalchemy.exc import IntegrityError

        with Session() as s:
            s.add(models.IdempotencyKey(key="commit:req-1001", scope="commit",
                                        request_hash="abc123",
                                        status="IN_FLIGHT"))
            s.commit()
        try:
            with Session() as s:
                s.add(models.IdempotencyKey(key="commit:req-1001", scope="commit",
                                            request_hash="different",
                                            status="IN_FLIGHT"))
                s.commit()
            raise AssertionError("duplicate key was ACCEPTED")
        except IntegrityError:
            pass
        with engine.connect() as c:
            n = c.execute(text(
                "SELECT count(*) FROM idempotency_key WHERE key = :k"),
                {"k": "commit:req-1001"}).scalar()
        assert n == 1, f"expected exactly 1 row, found {n}"
        return "duplicate insert raised IntegrityError; the IN_FLIGHT row stands alone"

    def d6() -> str:
        from pydantic import ValidationError

        from offersnapshot_pydantic import DivergenceCode, OfferSnapshot

        base = dict(
            tripCandidateId="tc-1", rail="SOLANA_NFT",
            sourceRef="ticket:T-1001/listing:L-77",
            commitmentClass="IRREVERSIBLE_ON_CHAIN",
            price={"amount": 120.5, "currency": "USD", "taxesIncluded": True},
            terms={"cancellation": "none"},
            expiresAt="2027-04-01T00:00:00Z")
        ok = OfferSnapshot(**base, payload={
            "rail": "ticket", "seat": "GA-114", "tier": "general",
            "mintRef": "MINT-XYZ", "ticketRef": "T-1001",
            "listingRef": "L-77"})
        assert type(ok.payload.root).__name__ == "RailPayload1"
        stay = OfferSnapshot(**{**base, "rail": "HOTEL_AGGREGATOR"},
                             payload={"rail": "stay", "phaseKind": "EVENT",
                                      "nights": 2, "propertyRef": "H-9"})
        assert type(stay.payload.root).__name__ == "RailPayload2"
        for bad, why in [
            ({"rail": "ticket", "phaseKind": "EVENT", "nights": 2},
             "stay shape tagged ticket"),
            ({"rail": "stay", "seat": "A1", "tier": "ga"},
             "ticket shape tagged stay"),
        ]:
            try:
                OfferSnapshot(**base, payload=bad)
                raise AssertionError(f"mislabeled payload accepted: {why}")
            except ValidationError:
                pass
        try:
            OfferSnapshot(**base, divergenceCode="NOT_A_CODE", payload={
                "rail": "ticket", "seat": "A", "tier": "g"})
            raise AssertionError("bogus divergence code accepted")
        except ValidationError:
            pass
        typed = OfferSnapshot(**base, divergenceCode="SEAT_TAKEN", payload={
            "rail": "ticket", "seat": "A", "tier": "g"})
        assert typed.divergenceCode is DivergenceCode.SEAT_TAKEN
        assert len(DivergenceCode) == 8
        try:
            ok.price.amount = 1.0
            raise AssertionError("frozen Pydantic model allowed mutation")
        except ValidationError:
            pass
        ts = open(os.path.join(COMPOSE_DIR, "src", "generated",
                               "offersnapshot.ts")).read()
        for code in ("SNAPSHOT_EXPIRED", "UPSTREAM_UNAVAILABLE", "SEAT_TAKEN"):
            assert code in ts, f"{code} missing from the TypeScript artifact"
        return ("ticket + stay payloads validate via the discriminator; "
                "mislabeled pair rejected; divergence enum typed in "
                "Pydantic (8 codes) and present in the TS artifact; "
                "frozen mutation refused")

    def d7() -> str:
        col = models.OfferSnapshot.__table__.c.sourceRef
        assert not col.foreign_keys, "sourceRef carries an FK — criterion 8 violated"
        with engine.connect() as c:
            cross = c.execute(text(
                "SELECT count(*) FROM information_schema.table_constraints tc "
                "JOIN information_schema.referential_constraints rc "
                "  ON tc.constraint_name = rc.constraint_name "
                "JOIN information_schema.constraint_table_usage ctu "
                "  ON rc.unique_constraint_name = ctu.constraint_name "
                "WHERE tc.constraint_type = 'FOREIGN KEY' "
                "  AND tc.table_schema <> ctu.table_schema")).scalar()
            snap_fks = c.execute(text(
                "SELECT kcu.column_name FROM information_schema.table_constraints tc "
                "JOIN information_schema.key_column_usage kcu "
                "  ON tc.constraint_name = kcu.constraint_name "
                "WHERE tc.constraint_type = 'FOREIGN KEY' "
                "  AND tc.table_name = 'offer_snapshot'")).fetchall()
        assert cross == 0, f"cross-schema FKs exist: {cross}"
        assert [r[0] for r in snap_fks] == ["tripCandidateId"], snap_fks
        return ("sourceRef has no FK (mapper); offer_snapshot's only FK is "
                "the internal tripCandidateId; zero cross-schema FKs — no "
                "cross-database join is expressible")

    def d8() -> str:
        cols = set(models.TripProfile.__table__.columns.keys())
        assert "checkIn" not in cols and "checkOut" not in cols, cols
        assert "partySize" not in cols, cols
        utc = timezone.utc
        with Session() as s:
            trip = models.TripProfile(
                buyer_id="buyer-1", tier="standard",
                authorization={"method": "card_hold", "status": "AUTHORIZED"},
                modules=[models.ModuleType.TICKETS, models.ModuleType.STAY],
                travelers=[
                    models.Traveler(role=models.TravelerRole.PRIMARY,
                                    utility_weights={"comfort": 0.7}),
                    models.Traveler(role=models.TravelerRole.COMPANION,
                                    utility_weights={"comfort": 0.4}),
                ],
                stay_phases=[
                    models.StayPhase(
                        seq=1, kind=models.StayPhaseKind.EVENT,
                        property_ref="prop:venue-hotel",
                        check_in=datetime(2027, 4, 2, 15, 0, tzinfo=utc),
                        check_out=datetime(2027, 4, 4, 11, 0, tzinfo=utc),
                        occupants={"travelers": 2},
                        criteria={"tier": "event-block"}),
                    models.StayPhase(
                        seq=2, kind=models.StayPhaseKind.RECOVERY,
                        property_ref="prop:recovery-hotel",
                        check_in=datetime(2027, 4, 4, 14, 0, tzinfo=utc),
                        check_out=datetime(2027, 4, 6, 11, 0, tzinfo=utc),
                        occupants={"travelers": 2},
                        criteria={"quiet": True}),
                ])
            s.add(trip)
            s.commit()
            tid = trip.id
        with Session() as s:
            trip = s.get(models.TripProfile, tid)
            assert len(trip.travelers) == 2
            assert [t.role for t in trip.travelers] == [
                models.TravelerRole.PRIMARY, models.TravelerRole.COMPANION]
            assert [p.kind for p in trip.stay_phases] == [
                models.StayPhaseKind.EVENT, models.StayPhaseKind.RECOVERY]
            assert trip.modules == [models.ModuleType.TICKETS,
                                    models.ModuleType.STAY]
        phase_cols = set(models.StayPhase.__table__.columns.keys())
        assert {"checkIn", "checkOut"} <= phase_cols, phase_cols
        return ("2 traveler rows with roles (PRIMARY, COMPANION); 2 stay "
                "phases in seq order (EVENT, RECOVERY), each carrying its "
                "OWN checkIn/checkOut; modules is a Postgres ARRAY column; "
                "the TRIP carries no checkIn/checkOut/partySize columns")

    def d9() -> str:
        with engine.connect() as c:
            counts = {}
            for t in ("facility_profile", "package_template",
                      "procedure_class_band"):
                counts[t] = c.execute(text(
                    f"SELECT count(*) FROM {t}")).scalar()  # noqa: S608 — fixed names
            for t in ("consent_record", "health_attribute"):
                counts[f"health_restricted.{t}"] = c.execute(text(
                    f"SELECT count(*) FROM health_restricted.{t}")).scalar()
        assert all(v == 0 for v in counts.values()), counts
        tcols = set(models.Traveler.__table__.columns.keys())
        assert not any("health" in k.lower() or "consent" in k.lower()
                       for k in tcols), tcols
        return (f"dormant tables present and empty {counts}; Traveler "
                "carries no health columns; health lives only in "
                "health_restricted behind ConsentRecord")

    def d10() -> str:
        # NEGATIVE atomicity case (schema review, term 1 follow-up).
        # D3 proves the annotation and its EventLog mirror CO-OCCUR;
        # that is satisfiable by two sequential writes. Term 1
        # requires them to be ONE transaction: if the mirror's
        # EventLog insert fails, the annotation must roll back too —
        # an annotation present without its EventLog row is the
        # shadow state the term exists to prevent, arriving through
        # a different door. A temporary BEFORE INSERT blocker on
        # event_log forces the mirror insert to fail; it is dropped
        # in a finally, and the positive path is then re-proven on
        # the SAME snapshot.
        make_snapshot()
        sid = ids["snapshot"]

        def mirror_count(conn) -> int:
            return conn.execute(text(
                'SELECT count(*) FROM event_log '
                'WHERE "aggregateType" = :at AND "aggregateId" = :ai '
                'AND "eventType" = :et'),
                {"at": "OfferSnapshot", "ai": sid,
                 "et": "SNAPSHOT_DIVERGED"}).scalar()

        def current_code(conn):
            return conn.execute(text(
                'SELECT "divergenceCode" FROM offer_snapshot '
                'WHERE id = :i'), {"i": sid}).scalar()

        with engine.connect() as c:
            assert current_code(c) is None, "fresh snapshot already annotated"
            assert mirror_count(c) == 0, "fresh snapshot already mirrored"

        with engine.connect() as c:
            c.execute(text(
                "CREATE OR REPLACE FUNCTION demo_atomicity_blocker() "
                "RETURNS trigger AS $$ BEGIN "
                "RAISE EXCEPTION 'DEMO_ATOMICITY_BLOCKER: event_log "
                "insert blocked (negative atomicity test)'; "
                "END; $$ LANGUAGE plpgsql"))
            c.execute(text(
                "CREATE TRIGGER trg_demo_atomicity_blocker "
                "BEFORE INSERT ON event_log FOR EACH ROW "
                "EXECUTE FUNCTION demo_atomicity_blocker()"))
            c.commit()
        try:
            err = ""
            with engine.connect() as c:
                try:
                    c.execute(text(
                        'UPDATE offer_snapshot SET "divergenceCode" = :dc, '
                        '"divergenceAt" = :t WHERE id = :i'),
                        {"dc": "SEAT_TAKEN", "t": now, "i": sid})
                    c.commit()
                except Exception as exc:  # noqa: BLE001
                    c.rollback()
                    err = str(exc)
            assert err, (
                "annotation was ACCEPTED while its EventLog mirror "
                "insert was blocked — annotation and mirror are NOT "
                "one transaction (criterion 5 failure)")
            assert "DEMO_ATOMICITY_BLOCKER" in err, (
                f"annotation failed, but not via the blocker: {err[:200]}")
            with engine.connect() as c:
                assert current_code(c) is None, (
                    "annotation PERSISTED despite the failed mirror "
                    "insert — shadow state (criterion 5 failure)")
                assert mirror_count(c) == 0, (
                    "mirror row exists for a rolled-back annotation")
        finally:
            with engine.connect() as c:
                c.execute(text(
                    "DROP TRIGGER IF EXISTS trg_demo_atomicity_blocker "
                    "ON event_log"))
                c.execute(text(
                    "DROP FUNCTION IF EXISTS demo_atomicity_blocker()"))
                c.commit()
        # Blocker dropped: the positive path on the SAME snapshot
        # must still work — annotation applies, exactly one mirror row.
        with engine.connect() as c:
            c.execute(text(
                'UPDATE offer_snapshot SET "divergenceCode" = :dc, '
                '"divergenceAt" = :t WHERE id = :i'),
                {"dc": "SEAT_TAKEN", "t": now, "i": sid})
            c.commit()
            assert current_code(c) == "SEAT_TAKEN"
            assert mirror_count(c) == 1, "positive path mirror missing"
        return ("with the mirror's EventLog INSERT blocked, the "
                "annotation errored via the blocker and rolled back "
                "with it (divergenceCode still NULL, 0 mirror rows); "
                "blocker dropped, the same snapshot then annotated "
                "cleanly with exactly one mirror row — annotation "
                "and mirror are a single transaction")

    check("D1 migration applies", d1)
    check("D2 table inventory", d2)
    check("D3 OfferSnapshot immutability (DB trigger + ORM guard)", d3)
    check("D4 EventLog append-only (DB trigger + ORM guard)", d4)
    check("D5 IdempotencyKey uniqueness (Postgres)", d5)
    check("D6 generated Pydantic: payload union + typed divergence", d6)
    check("D7 sourceRef is a reference, not a FK", d7)
    check("D8 TripProfile: travelers as rows, StayPhase[] structure", d8)
    check("D9 dormant health set: present, unused, isolated", d9)
    check("D10 divergence mirror atomicity (negative case)", d10)

    failed = [r for r in RESULTS if not r[1]]
    print("=" * 72)
    print(f"RESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed"
          + ("" if not failed else f" — FAILED: {[r[0] for r in failed]}"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
