"""Database access for the composition-layer runtime (Sprint 1).

Sync SQLAlchemy over the same config the schema layer uses
(config.database_url() — COMPOSE_DATABASE_URL overrides). The engine
is built lazily and cached per URL so tests can point the service at
the throwaway demonstration database by setting the env var before
import. Endpoints are sync `def`s, so FastAPI runs them in its
threadpool and the sync session never blocks the event loop.
"""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

import config

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(config.database_url(), pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_engine)
    return _engine


def session() -> Session:
    engine()
    assert _SessionLocal is not None
    return _SessionLocal()


def get_session():
    """FastAPI dependency: one session per request."""
    db = session()
    try:
        yield db
    finally:
        db.close()


def database_ok() -> bool:
    try:
        with engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 — health reports, never raises
        return False


def current_revision() -> str | None:
    """The Alembic head recorded in the connected database, or None
    if the database is unreachable or not yet migrated."""
    try:
        with engine().connect() as conn:
            return conn.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar()
    except Exception:  # noqa: BLE001
        return None
