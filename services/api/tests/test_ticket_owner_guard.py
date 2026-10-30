"""Evidence tests for the Ticket owner guard trigger.

Artifact under test (executed verbatim, never copied):
    prisma/manual-migrations/2026-10-30-ticket-owner-guard.sql

What it proves (the mirror's evidence discipline — positive, negative,
atomicity, regression):
  * POSITIVE  — the transfer endpoint's exact update shape
    (ownerId + status='transferred' in one statement, tickets.py)
    succeeds.
  * NEGATIVE  — an ownerId change with status untouched, with
    status='active', or with status='listed' is REFUSED by the
    trigger, and the row is byte-identical afterward.
  * ATOMICITY — inside one explicit transaction, a legitimate update
    followed by a refused ownerId change rolls back TOGETHER: the
    guard's refusal aborts the whole transaction, not just itself.
  * NULL SAFETY — ownerId value->NULL and NULL->value changes are
    guarded exactly like value->value (IS DISTINCT FROM).
  * REGRESSION — the other Ticket writers' shapes still work:
    status-only active->listed (listing creation), a tier-only
    update, and INSERT with an initial ownerId (guard is UPDATE-only).
  * LEDGER    — the artifact records its own application in
    public.ddl_ledger (id '2026-10-30-ticket-owner-guard'), and the
    presence check the composition layer will use — pg_trigger
    lookup for trg_ticket_owner_guard, corroborated by the ledger
    row — finds the guard.

Substrate (stated, not hidden): REAL PostgreSQL 16.2 — this VM's
pgserver-bundled instance on 127.0.0.1:55433, the same substrate the
composition layer's schema demo uses. A throwaway database
("services_api_ticket_guard_test") is dropped/created per run. The
"Ticket" table is built faithful to prisma/schema.prisma (UUID PK
via gen_random_uuid(), quoted Prisma column names, tier/status
defaults); BOTH foreign keys are real — minimal "User" and "Event"
parent tables (id only) stand behind them, no FK is dropped.
Override the server with TICKET_GUARD_PG_BASE. If no server answers,
the module SKIPS rather than failing.

Run (needs an interpreter with pytest + psycopg; on this VM):
    ~/workspace/tools/composevenv/bin/python -m pytest \
        tests/test_ticket_owner_guard.py -v
Evidence log: tests/ticket_owner_guard_evidence.log
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import psycopg
import pytest

BASE = os.environ.get(
    "TICKET_GUARD_PG_BASE", "postgresql://postgres@127.0.0.1:55433"
)
TEST_DB = "services_api_ticket_guard_test"
GUARD_SQL = (
    Path(__file__).resolve().parent.parent
    / "prisma"
    / "manual-migrations"
    / "2026-10-30-ticket-owner-guard.sql"
)
MARKER = "TICKET_OWNER_GUARD"

SCHEMA_DDL = """
CREATE TABLE "User" (id UUID PRIMARY KEY DEFAULT gen_random_uuid());
CREATE TABLE "Event" (id UUID PRIMARY KEY DEFAULT gen_random_uuid());
CREATE TABLE "Ticket" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "eventId" UUID NOT NULL REFERENCES "Event"(id),
    "ownerId" UUID REFERENCES "User"(id),
    tier TEXT NOT NULL DEFAULT 'general',
    status TEXT NOT NULL DEFAULT 'active',
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

ROW_SQL = (
    'SELECT id, "eventId", "ownerId", tier, status, "createdAt", '
    '"updatedAt" FROM "Ticket" WHERE id = %s'
)


@pytest.fixture(scope="session", autouse=True)
def _database():
    try:
        admin = psycopg.connect(f"{BASE}/postgres", autocommit=True)
    except psycopg.OperationalError as exc:
        pytest.skip(f"no PostgreSQL at {BASE} ({exc})")
    with admin:
        admin.execute(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)')
        admin.execute(f'CREATE DATABASE "{TEST_DB}"')
    conn = psycopg.connect(f"{BASE}/{TEST_DB}", autocommit=True)
    conn.execute(SCHEMA_DDL)
    # The artifact under test, applied verbatim.
    conn.execute(GUARD_SQL.read_text())
    yield conn
    conn.close()
    with psycopg.connect(f"{BASE}/postgres", autocommit=True) as admin:
        admin.execute(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)')


@pytest.fixture()
def conn(_database):
    return _database


def _user(conn) -> uuid.UUID:
    return conn.execute('INSERT INTO "User" DEFAULT VALUES RETURNING id').fetchone()[0]


def _ticket(conn, owner: uuid.UUID | None, status: str = "active") -> uuid.UUID:
    event_id = conn.execute(
        'INSERT INTO "Event" DEFAULT VALUES RETURNING id'
    ).fetchone()[0]
    return conn.execute(
        'INSERT INTO "Ticket" ("eventId", "ownerId", status) '
        "VALUES (%s, %s, %s) RETURNING id",
        (event_id, owner, status),
    ).fetchone()[0]


def _row(conn, ticket_id: uuid.UUID):
    return conn.execute(ROW_SQL, (ticket_id,)).fetchone()


def _expect_guard_refusal(conn, sql: str, params: tuple) -> None:
    with pytest.raises(psycopg.errors.RaiseException) as excinfo:
        conn.execute(sql, params)
    assert MARKER in str(excinfo.value), f"refused by the wrong mechanism: {excinfo.value}"


# ---------------------------------------------------------------- POSITIVE

