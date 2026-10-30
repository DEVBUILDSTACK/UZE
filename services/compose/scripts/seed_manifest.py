#!/usr/bin/env python
"""Seed the Sprint 1 QuestionManifest into the composition database.

Thin CLI over src/seed.py (the seed data + the idempotent loader live
there, importable by tests). Targets COMPOSE_DATABASE_URL if set,
else the demonstration substrate — the same pgserver PostgreSQL the
Sprint 0 demo uses (postgresql+psycopg://postgres@127.0.0.1:55433).
The database must already be migrated (`alembic upgrade head`).
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMPOSE_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(COMPOSE_DIR, "src"))
sys.path.insert(0, os.path.join(COMPOSE_DIR, "src", "generated"))

os.environ.setdefault(
    "COMPOSE_DATABASE_URL",
    "postgresql+psycopg://postgres@127.0.0.1:55433/uzemarkets-compose",
)


def main() -> int:
    import db
    import seed

    session = db.session()
    try:
        row = seed.seed(session)
        print(
            f"seed manifest: key={row.key} version={row.version} "
            f"active={row.active} slots={len(row.questions)}"
        )
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
