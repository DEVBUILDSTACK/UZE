"""SURA endpoints (spec §5, 2026-11-17:
docs/specifications/sura-agentic-guidance-v1.md).

The headless plane of SURA, the agentic guidance layer
over the Talent marketplace, under the existing
/api/v1/talent prefix and in the existing
INSUFFICIENT_DATA discipline (422 naming the fields):

- POST /sura/sourced — ingest one sourced feed record.
  Provenance is REQUIRED; the profile validates as a
  TalentProfile; the record persists to the feed store
  and the profile enters the solver pool marked.
- GET /sura/sourced — the sourced supply, with provenance
  and switch-likelihood.
- POST /sura/guidance/demand — demand guidance for one
  employer need, over the applied ∪ sourced pool.
- POST /sura/guidance/supply — supply guidance for one
  candidate against open role listings: geo-filtered,
  fit-ranked, explained.

HONESTY: nothing here fetches a signal from anywhere.
The feed asserts; SURA computes. Scores are the labelled
heuristic v1 of sura.py — deterministic arithmetic over
declared fields and supplied signals, never an "AI
match" claim.
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


def combined_pool() -> list[dict[str, Any]]:
    """The marketplace pool: applied profiles ∪ sourced
    profiles. Inside the solver and the guidance the two
    are treated identically; sourced profiles carry their
    provenance with them."""
    return talent_ats.load_profiles() + sura.load_sourced_profiles()


class SourcedIn(BaseModel):
    profile: dict[str, Any] = {}
    provenance: dict[str, Any] = {}
    signals: dict[str, Any] | None = None
    geo_availability: list[Any] | None = None


@router.post("/sura/sourced")
def ingest_sourced(body: SourcedIn):
    record, problems = sura.validate_feed_record(body.model_dump())
    if problems:
        return _insufficient(problems)
    entry = sura.record_sourced(record)
    return JSONResponse(
        content={"status": "recorded", **entry["record"]}
    )


@router.get("/sura/sourced")
def list_sourced():
    profiles = sura.load_sourced_profiles()
    return JSONResponse(
        content={"count": len(profiles), "profiles": profiles}
    )


class DemandGuidanceIn(BaseModel):
    need: dict[str, Any] = {}


@router.post("/sura/guidance/demand")
def demand_guidance(body: DemandGuidanceIn):
    result = sura.demand_guidance(body.need, combined_pool())
    # Record the guidance event — the RL talent
    # environment's episode feed (spec §9.2).
    top = result["candidates"][0] if result["candidates"] else None
    event = sura.record_guidance_event(
        side="demand",
        subject=str(body.need.get("role") or "ROLE_REQUIREMENT"),
        context={
            "role": body.need.get("role"),
            "role_family": body.need.get(
                "role_family", "operations"),
            "opportunity_category": result["category"],
            "skills": list(body.need.get("skills") or []),
            "geo_requirement": sura.need_geo_requirement(
                body.need),
            "candidate": top["name"] if top else None,
        },
        guidance={
            "status": result["status"],
            "notes": result["recommendations"],
            "top_fit_score": (
                top["fit"]["score"] if top else None),
            "scores": {"pool": result["pool"]},
        },
    )
    return JSONResponse(
        content={**result, "recorded_event_id": event["event_id"]}
    )


class SupplyGuidanceIn(BaseModel):
    profile_name: str = ""
    profile: dict[str, Any] | None = None
    needs: list[Any] | None = None


@router.post("/sura/guidance/supply")
def supply_guidance(body: SupplyGuidanceIn):
    if not isinstance(body.needs, list):
        return _insufficient(["needs"])
    profile: dict[str, Any] | None = None
    if body.profile is not None:
        profile, problems = talent_profile.validate_profile(
            body.profile
        )
        if problems:
            return _insufficient(
                [f"profile.{p}" for p in problems]
            )
    elif body.profile_name.strip():
        for candidate in combined_pool():
            if candidate.get("name") == body.profile_name.strip():
                profile = candidate
                break
        if profile is None:
            return JSONResponse(
                status_code=404,
                content={"error": "PROFILE_NOT_FOUND"},
            )
    else:
        return _insufficient(["profile_name"])
    result = sura.supply_guidance(profile, body.needs)
    # Record the guidance event — the RL talent
    # environment's episode feed (spec §9.2).
    top_role = result["roles"][0] if result["roles"] else None
    top_fit = top_role["fit"] if top_role else {}
    event = sura.record_guidance_event(
        side="supply",
        subject=str(profile.get("name") or ""),
        context={
            "role": top_role["role"] if top_role else None,
            "role_family": (
                top_role["role_family"] if top_role else None),
            "opportunity_category": (
                top_role["opportunity_category"]
                if top_role else None),
            "skills": sorted(
                (top_fit.get("skills_covered") or [])
                + (top_fit.get("skills_missing") or [])
            ),
            "geo_requirement": (
                top_role["geo_requirement"] if top_role else None),
            "candidate": profile.get("name"),
        },
        guidance={
            "status": "guided" if result["roles"] else "no_roles",
            "notes": result["notes"],
            "top_fit_score": (
                top_fit.get("score") if top_role else None),
            "scores": {
                "roles": len(result["roles"]),
                "excluded_by_geo": result["excluded_by_geo"],
            },
        },
    )
    return JSONResponse(
        content={**result, "recorded_event_id": event["event_id"]}
    )
