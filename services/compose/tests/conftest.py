"""Test substrate for the Sprint 1 intake slice.

REAL PostgreSQL, the demonstration's substrate: the pgserver-bundled
PostgreSQL 16.2 binaries running as a local instance at
127.0.0.1:55433 — the same database the Sprint 0 demo resets
(uzemarkets-compose, a throwaway). The session fixture drops and
recreates it, migrates it with Alembic (`upgrade head`, a subprocess
exactly as scripts/demo_schema.py does), and seeds the Sprint 1
QuestionManifest. COMPOSE_DATABASE_URL overrides the target, as
everywhere in this service; the database NAME must remain
uzemarkets-compose (guard below), because the fixture resets it.
Nothing here runs on SQLite or a mock: the classifier's pure tests
need no database, and the flow tests run against the real schema —
triggers, ARRAY columns, typed JSON and all.
"""

from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMPOSE_DIR = os.path.dirname(HERE)
SRC_DIR = os.path.join(COMPOSE_DIR, "src")
GEN_DIR = os.path.join(SRC_DIR, "generated")
for path in (SRC_DIR, GEN_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault(
    "COMPOSE_DATABASE_URL",
    "postgresql+psycopg://postgres@127.0.0.1:55433/uzemarkets-compose",
)

import pytest  # noqa: E402

DATABASE_URL = os.environ["COMPOSE_DATABASE_URL"]
assert DATABASE_URL.rsplit("/", 1)[-1].split("?")[0] == "uzemarkets-compose", (
    "guard: the test fixture resets its target database; it must be "
    "named uzemarkets-compose"
)


@pytest.fixture(scope="session")
def migrated_db():
    """Fresh database, migrated to head, seed manifest loaded."""
    import sqlalchemy
    from sqlalchemy import text

    admin_url = DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    admin = sqlalchemy.create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.exec_driver_sql('DROP DATABASE IF EXISTS "uzemarkets-compose"')
        c.exec_driver_sql('CREATE DATABASE "uzemarkets-compose"')
    admin.dispose()

    env = dict(os.environ, COMPOSE_DATABASE_URL=DATABASE_URL)
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=COMPOSE_DIR, env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"alembic upgrade failed: {proc.stderr[-400:]}"

    import db
    import seed

    session = db.session()
    try:
        seed.seed(session)
    finally:
        session.close()
    return DATABASE_URL


@pytest.fixture()
def client(migrated_db):
    """A TestClient over a clean intake_draft table (manifest kept)."""
    import db
    import models
    from app import create_app
    from fastapi.testclient import TestClient

    session = db.session()
    try:
        session.query(models.IntakeDraft).delete()
        session.commit()
    finally:
        session.close()
    return TestClient(create_app())


# --- Sprint 1.5 marketplace fixtures (Day 2/3) ----------------------
# Shared by test_intents.py and test_settle.py: a TestClient over
# clean intent tables with the demo fixture's micro-regions seeded.

FIXTURE_PATH = os.path.join(
    COMPOSE_DIR, "scripts", "fixtures", "sprint15_demo.json"
)


@pytest.fixture()
def demo_fixture():
    import json

    with open(FIXTURE_PATH) as fh:
        return json.load(fh)


@pytest.fixture()
def market_client(migrated_db, demo_fixture):
    import db
    import models
    from app import create_app
    from fastapi.testclient import TestClient

    session = db.session()
    try:
        session.query(models.Match).delete()
        session.query(models.Bid).delete()
        session.query(models.Intent).delete()
        session.query(models.MicroRegion).delete()
        # EventLog is append-only by design (Sprint 0 criterion 6) —
        # it is never cleaned between tests; event assertions filter
        # by aggregate id instead.
        session.commit()
        for row in demo_fixture["microRegions"]:
            session.add(
                models.MicroRegion(
                    id=row["id"],
                    label=row["label"],
                    metro=row["metro"],
                    region=row["region"],
                )
            )
        session.commit()
    finally:
        session.close()
    return TestClient(create_app())
