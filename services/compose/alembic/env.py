"""Alembic environment — UZEMARKETS composition layer.

The migration authority for database `uzemarkets-compose` under the
ratified (C) pattern (SQLAlchemy + Alembic, the Assurative V2 pattern).
- The connection URL comes from src/config.py (COMPOSE_DATABASE_URL env
  override; the database NAME is uzemarkets-compose — config.py).
- target_metadata is src/models.py's metadata — the single authoring
  source. Migrations are generated from it, then reviewed by hand;
  additive-only discipline from here forward.
- include_schemas=True: the health_restricted namespace is part of this
  database and migrates with it.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import models  # noqa: E402  (the authoring source)
from config import database_url  # noqa: E402

config = context.config
config.set_main_option("sqlalchemy.url", database_url())

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = models.Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
