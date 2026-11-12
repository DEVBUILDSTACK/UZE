"""TalentProfile — the single schema for talent ingestion
(owner tap, 2026-11-12: Master Directive Part 3).

Two doors, one schema: an agentic talent submits this JSON
directly; a human's PDF/Word resume will be structured into
the same shape by the deferred parsing layer (January 2nd —
see docs/specifications/talent-placement-parsing.md). Until
then the gateway accepts JSON only and says so cleanly.

Validation follows the platform discipline: a profile that
cannot be validated is refused with the exact field names
that are missing or invalid (INSUFFICIENT_DATA), never
completed by guessing.

Storage (honest scope): v1 persists validated profiles to an
append-only JSONL file (env TALENT_PROFILES_PATH, default
./data/talent-profiles.jsonl) — the same pattern as the alpha
intake; a database table is a later migration.
"""

from __future__ import annotations

import json
import os
import zipfile
import io
from pathlib import Path
from typing import Any

REQUIRED_FIELDS: tuple[str, ...] = (
    "name",
    "role",
    "experience_years",
    "skills",
    "expected_rate_usd",
)

# Talent taxonomy (owner tap, 2026-11-12): who the employer is
# and what the worker is are different axes. Both fields are
# OPTIONAL — profiles validated before the taxonomy existed
# stay valid — but when present they must be exact enum values
# (accepted case-insensitively, stored canonical).
ASSET_CLASS_FOCUS: tuple[str, ...] = ("HOSPITALITY", "RESIDENTIAL")
TALENT_TYPES: tuple[str, ...] = (
    "HUMAN_EMPLOYEE",
    "HUMAN_CONTRACTOR",
    "AGENTIC_SERVICE",
)

PDF_DEFERRAL_MESSAGE = (
    "PDF/Word resume parsing is deferred to our January 2nd "
    "update. Please provide your resume in JSON format."
)


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_profile(data: Any) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate a decoded JSON payload against TalentProfile.

    Returns (normalized_profile, []) on success, or
    (None, [field, ...]) naming every missing/invalid field.
    """
    if not isinstance(data, dict):
        return None, list(REQUIRED_FIELDS)
    problems: list[str] = []

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        problems.append("name")
    role = data.get("role")
    if not isinstance(role, str) or not role.strip():
        problems.append("role")
    exp = data.get("experience_years")
    if not _is_number(exp) or exp < 0:
        problems.append("experience_years")
    skills = data.get("skills")
    if (
        not isinstance(skills, list)
        or not skills
        or not all(isinstance(s, str) and s.strip() for s in skills)
    ):
        problems.append("skills")
    rate = data.get("expected_rate_usd")
    if not _is_number(rate) or rate <= 0:
        problems.append("expected_rate_usd")
    certs = data.get("certifications", [])
    if not isinstance(certs, list) or not all(
        isinstance(c, str) for c in certs
    ):
        problems.append("certifications")
    focus = data.get("asset_class_focus")
    if focus is not None and (
        not isinstance(focus, str)
        or focus.strip().upper() not in ASSET_CLASS_FOCUS
    ):
        problems.append("asset_class_focus")
    ttype = data.get("talent_type")
    if ttype is not None and (
        not isinstance(ttype, str)
        or ttype.strip().upper() not in TALENT_TYPES
    ):
        problems.append("talent_type")

    if problems:
        return None, problems
    return (
        {
            "name": name.strip(),
            "role": role.strip(),
            "experience_years": exp,
            "skills": [s.strip() for s in skills],
            "expected_rate_usd": rate,
            "certifications": list(certs),
            "asset_class_focus": (
                focus.strip().upper() if isinstance(focus, str) else None
            ),
            "talent_type": (
                ttype.strip().upper() if isinstance(ttype, str) else None
            ),
        },
        [],
    )


def _store_path() -> Path:
    return Path(
        os.environ.get("TALENT_PROFILES_PATH", "./data/talent-profiles.jsonl")
    )


def record_profile(profile: dict[str, Any], sender: str) -> None:
    """Append one validated profile to the v1 JSONL store."""
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps({"sender": sender, "profile": profile}) + "\n"
        )


def is_pdf(data: bytes) -> bool:
    return data[:4] == b"%PDF"


def is_docx(data: bytes) -> bool:
    if data[:4] != b"PK\x03\x04":
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return "word/document.xml" in zf.namelist()
    except Exception:
        return False


def derive_talent_placement(years: list[dict]) -> dict[str, Any]:
    """The B2B -> B2C bridge (Master Directive Part 2): from an
    underwrite's own line items, name the operational roles the
    asset's payroll already pays for, and point at Talent
    Placement. Roles are read from payroll/role line labels —
    never invented: no role lines, no requirement.
    """
    role_rules: tuple[tuple[str, str], ...] = (
        ("manager", "Property Manager"),
        ("maint", "Maintenance"),
        ("leasing", "Leasing Agent"),
        ("security", "Security"),
        ("housekeep", "Housekeeping"),
    )
    roles: list[str] = []
    payroll_total = 0.0
    for entry in years or []:
        for label, amount in (entry.get("line_items") or {}).items():
            low = str(label).lower()
            if "payroll" in low or "salary" in low or "wages" in low:
                try:
                    payroll_total += abs(float(amount))
                except (TypeError, ValueError):
                    pass
            for needle, role in role_rules:
                if needle in low and role not in roles:
                    roles.append(role)
    return {
        "required": bool(roles),
        "roles": roles,
        "payroll_budget_annual": round(payroll_total, 2) if payroll_total else None,
        "cta_url": "/talent/placement?source=underwrite",
        # Two paths (owner tap, 2026-11-12): Operations hires
        # the roles the payroll names; Knowledge Work is the
        # standing offer to outsource the asset's ongoing
        # financial analysis — to a human contractor or an
        # agentic service.
        "paths": [
            {
                "kind": "operations",
                "label": "Hire operational staff for this asset",
                "roles": roles,
                "cta_url": "/talent/placement?source=underwrite&path=operations",
            },
            {
                "kind": "knowledge_work",
                "label": "Outsource the ongoing Financial Analysis of this asset",
                "service": "Financial Analysis",
                "cta_url": "/talent/placement?source=underwrite&path=knowledge",
            },
        ],
    }


def role_family(profile: dict[str, Any]) -> str:
    """Which side of the marketplace a profile serves:
    'knowledge_work' for financial-analysis roles, else
    'operations'."""
    role = str(profile.get("role", "")).lower()
    if "analyst" in role or "financial analysis" in role:
        return "knowledge_work"
    return "operations"


def match_profiles(
    need: dict[str, Any], profiles: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """The matcher (mock logic, deterministic): a profile
    matches a need when the role family agrees, the role
    matches (for operations needs that name one), and the
    asset-class focus is compatible — a profile with no focus
    serves any focus; a need with no focus accepts any.
    Input order is preserved."""
    out: list[dict[str, Any]] = []
    want_family = need.get("role_family", "operations")
    want_role = str(need.get("role", "")).lower().strip()
    want_focus = need.get("asset_class_focus")
    for p in profiles:
        if role_family(p) != want_family:
            continue
        if want_role:
            have_role = str(p.get("role", "")).lower()
            if want_role not in have_role and have_role not in want_role:
                continue
        p_focus = p.get("asset_class_focus")
        if want_focus and p_focus and p_focus != want_focus:
            continue
        out.append(p)
    return out
