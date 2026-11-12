"""UZEMARKETS composition layer — runtime (Sprint 1, slices 1–4).

App factory in the sibling service's shape (services/api's create_app).
Mounted: /health, the intakes router (slice 1), the snapshots
router carrying the R4 read-through reconciliation (slice 2), the
approvals router — the human approval gate (slice 3), whose reads
and decisions run slice 2's reconciliation at request time — and
the commitments router (slice 4): commitment recording from an
APPROVED approval, gated by one final commit-time reconciliation
and carried by a Postgres idempotency key. That completes the
Sprint 1 surface.

Run (toolchain venv, from services/compose):
    PYTHONPATH=src:src/generated uvicorn app:app --port 8100
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

import agtech
import approvals
import assuraties
import email_gateway
import commitments
import db
import intakes
import intents
import metering
import partners
import agents
import pulse
import settle
import snapshots
import assign
import auctions
import builders
import alpha
import ticketing
import proforma
import matrix
import contributions
import costar
import underwrite_engine
import treasury
import treasury_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="UZEMARKETS composition layer — intake service",
        description=(
            "Sprint 1: intake drafts + deterministic classify(); "
            "R4 read-through reconciliation for ticket-kind snapshots; "
            "the human approval gate over them; commitment recording "
            "from an approved approval, idempotency-keyed."
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
    app.include_router(commitments.router)
    app.include_router(intents.router)
    app.include_router(settle.router)
    app.include_router(metering.router)
    app.include_router(pulse.router)
    app.include_router(agtech.router)
    app.include_router(partners.router)
    app.include_router(partners.admin_router)
    app.include_router(agents.router)
    app.include_router(treasury_router.router)
    app.include_router(treasury.router)
    app.include_router(assign.router)
    app.include_router(auctions.router)
    app.include_router(builders.router)
    app.include_router(alpha.router)
    app.include_router(ticketing.router)
    app.include_router(proforma.router)
    app.include_router(matrix.router)
    app.include_router(contributions.router)
    app.include_router(costar.router)
    app.include_router(underwrite_engine.router)
    app.include_router(assuraties.router)
    app.include_router(email_gateway.router)
    return app


app = create_app()
