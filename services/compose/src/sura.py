"""SURA — agentic guidance over the Talent marketplace
(spec, 2026-11-17: docs/specifications/
sura-agentic-guidance-v1.md).

SURA (S-U-R-A, an acronym from the Assurative word family)
is built from the Assurative V2 core, like everything in
this service. It is the guidance layer over the Talent
marketplace, modelled clean-room on Saral AI's publicly
observable behaviour — outbound sourcing of passive
candidates from public signals, a fit score, a
switch-likelihood estimate — re-implemented as our own
objects, our own arithmetic, our own copy. No Saral code,
data, or scoring internals are used.

Three things live here:

1. The sourced feed (spec §3): profiles supplied through
   an explicit feed surface, with provenance REQUIRED,
   ingested as TalentProfiles with provenance marked, and
   persisted to an append-only JSONL store (env
   TALENT_SOURCED_PATH). Sourced candidates enter the same
   solver pool as applied candidates and are treated
   identically by the matcher and the scorecard.

2. The scores (spec §3.4–§3.5): a fit score per
   (need, profile) and a switch-likelihood per profile —
   deterministic heuristics over DECLARED fields and
   SUPPLIED signals only, bounded 0–100, with their full
   component breakdown returned alongside. Labelled
   heuristic v1; they are arithmetic, not a learned model.

3. Guidance (spec §2): a demand guidance object for the
   employer side (human or agentic) and a supply guidance
   object for the candidate side — roles defined by skill
   and by geo-requirement (remote / hybrid / onsite).

HONESTY (standing, spec §6): SURA v1 does NOT scrape
GitHub, LinkedIn, X, Stack Overflow, or any other source,
and nothing here claims it does. Signals are values a
feed asserts; SURA computes over asserted values only.
A real signal connector is future work.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import talent_profile

# The public signal sources a feed may name (spec §3.1) —
# the sources Saral's public pages name, plus the generic
# feed values. Naming a source is a provenance claim by
# the feed, not a claim that SURA reads that source.
SIGNAL_SOURCES: tuple[str, ...] = (
    "github",
    "linkedin",
    "x",
    "stack_overflow",
    "behance",
    "web",
    "partner_feed",
    "manual",
)
PROVENANCE_FIELDS: tuple[str, ...] = (
    "source",
    "source_ref",
    "feed",
    "sourced_at",
    "basis",
)
_NUMERIC_SIGNALS: tuple[str, ...] = (
    "last_activity_days",
    "activity_events_90d",
    "career_moves_5y",
    "years_in_current_role",
)
SIGNAL_FIELDS: tuple[str, ...] = _NUMERIC_SIGNALS + ("open_to_work",)

GEO_MODES: tuple[str, ...] = talent_profile.WORK_MODES

# The stored canonical is ON_SITE (the platform work-mode
# enum); "ONSITE" — the natural spelling on employer- and
# candidate-facing inputs — is accepted at the SURA
# boundary and normalized to it (spec §3.3).
_GEO_ALIASES: dict[str, str] = {"ONSITE": "ON_SITE"}


def _canon_geo(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    mode = value.strip().upper()
    mode = _GEO_ALIASES.get(mode, mode)
    return mode if mode in GEO_MODES else None

FIT_HEURISTIC = "sura_fit_heuristic_v1"
SWITCH_HEURISTIC = "sura_switch_heuristic_v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# --- Feed record validation (spec §3.1) ---


def validate_provenance(
    data: Any,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate one provenance object. Provenance is
    REQUIRED for sourced supply — there is no anonymous
    sourced candidate. Returns (normalized, []) or
    (None, [field, ...])."""
    if not isinstance(data, dict):
        return None, list(PROVENANCE_FIELDS)
    problems: list[str] = []
    source = data.get("source")
    if (
        not isinstance(source, str)
        or source.strip().lower() not in SIGNAL_SOURCES
    ):
        problems.append("source")
    for field in ("source_ref", "feed", "sourced_at", "basis"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(field)
    if problems:
        return None, problems
    return (
        {
            "source": source.strip().lower(),
            "source_ref": data["source_ref"].strip(),
            "feed": data["feed"].strip(),
            "sourced_at": data["sourced_at"].strip(),
            "basis": data["basis"].strip(),
        },
        [],
    )


def validate_signals(
    data: Any,
) -> tuple[dict[str, Any], list[str]]:
    """Validate the optional supplied-signals object.
    Signals are values the feed asserts about public
    activity; every field is optional, strict-when-present.
    Returns (normalized, [field, ...]) — the normalized
    dict carries only the fields actually supplied."""
    if data is None:
        return {}, []
    if not isinstance(data, dict):
        return {}, list(SIGNAL_FIELDS)
    problems: list[str] = []
    out: dict[str, Any] = {}
    for field in _NUMERIC_SIGNALS:
        value = data.get(field)
        if value is not None:
            if not _is_number(value) or value < 0:
                problems.append(field)
            else:
                out[field] = value
    openness = data.get("open_to_work")
    if openness is not None:
        if not isinstance(openness, bool):
            problems.append("open_to_work")
        else:
            out["open_to_work"] = openness
    return out, problems


def validate_geo_availability(
    data: Any,
) -> tuple[list[str], list[str]]:
    """Validate the optional geo_availability list: the
    work modes a candidate accepts (REMOTE / HYBRID /
    ON_SITE), normalized canonical, order preserved."""
    if data is None:
        return [], []
    if not isinstance(data, list) or not all(
        _canon_geo(m) is not None for m in data
    ):
        return [], ["geo_availability"]
    out: list[str] = []
    for m in data:
        mode = _canon_geo(m)
        if mode is not None and mode not in out:
            out.append(mode)
    return out, []


def validate_feed_record(
    data: Any,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate one sourced feed record (spec §3.1): a
    TalentProfile + REQUIRED provenance + optional signals
    and geo availability. Returns (record, []) or
    (None, [field, ...]) with nested problems prefixed
    (profile.*, provenance.*, signals.*). The record's
    profile carries the provenance, signals, geo
    availability, and computed switch-likelihood as
    annotations, so it enters the solver pool marked."""
    if not isinstance(data, dict):
        return None, [
            "profile", "provenance",
        ]
    problems: list[str] = []
    profile, pproblems = talent_profile.validate_profile(
        data.get("profile")
    )
    problems += [f"profile.{p}" for p in pproblems]
    provenance, vproblems = validate_provenance(
        data.get("provenance")
    )
    problems += [f"provenance.{p}" for p in vproblems]
    signals, sproblems = validate_signals(data.get("signals"))
    problems += [f"signals.{p}" for p in sproblems]
    geo, gproblems = validate_geo_availability(
        data.get("geo_availability")
    )
    problems += gproblems
    if problems:
        return None, problems
    switch = switch_likelihood(signals)
    annotated = {
        **profile,
        "provenance": provenance,
        "signals": signals,
        "geo_availability": geo,
        "sura": {"switch_likelihood": switch},
    }
    return (
        {
            "profile": annotated,
            "provenance": provenance,
            "signals": signals,
            "geo_availability": geo,
            "switch_likelihood": switch,
        },
        [],
    )


# --- The sourced store (append-only JSONL, spec §3.2) ---


def _sourced_path() -> Path:
    return Path(
        os.environ.get(
            "TALENT_SOURCED_PATH",
            "./data/talent-sourced.jsonl",
        )
    )


def record_sourced(record: dict[str, Any]) -> dict[str, Any]:
    """Append one validated feed record to the sourced
    store — the feed's audit record."""
    entry = {
        "type": "sourced_profile",
        "received_at": _now(),
        "feed": record["provenance"]["feed"],
        "record": record,
    }
    path = _sourced_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def load_sourced_profiles() -> list[dict[str, Any]]:
    """The sourced supply: every ingested profile, with
    its provenance, signals, and switch-likelihood
    annotations — ready to join the solver pool."""
    path = _sourced_path()
    if not path.exists():
        return []
    profiles: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                profiles.append(json.loads(line)["record"]["profile"])
    return profiles


def is_sourced(profile: dict[str, Any]) -> bool:
    return isinstance(profile.get("provenance"), dict)


# --- Geo semantics (spec §3.3) ---


def candidate_availability(
    profile: dict[str, Any],
) -> list[str] | None:
    """The work modes a candidate accepts: their declared
    geo_availability, else their employee work_mode as a
    singleton, else None (undeclared = unconstrained)."""
    geo = profile.get("geo_availability")
    if isinstance(geo, list) and geo:
        return list(geo)
    mode = profile.get("work_mode")
    if isinstance(mode, str) and mode in GEO_MODES:
        return [mode]
    return None


def need_geo_requirement(need: dict[str, Any]) -> str | None:
    return _canon_geo((need or {}).get("geo_requirement"))


def geo_qualified(
    need: dict[str, Any], profile: dict[str, Any]
) -> bool:
    """Geo-qualified when the role's geo-requirement is in
    the candidate's availability — or when either side is
    undeclared (spec §3.3)."""
    requirement = need_geo_requirement(need)
    if requirement is None:
        return True
    availability = candidate_availability(profile)
    if availability is None:
        return True
    return requirement in availability


# --- Switch-likelihood (spec §3.5, heuristic v1) ---


def _band(value: float, bands: tuple) -> float:
    for earned, test in bands:
        if test(value):
            return earned
    return 0


def switch_likelihood(signals: dict[str, Any] | None) -> dict[str, Any]:
    """Switch-likelihood, 0–100, from SUPPLIED signals
    only. Deterministic bands (spec §3.5); a missing signal
    contributes 0 and is named in the breakdown — the score
    never invents a signal."""
    signals = signals or {}
    components: dict[str, Any] = {}
    missing: list[str] = []
    total = 0.0

    tenure = signals.get("years_in_current_role")
    if tenure is None:
        missing.append("years_in_current_role")
        components["tenure_pressure"] = None
    else:
        earned = _band(tenure, (
            (30, lambda v: 2 <= v <= 4),
            (22, lambda v: 1 <= v < 2),
            (18, lambda v: 4 < v <= 6),
            (10, lambda v: v < 1),
            (8, lambda v: v > 6),
        ))
        components["tenure_pressure"] = earned
        total += earned

    moves = signals.get("career_moves_5y")
    if moves is None:
        missing.append("career_moves_5y")
        components["mobility_history"] = None
    else:
        earned = _band(moves, (
            (25, lambda v: v == 2),
            (15, lambda v: v == 1 or v >= 3),
            (5, lambda v: v == 0),
        ))
        components["mobility_history"] = earned
        total += earned

    activity = signals.get("activity_events_90d")
    if activity is None:
        missing.append("activity_events_90d")
        components["public_activity"] = None
    else:
        earned = _band(activity, (
            (25, lambda v: v >= 40),
            (18, lambda v: v >= 15),
            (10, lambda v: v >= 5),
            (5, lambda v: v >= 1),
            (0, lambda v: v == 0),
        ))
        components["public_activity"] = earned
        total += earned

    recency = signals.get("last_activity_days")
    if recency is None:
        missing.append("last_activity_days")
        components["activity_recency"] = None
    else:
        earned = _band(recency, (
            (20, lambda v: v <= 14),
            (12, lambda v: v <= 45),
            (6, lambda v: v <= 120),
            (0, lambda v: v > 120),
        ))
        components["activity_recency"] = earned
        total += earned

    openness = signals.get("open_to_work")
    if openness is None:
        missing.append("open_to_work")
        components["declared_openness"] = None
    else:
        earned = 10 if openness else 0
        components["declared_openness"] = earned
        total += earned

    return {
        "score": int(min(100, round(total))),
        "heuristic": SWITCH_HEURISTIC,
        "components": components,
        "basis": [f for f in SIGNAL_FIELDS if f not in missing],
        "missing_signals": missing,
    }


def profile_switch_likelihood(
    profile: dict[str, Any],
) -> dict[str, Any] | None:
    """The switch-likelihood for a pool profile: the score
    computed at ingestion when SURA annotations ride on
    the profile; recomputed from supplied signals when a
    profile carries signals without annotations; None when
    the profile carries no signals at all (an applied
    profile SURA has no signal basis for — never faked)."""
    sura_block = profile.get("sura")
    if isinstance(sura_block, dict) and isinstance(
        sura_block.get("switch_likelihood"), dict
    ):
        return sura_block["switch_likelihood"]
    signals = profile.get("signals")
    if isinstance(signals, dict) and signals:
        return switch_likelihood(signals)
    return None


# --- Fit score (spec §3.4, heuristic v1) ---


def _skill_tokens(values: Any) -> set[str]:
    out: set[str] = set()
    for v in values or []:
        if isinstance(v, str) and v.strip():
            out.add(v.strip().lower())
    return out


def fit_score(
    need: dict[str, Any], profile: dict[str, Any]
) -> dict[str, Any]:
    """Fit of one profile to one need, 0–100: the weighted
    composite of the components whose basis is declared
    (spec §3.4), renormalized over the available weight.
    Deterministic — same inputs, same score, always."""
    components: dict[str, Any] = {}
    earned_total = 0.0
    available_total = 0.0

    # Skill coverage (max 50).
    required = _skill_tokens((need or {}).get("skills"))
    covered: set[str] = set()
    missing: list[str] = []
    if required:
        have = _skill_tokens(profile.get("skills"))
        assessment = profile.get("assessment")
        if isinstance(assessment, dict):
            have |= _skill_tokens(assessment.get("skills_proven"))
        covered = required & have
        missing = sorted(required - have)
        earned = 50.0 * len(covered) / len(required)
        components["skill_coverage"] = {
            "earned": round(earned, 2), "available": 50,
        }
        earned_total += earned
        available_total += 50

    # Role match (max 20) — always has a basis.
    if talent_profile.match_profiles(need, [profile]):
        role_earned = 20.0
    elif talent_profile.role_family(profile) == (
        (need or {}).get("role_family", "operations")
    ):
        role_earned = 10.0
    else:
        role_earned = 0.0
    components["role_match"] = {
        "earned": role_earned, "available": 20,
    }
    earned_total += role_earned
    available_total += 20

    # Geo fit (max 20) — only when both sides declare.
    requirement = need_geo_requirement(need)
    availability = candidate_availability(profile)
    if requirement is not None and availability is not None:
        geo_earned = 20.0 if requirement in availability else 0.0
        components["geo_fit"] = {
            "earned": geo_earned, "available": 20,
        }
        earned_total += geo_earned
        available_total += 20

    # Experience fit (max 10).
    minimum = (need or {}).get("min_experience_years")
    if _is_number(minimum) and minimum >= 0:
        years = profile.get("experience_years")
        if _is_number(years):
            exp_earned = (
                10.0 if minimum == 0
                else 10.0 * min(years / minimum, 1.0)
            )
            components["experience_fit"] = {
                "earned": round(exp_earned, 2), "available": 10,
            }
            earned_total += exp_earned
            available_total += 10

    # Assessment evidence (max 10).
    assessment = profile.get("assessment")
    if isinstance(assessment, dict) and _is_number(
        assessment.get("score")
    ):
        assess_earned = assessment["score"] / 10.0
        components["assessment_evidence"] = {
            "earned": round(assess_earned, 2), "available": 10,
        }
        earned_total += assess_earned
        available_total += 10

    score = (
        int(round(100 * earned_total / available_total))
        if available_total else 0
    )
    return {
        "score": max(0, min(100, score)),
        "heuristic": FIT_HEURISTIC,
        "components": components,
        "skills_covered": sorted(covered),
        "skills_missing": missing,
    }


# --- Guidance (spec §2) ---


def _candidate_entry(
    need: dict[str, Any], profile: dict[str, Any]
) -> dict[str, Any]:
    assessment = profile.get("assessment")
    return {
        "name": profile.get("name"),
        "role": profile.get("role"),
        "sourced": is_sourced(profile),
        "provenance": profile.get("provenance"),
        "fit": fit_score(need, profile),
        "switch_likelihood": profile_switch_likelihood(profile),
        "assessment_score": (
            assessment.get("score")
            if isinstance(assessment, dict) else None
        ),
        "segment": talent_profile.experience_segment(profile),
        "segment_route": talent_profile.segment_route(need, profile),
        "geo_availability": candidate_availability(profile),
    }


def demand_guidance(
    need: dict[str, Any], profiles: list[dict[str, Any]]
) -> dict[str, Any]:
    """Demand guidance (spec §2.1): for one employer need,
    the category route, the pool's real state (applied vs
    sourced, fit distribution), the fit-ranked candidates
    with provenance where sourced, and recommendations
    derived deterministically from that state."""
    route = talent_profile.route_category(
        (need or {}).get("opportunity_category")
    )
    base = {
        "kind": "DEMAND_GUIDANCE",
        "guidance": "SURA",
        "need": need,
        **route,
    }
    if route["routing"] == "affiliate_expert":
        return {
            **base,
            "status": "routed_to_affiliate_expert",
            "pool": {
                "total": 0, "applied": 0, "sourced": 0,
                "fit_distribution": {
                    "80_plus": 0, "60_79": 0,
                    "40_59": 0, "below_40": 0,
                },
            },
            "candidates": [],
            "recommendations": [
                "This category is not built natively — route "
                "it through a placement agreement to an expert "
                "contractor-affiliate, case by case."
            ],
        }
    entries = [_candidate_entry(need, p) for p in profiles]
    entries.sort(key=lambda e: -e["fit"]["score"])
    sourced_count = sum(1 for e in entries if e["sourced"])
    distribution = {"80_plus": 0, "60_79": 0, "40_59": 0, "below_40": 0}
    for e in entries:
        s = e["fit"]["score"]
        if s >= 80:
            distribution["80_plus"] += 1
        elif s >= 60:
            distribution["60_79"] += 1
        elif s >= 40:
            distribution["40_59"] += 1
        else:
            distribution["below_40"] += 1
    recommendations: list[str] = []
    if not entries:
        recommendations.append(
            "No supply answers this need in the current pool "
            "— open the SURA sourced feed for this skill set, "
            "or widen the need (skills, geo-requirement)."
        )
    else:
        if len(entries) < 3:
            recommendations.append(
                f"Thin pool ({len(entries)} candidate(s)): "
                "consider widening the required skills or "
                "relaxing the geo-requirement before posting "
                "the intent."
            )
        if sourced_count == 0:
            recommendations.append(
                "All current supply is applied supply — no "
                "sourced candidates in the pool; the SURA "
                "feed is the gap for this need."
            )
        if all(
            e["segment_route"] == "intents_marketplace"
            for e in entries
        ):
            recommendations.append(
                "The supply for this need sits in the "
                "early-career segment — it is served by the "
                "intents marketplace, not the placement desk."
            )
        top = entries[0]["fit"]["score"]
        if top >= 80:
            recommendations.append(
                f"Strong fit available (top fit score {top}): "
                "the need can be posted as an intent against "
                "the current pool."
            )
    return {
        **base,
        "status": "guided" if entries else "no_supply",
        "pool": {
            "total": len(entries),
            "applied": len(entries) - sourced_count,
            "sourced": sourced_count,
            "fit_distribution": distribution,
        },
        "candidates": entries,
        "recommendations": recommendations,
    }


def supply_guidance(
    profile: dict[str, Any], needs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Supply guidance (spec §2.2): for one candidate, the
    open role listings they geo-qualify for, fit-ranked,
    each with its fit explanation — plus guidance notes
    derived from the profile's own state."""
    roles: list[dict[str, Any]] = []
    excluded = 0
    for need in needs or []:
        if not geo_qualified(need, profile):
            excluded += 1
            continue
        roles.append({
            "role": need.get("role"),
            "role_family": need.get("role_family", "operations"),
            "opportunity_category": need.get("opportunity_category"),
            "geo_requirement": need_geo_requirement(need),
            "fit": fit_score(need, profile),
            "segment_route": talent_profile.segment_route(
                need, profile
            ),
        })
    roles.sort(key=lambda r: -r["fit"]["score"])
    notes: list[str] = []
    if not isinstance(profile.get("assessment"), dict):
        notes.append(
            "No pre-assessment on file — the assessment is "
            "fit evidence: completing one adds the evidence "
            "component to your fit on every role."
        )
    if excluded:
        notes.append(
            f"Your declared geo availability excludes "
            f"{excluded} open role(s); widening availability "
            "would surface them."
        )
    if needs and not roles and excluded == len(needs):
        notes.append(
            "Every open role sits outside your geo "
            "availability."
        )
    if not needs:
        notes.append(
            "No open role listings were supplied to guide "
            "against."
        )
    return {
        "kind": "SUPPLY_GUIDANCE",
        "guidance": "SURA",
        "candidate": {
            "name": profile.get("name"),
            "role": profile.get("role"),
            "sourced": is_sourced(profile),
            "provenance": profile.get("provenance"),
            "geo_availability": candidate_availability(profile),
            "switch_likelihood": profile_switch_likelihood(profile),
        },
        "roles": roles,
        "excluded_by_geo": excluded,
        "notes": notes,
    }


# --- Guidance events: the RL talent environment's feed ---
#
# Spec §9.2: SURA's guidance is an RL workload of the
# uze-rl TALENT environment (one of five: underwrite /
# assign / auction / talent / whb). The monorepo side of
# that plane is the honest event feed — every guidance
# call is recorded in episode-ready form; the ATS
# lifecycle settles the outcome fields as real outcomes
# land. Training, benchmarking, and promotion live in
# uze-rl, never here. No trained policy exists yet; the
# incumbent guidance policy is the labelled heuristic v1
# of §3.4–§3.5, and it changes only through uze-rl's
# gated promotion — never by silent self-modification or
# ad-hoc weight tuning.

GUIDANCE_POLICY = FIT_HEURISTIC  # the incumbent, labelled


def _guidance_events_path() -> Path:
    return Path(
        os.environ.get(
            "TALENT_GUIDANCE_EVENTS_PATH",
            "./data/talent-guidance-events.jsonl",
        )
    )


def _append_guidance_record(record: dict[str, Any]) -> None:
    path = _guidance_events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def record_guidance_event(
    side: str,
    subject: str,
    context: dict[str, Any],
    guidance: dict[str, Any],
) -> dict[str, Any]:
    """Record one guidance call as an episode-ready event:
    the guidance given (side, subject, recommendations and
    scores), the context (role/candidate, required skills,
    geo-requirement), and the outcome fields — open at
    recording, settled later by the ATS lifecycle. This
    record is the feed the RL talent environment reads to
    build episodes."""
    event = {
        "event_id": "gev_" + uuid.uuid4().hex[:12],
        "recorded_at": _now(),
        "side": side,
        "subject": subject,
        "policy": GUIDANCE_POLICY,
        "context": context,
        "guidance": guidance,
        "outcome": {
            "status": "open",
            "matched": None,
            "placed": None,
            "accepted": None,
            "rejected": None,
            "application_ref": None,
            "settled_at": None,
        },
    }
    _append_guidance_record({
        "type": "guidance_event",
        "event": event,
    })
    return event


def record_guidance_outcome(
    event_id: str, outcome: dict[str, Any]
) -> None:
    """Append one outcome update for a guidance event —
    the fold in load_guidance_events applies updates in
    order, so the stored history stays append-only."""
    _append_guidance_record({
        "type": "guidance_outcome",
        "event_id": event_id,
        "outcome": outcome,
        "at": _now(),
    })


def load_guidance_events() -> list[dict[str, Any]]:
    """Fold the guidance-events record into episode-ready
    events: each event with its outcome fields as settled
    so far. This is the read the RL talent environment
    builds episodes from."""
    path = _guidance_events_path()
    if not path.exists():
        return []
    events: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("type") == "guidance_event":
                event = record["event"]
                events[event["event_id"]] = event
                order.append(event["event_id"])
            elif record.get("type") == "guidance_outcome":
                event = events.get(record["event_id"])
                if event is not None:
                    event["outcome"].update(record["outcome"])
    return [events[event_id] for event_id in order]


def _event_matches_application(
    event: dict[str, Any], app: dict[str, Any]
) -> bool:
    """The v1 linkage rule: a guidance event links to an
    application when the application's candidate reference
    names the event's candidate (its subject on the supply
    side, its top candidate on the demand side) and its
    role reference names the event's role."""
    profile_ref = app.get("profile_ref")
    role_ref = app.get("role_ref")
    context = event.get("context") or {}
    candidate_hit = profile_ref in (
        event.get("subject"), context.get("candidate"),
    )
    role_hit = role_ref in (
        event.get("subject"), context.get("role"),
    )
    return bool(candidate_hit and role_hit)


def _outcome_for_state(state: str) -> dict[str, Any]:
    """Map an application's lifecycle state onto a linked
    guidance event's outcome fields. ACCEPTED is the
    settlement point: placed and accepted settle True.
    REJECTED settles rejected True, placed False."""
    if state == "ACCEPTED":
        return {
            "status": "settled_accepted",
            "matched": True,
            "placed": True,
            "accepted": True,
            "rejected": False,
        }
    if state == "REJECTED":
        return {
            "status": "settled_rejected",
            "matched": True,
            "placed": False,
            "accepted": False,
            "rejected": True,
        }
    return {
        "status": "in_progress",
        "matched": True,
        "placed": None,
        "accepted": None,
        "rejected": None,
    }


def settle_outcomes_for_application(
    app: dict[str, Any],
) -> list[dict[str, Any]]:
    """Settle the outcome fields of every open guidance
    event linked to this application, from the
    application's current lifecycle state. Called by the
    ATS surface on application creation and on every
    transition; appends an outcome record only when a
    field actually changes. Returns the updated events."""
    updated: list[dict[str, Any]] = []
    for event in load_guidance_events():
        outcome = event["outcome"]
        if outcome.get("status", "").startswith("settled"):
            continue
        if outcome.get("application_ref") not in (
            None, app["application_id"],
        ):
            continue
        if outcome.get("application_ref") is None and not (
            _event_matches_application(event, app)
        ):
            continue
        target = _outcome_for_state(app["state"])
        target["application_ref"] = app["application_id"]
        if target["status"].startswith("settled"):
            target["settled_at"] = _now()
        changed = {
            k: v for k, v in target.items()
            if outcome.get(k) != v
        }
        if changed:
            record_guidance_outcome(event["event_id"], changed)
            outcome.update(changed)
            updated.append(event)
    return updated
