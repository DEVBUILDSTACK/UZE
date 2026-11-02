"""UZEMARKETS composition layer — runtime (Sprint 1, slices 1–3).

App factory in the sibling service's shape (services/api's create_app).
Mounted: /health, the intakes router (slice 1), the snapshots
router carrying the R4 read-through reconciliation (slice 2), and
the approvals router — the human approval gate (slice 3), whose
reads and decisions run slice 2's reconciliation at request time.
Commitment recording is the remaining Sprint 1 slice and is NOT
mounted here; an honest surface is part of the slice discipline.

Run (toolchain venv, from services/compose):
    PYTHONPATH=src:src/generated uvicorn app:app --port 8100
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

import approvals
import db
import intakes
import snapshots


def create_app() -> FastAPI:
    app = FastAPI(
        title="UZEMARKETS composition layer — intake service",
        description=(
            "Sprint 1: intake drafts + deterministic classify(); "
            "R4 read-through reconciliation for ticket-kind snapshots; "
            "the human approval gate over them."
        ),
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
    app.include_router(snapshots.router)
    app.include_router(approvals.router)
    return app


app = create_app()