def test_positive_transfer_shape_succeeds(conn):
    """The transfer endpoint's exact update (tickets.py: ownerId +
    status='transferred' in one statement) passes the guard."""
    owner, new_owner = _user(conn), _user(conn)
    tid = _ticket(conn, owner)
    conn.execute(
        'UPDATE "Ticket" SET "ownerId" = %s, status = \'transferred\' WHERE id = %s',
        (new_owner, tid),
    )
    row = _row(conn, tid)
    assert row[2] == new_owner and row[4] == "transferred"


# ---------------------------------------------------------------- NEGATIVE

def test_negative_owner_change_status_untouched_refused(conn):
    owner, new_owner = _user(conn), _user(conn)
    tid = _ticket(conn, owner)
    before = _row(conn, tid)
    _expect_guard_refusal(
        conn, 'UPDATE "Ticket" SET "ownerId" = %s WHERE id = %s', (new_owner, tid)
    )
    assert _row(conn, tid) == before, "row changed despite the refusal"


def test_negative_owner_change_status_active_refused(conn):
    owner, new_owner = _user(conn), _user(conn)
    tid = _ticket(conn, owner)
    before = _row(conn, tid)
    _expect_guard_refusal(
        conn,
        'UPDATE "Ticket" SET "ownerId" = %s, status = \'active\' WHERE id = %s',
        (new_owner, tid),
    )
    assert _row(conn, tid) == before


def test_negative_owner_change_status_listed_refused(conn):
    owner, new_owner = _user(conn), _user(conn)
    tid = _ticket(conn, owner, status="listed")
    before = _row(conn, tid)
    _expect_guard_refusal(
        conn,
        'UPDATE "Ticket" SET "ownerId" = %s, status = \'listed\' WHERE id = %s',
        (new_owner, tid),
    )
    assert _row(conn, tid) == before


def test_negative_owner_change_is_transaction_atomic(conn):
    """A refused ownerId change aborts its whole transaction: a prior
    legitimate update in the same transaction rolls back with it."""
    owner, new_owner = _user(conn), _user(conn)
    tid = _ticket(conn, owner)
    before = _row(conn, tid)
    txn = psycopg.connect(f"{BASE}/{TEST_DB}", autocommit=False)
    try:
        txn.execute('UPDATE "Ticket" SET tier = \'vip\' WHERE id = %s', (tid,))
        with pytest.raises(psycopg.errors.RaiseException) as excinfo:
            txn.execute(
                'UPDATE "Ticket" SET "ownerId" = %s WHERE id = %s',
                (new_owner, tid),
            )
        assert MARKER in str(excinfo.value)
        txn.rollback()
    finally:
        txn.close()
    after = _row(conn, tid)
    assert after == before, (
        "the legitimate tier update survived the rollback — "
        "the refusal is not transaction-atomic"
    )


def test_negative_owner_null_transitions_refused(conn):
    """NULL-safety: value->NULL and NULL->value ownerId changes are
    guarded exactly like value->value (IS DISTINCT FROM)."""
    owner, new_owner = _user(conn), _user(conn)
    tid = _ticket(conn, owner)
    before = _row(conn, tid)
    _expect_guard_refusal(
        conn, 'UPDATE "Ticket" SET "ownerId" = NULL WHERE id = %s', (tid,)
    )
    assert _row(conn, tid) == before

    tid2 = _ticket(conn, None)
    before2 = _row(conn, tid2)
    _expect_guard_refusal(
        conn, 'UPDATE "Ticket" SET "ownerId" = %s WHERE id = %s', (new_owner, tid2)
    )
    assert _row(conn, tid2) == before2


# -------------------------------------------------------------- REGRESSION

def test_regression_status_only_listed_succeeds(conn):
    """Listing creation's shape (listings.py): status active->listed,
    ownerId untouched."""
    tid = _ticket(conn, _user(conn))
    conn.execute('UPDATE "Ticket" SET status = \'listed\' WHERE id = %s', (tid,))
    assert _row(conn, tid)[4] == "listed"


def test_regression_other_field_update_succeeds(conn):
    tid = _ticket(conn, _user(conn))
    conn.execute('UPDATE "Ticket" SET tier = \'vip\' WHERE id = %s', (tid,))
    assert _row(conn, tid)[3] == "vip"


def test_regression_insert_with_initial_owner_succeeds(conn):
    """Ticket creation's shape: INSERT carries the initial ownerId;
    the guard is BEFORE UPDATE only. An unissued (NULL owner) insert
    is equally fine."""
    owner = _user(conn)
    tid = _ticket(conn, owner)
    assert _row(conn, tid)[2] == owner
    tid2 = _ticket(conn, None)
    assert _row(conn, tid2)[2] is None


# ------------------------------------------------------------------ LEDGER

def test_ledger_row_recorded_and_trigger_present(conn):
    """DDL-ledger amendment: applying the artifact records itself in
    public.ddl_ledger under its own id, and the composition layer's
    presence check (pg_trigger lookup for trg_ticket_owner_guard,
    corroborated by this ledger row) finds the guard."""
    rows = conn.execute(
        "SELECT note FROM public.ddl_ledger WHERE id = %s",
        ("2026-10-30-ticket-owner-guard",),
    ).fetchall()
    assert len(rows) == 1, f"expected exactly one ledger row, got {rows}"
    assert rows[0][0] == "Ticket ownerId guard trigger (trg_ticket_owner_guard)"
    present = conn.execute(
        "SELECT 1 FROM pg_trigger "
        "WHERE tgname = 'trg_ticket_owner_guard' AND NOT tgisinternal"
    ).fetchone()
    assert present is not None, "pg_trigger presence check found no guard trigger"
