"""Project-bid endpoint (owner tap, 2026-11-13).

POST /api/v1/talent/project-bid — the agentic bidding mock:
a developer's agent posts a design brief, a stated budget,
and the bids received; the endpoint ranks them against the
budget and names the lowest in-budget bid. MOCK by
construction and labelled so in every response: it performs
a budget check only, computes no yield on cost, awards
nothing, and records nothing.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import talent_profile

router = APIRouter(prefix="/api/v1/talent", tags=["talent"])


class ProjectBidIn(BaseModel):
    brief: str = ""
    budget_usd: float = 0
    bids: list[dict[str, Any]] = []


@router.post("/project-bid")
def project_bid(body: ProjectBidIn):
    evaluation, problems = talent_profile.evaluate_project_bids(
        body.brief, body.budget_usd, body.bids
    )
    if problems:
        return JSONResponse(
            status_code=422,
            content={
                "error": "INSUFFICIENT_DATA",
                "missing_fields": problems,
            },
        )
    return JSONResponse(content=evaluation)
