"""UZEMARKETS composition layer — intake service (Sprint 1, slice 1).

App factory in the sibling service's shape (services/api's create_app):
this slice mounts exactly one router — intakes — plus /health. The
R4 read-through, the approval gate, and commitment recording are
later Sprint 1 slices and are NOT mounted here; an honest surface is
part of the slice discipline.

Run (toolchain venv, from services/compose):
    PYTHONPATH=src:src/generated uvicorn app:app --port 8100
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

import db
import intakes


def create_app() -> FastAPI:
    app = FastAPI(
        title="UZEMARKETS composition layer — intake service",
        description="Sprint 1 slice 1: intake drafts + deterministic classify().",
    )

    @app.get("/health", tags=["health"])
    def health():
        if not db.database_ok():
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unavailable",
                    "database": False,
                    "schemaRevision": None,
                },
            )
        return {
            "status": "ok",
            "database": True,
            "schemaRevision": db.current_revision(),
        }

    app.include_router(intakes.router)
    return app


app = create_app()
