"""Talent ATS — applications, lifecycle, and the intents
solver (extension spec, 2026-11-17:
docs/specifications/talent-extension-headsin-v1.md).

The ATS is the Enterprise Services workflow layer operating
on Talent-layer people. Three things live here:

1. The application state machine (spec §2.6): one state,
   seen identically by candidate and employer — the two-way
   lifecycle modelled on HeadsIn's public product:
   RECOMMENDED → APPLIED → IN_PROGRESS → ACCEPTED /
   REJECTED. Every transition is an event on an append-only
   record; message threads are bound to the application.

2. Assessment records (spec §2.3): a pre-assessment can be
   recorded against a named profile after the profile lands.

3. The solver (spec §5): employer role requirements are
   expressed as INTENTS; candidate supply — human profiles
   and agentic services alike — responds as solvers. The
   current solver implementation is the existing
   deterministic matcher behind this interface.

HONESTY (standing, never softened): NEAR AI attested
inference on our side is credit-blocked (HTTP 402, $0 org
balance). Nothing here performs or claims live NEAR AI
inference; every solver response carries that state in
band, following the repo's labelled-mock discipline.

Storage (honest scope): v1 persists to append-only JSONL
files (env TALENT_APPLICATIONS_PATH / TALENT_ASSESSMENTS_
PATH) — the same pattern as talent profiles and referrals;
a database table is a later migration.

Clean-room note: the lifecycle shape is modelled on
HeadsIn's publicly observable product behaviour; this is
our own implementation. No HeadsIn code is used.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import talent_profile

APPLICATION_STATES: tuple[str, ...] = (
    "RECOMMENDED",
    "APPLIED",
    "IN_PROGRESS",
    "ACCEPTED",
    "REJECTED",
)

# Legal transitions. ACCEPTED and REJECTED are terminal.
# ACCEPTED is the settlement point of a match: it produces
# the placement record that feeds Enterprise Services
# payroll setup (extension spec §4.3).
TRANSITIONS: dict[str, frozenset] = {
    "RECOMMENDED": frozenset({"APPLIED"}),
    "APPLIED": frozenset({"IN_PROGRESS", "REJECTED"}),
    "IN_PROGRESS": frozenset({"ACCEPTED", "REJECTED"}),
    "ACCEPTED": frozenset(),
    "REJECTED": frozenset(),
}

NEAR_AI_INFERENCE_STATE: dict[str, Any] = {
    "provider": "NEAR AI",
    "status": "unavailable",
    "detail": (
        "NEAR AI attested inference is credit-blocked "
        "(HTTP 402, $0 org balance); matching ran on the "
        "deterministic matcher, not on NEAR AI inference."
    ),
}

SOLVER_NAME = "deterministic_matcher_v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Applications (pure state machine) ---


def new_application(
    profile_ref: str, role_ref: str, actor: str = "system"
) -> dict[str, Any]:
    """Open an application at RECOMMENDED. The creation is
    the first event on its record."""
    app = {
        "application_id": "app_" + uuid.uuid4().hex[:12],
        "profile_ref": profile_ref,
        "role_ref": role_ref,
        "state": "RECOMMENDED",
        "events": [],
        "messages": [],
    }
    app["events"].append({
        "type": "created",
        "from_state": None,
        "to_state": "RECOMMENDED",
        "actor": actor,
        "at": _now(),
    })
    return app


def apply_transition(
    app: dict[str, Any], to_state: Any, actor: str = "system"
) -> tuple[dict[str, Any] | None, list[str]]:
    """Advance the state machine. Returns (updated, []) or
    (None, [problem]) — an unknown state names 'to_state';
    a known but illegal transition names 'transition' and
    the caller also gets the from/to pair for the label."""
    if (
        not isinstance(to_state, str)
        or to_state.strip().upper() not in APPLICATION_STATES
    ):
        return None, ["to_state"]
    target = to_state.strip().upper()
    current = app["state"]
    if target not in TRANSITIONS[current]:
        return None, ["transition"]
    updated = {
        **app,
        "state": target,
        "events": app["events"] + [{
            "type": "state_changed",
            "from_state": current,
            "to_state": target,
            "actor": actor,
            "at": _now(),
        }],
        "messages": list(app["messages"]),
    }
    return updated, []


def add_message(
    app: dict[str, Any], author: Any, body: Any
) -> tuple[dict[str, Any] | None, list[str]]:
    """Append a message to the application's thread.
    Returns (updated, []) or (None, [field, ...])."""
    problems: list[str] = []
    if not isinstance(author, str) or not author.strip():
        problems.append("author")
    if not isinstance(body, str) or not body.strip():
        problems.append("body")
    if problems:
        return None, problems
    message = {
        "author": author.strip(),
        "body": body.strip(),
        "at": _now(),
    }
    updated = {
        **app,
        "events": list(app["events"]),
        "messages": app["messages"] + [message],
    }
    return updated, []


# --- Append-only JSONL record (event-sourced fold) ---


def _applications_path() -> Path:
    return Path(
        os.environ.get(
            "TALENT_APPLICATIONS_PATH",
            "./data/talent-applications.jsonl",
        )
    )


def _append_record(record: dict[str, Any]) -> None:
    path = _applications_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def record_application(app: dict[str, Any]) -> None:
    """Persist a newly created application."""
    _append_record({
        "type": "application",
        "application": app,
    })


def record_transition(app: dict[str, Any], event: dict[str, Any]) -> None:
    """Persist one state change as an event record."""
    _append_record({
        "type": "transition",
        "application_id": app["application_id"],
        "state": app["state"],
        "event": event,
    })


def record_message(app: dict[str, Any], message: dict[str, Any]) -> None:
    """Persist one thread message."""
    _append_record({
        "type": "message",
        "application_id": app["application_id"],
        "message": message,
    })


def load_application(
    application_id: str,
) -> dict[str, Any] | None:
    """Fold the append-only record for one application into
    its current view: state, full event stream, message
    thread — the two-way view, one record. None when the
    application does not exist."""
    path = _applications_path()
    if not path.exists():
        return None
    app: dict[str, Any] | None = None
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("type") == "application":
                candidate = record["application"]
                if candidate["application_id"] == application_id:
                    app = candidate
            elif app is not None and (
                record.get("application_id") == application_id
            ):
                if record["type"] == "transition":
                    app["state"] = record["state"]
                    app["events"].append(record["event"])
                elif record["type"] == "message":
                    app["messages"].append(record["message"])
    return app


# --- Assessment records ---


def _assessments_path() -> Path:
    return Path(
        os.environ.get(
            "TALENT_ASSESSMENTS_PATH",
            "./data/talent-assessments.jsonl",
        )
    )


def record_assessment(
    profile_name: str, assessment: dict[str, Any]
) -> dict[str, Any]:
    """Append one validated assessment record against a
    named profile (spec §2.3)."""
    record = {
        "profile_name": profile_name,
        "assessment": assessment,
        "recorded_at": _now(),
    }
    path = _assessments_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    return record


# --- The intents solver ---


def load_profiles() -> list[dict[str, Any]]:
    """The recorded TalentProfiles — the solver's supply.
    Reads the same v1 JSONL store the gateway writes."""
    path = talent_profile._store_path()
    if not path.exists():
        return []
    profiles: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                profiles.append(json.loads(line)["profile"])
    return profiles


def solve_intent(
    need: dict[str, Any], profiles: list[dict[str, Any]]
) -> dict[str, Any]:
    """Answer one role-requirement intent (spec §5). The
    intent is the need; the offers are the scorecard-ranked
    candidate supply; the routing (native vs
    affiliate-expert) and the NEAR AI honesty label ride in
    band. Settlement of a chosen offer is the placement
    record: an application advanced to ACCEPTED."""
    result = talent_profile.scorecard_matches(need, profiles)
    return {
        "intent": {"kind": "ROLE_REQUIREMENT", "need": need},
        "solver": SOLVER_NAME,
        "inference": dict(NEAR_AI_INFERENCE_STATE),
        "status": result["status"],
        "category": result["category"],
        "category_class": result["category_class"],
        "routing": result["routing"],
        "route_reason": result["route_reason"],
        "offers": result["matches"],
    }
