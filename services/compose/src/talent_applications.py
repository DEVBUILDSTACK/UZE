"""Talent ATS + solver endpoints (extension spec §7,
2026-11-17).

The headless plane of the talent extension, under the
existing /api/v1/talent prefix and in the existing
INSUFFICIENT_DATA discipline (422 naming the fields):

- POST /intents/solve — the NEAR AI Intents-pattern solver
  interface: a role-requirement intent in, scorecard-ranked
  candidate offers out, with category routing and the NEAR
  AI honesty label in band. The current solver is the
  deterministic matcher; NEAR AI attested inference is
  credit-blocked (HTTP 402) and is labelled unavailable,
  never simulated.
- POST /assessments — record a pre-assessment object
  against a named profile.
- POST /applications — open an application at RECOMMENDED.
- GET /applications/{id} — the two-way view: current state,
  full event stream, message thread, one record.
- POST /applications/{id}/transition — advance the state
  machine; the transition is recorded as an event; an
  illegal transition is refused by name.
- POST /applications/{id}/messages — append to the
  application's message thread.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import sura
import talent_ats
import talent_profile

router = APIRouter(prefix="/api/v1/talent", tags=["talent"])


def _insufficient(problems: list[str]) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "INSUFFICIENT_DATA",
            "missing_fields": problems,
        },
    )


def _not_found() -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": "APPLICATION_NOT_FOUND"},
    )


class SolveIn(BaseModel):
    need: dict[str, Any] = {}


@router.post("/intents/solve")
def solve(body: SolveIn):
    # The solver pool is applied ∪ sourced supply (SURA
    # spec §3.2): sourced candidates — ingested through
    # the SURA feed with provenance marked — are treated
    # identically to applied candidates inside the solver,
    # and their provenance rides in every offer.
    pool = talent_ats.load_profiles() + sura.load_sourced_profiles()
    return JSONResponse(
        content=talent_ats.solve_intent(body.need, pool)
    )


class AssessmentIn(BaseModel):
    profile_name: str = ""
    assessment: dict[str, Any] = {}


@router.post("/assessments")
def record_assessment(body: AssessmentIn):
    problems: list[str] = []
    if not body.profile_name.strip():
        problems.append("profile_name")
    assessment, aproblems = talent_profile.validate_assessment(
        body.assessment
    )
    problems += [f"assessment.{p}" for p in aproblems]
    if problems:
        return _insufficient(problems)
    record = talent_ats.record_assessment(
        body.profile_name.strip(), assessment
    )
    return JSONResponse(
        content={"status": "recorded", **record}
    )


class ApplicationIn(BaseModel):
    profile_ref: str = ""
    role_ref: str = ""
    actor: str = "system"


@router.post("/applications")
def create_application(body: ApplicationIn):
    problems = [
        field
        for field in ("profile_ref", "role_ref")
        if not getattr(body, field).strip()
    ]
    if problems:
        return _insufficient(problems)
    app = talent_ats.new_application(
        body.profile_ref.strip(),
        body.role_ref.strip(),
        body.actor.strip() or "system",
    )
    talent_ats.record_application(app)
    # Settle any linked SURA guidance events (spec §9.2):
    # entering the lifecycle marks the outcome matched.
    sura.settle_outcomes_for_application(app)
    return JSONResponse(content=app)


@router.get("/applications/{application_id}")
def get_application(application_id: str):
    app = talent_ats.load_application(application_id)
    if app is None:
        return _not_found()
    return JSONResponse(content=app)


class TransitionIn(BaseModel):
    to_state: str = ""
    actor: str = "system"


@router.post("/applications/{application_id}/transition")
def transition_application(application_id: str, body: TransitionIn):
    app = talent_ats.load_application(application_id)
    if app is None:
        return _not_found()
    updated, problems = talent_ats.apply_transition(
        app, body.to_state, body.actor.strip() or "system"
    )
    if problems == ["transition"]:
        return JSONResponse(
            status_code=422,
            content={
                "error": "ILLEGAL_TRANSITION",
                "from_state": app["state"],
                "to_state": body.to_state.strip().upper(),
            },
        )
    if problems:
        return _insufficient(problems)
    talent_ats.record_transition(updated, updated["events"][-1])
    # Settle linked SURA guidance events from the new
    # lifecycle state (spec §9.2) — ACCEPTED settles
    # placed/accepted; REJECTED settles rejected.
    sura.settle_outcomes_for_application(updated)
    return JSONResponse(content=updated)


class MessageIn(BaseModel):
    author: str = ""
    body: str = ""


@router.post("/applications/{application_id}/messages")
def post_message(application_id: str, body: MessageIn):
    app = talent_ats.load_application(application_id)
    if app is None:
        return _not_found()
    updated, problems = talent_ats.add_message(
        app, body.author, body.body
    )
    if problems:
        return _insufficient(problems)
    talent_ats.record_message(updated, updated["messages"][-1])
    return JSONResponse(content=updated)
