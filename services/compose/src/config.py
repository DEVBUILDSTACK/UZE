"""Connection configuration for the UZEMARKETS composition layer.

Schema-review criterion 11: the database name is `uzemarkets-compose`
(James's tap, 2026-10-30). It is named here, in the connection config —
not inferred from a host, not defaulted by a tool.

The URL is overridable via the COMPOSE_DATABASE_URL environment variable
(deployments, tests, the Sprint 0 demo). No credentials live in this file;
the default below is a shape only — user/host are placeholders for the
operator's own .env (see .env.example), and there are no secrets here.
"""

from __future__ import annotations

import os

DATABASE_NAME = "uzemarkets-compose"

# Postgres schema (namespace) holding the consent-gated health tables.
# Nothing outside this namespace references into it, and nothing inside it
# is referenced from the public schema — see models.py.
RESTRICTED_SCHEMA = "health_restricted"

_DEFAULT_URL = (
    "postgresql+psycopg://compose@127.0.0.1:5432/" + DATABASE_NAME
)


def database_url() -> str:
    """The composition layer's database URL (env override wins)."""
    url = os.environ.get("COMPOSE_DATABASE_URL", _DEFAULT_URL)
    # Hosted Postgres providers (Render and peers) hand out
    # driver-less postgresql:// URLs; the runtime driver is
    # psycopg v3, so name it explicitly when no driver is set.
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    elif url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    return url
