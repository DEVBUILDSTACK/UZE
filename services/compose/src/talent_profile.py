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

# Development, Design & Wellness taxonomy (owner tap,
# 2026-11-13 — standby + hackathon scope override, James's own
# words). The D (Development) side of the marketplace connects
# to H&I (Hospitality & Income): a developer who secures land
# and builds needs the project team that turns it into a
# hospitality asset. `role` stays FREE TEXT — a closed role
# enum would break every profile validated before this
# taxonomy existed. Instead, two OPTIONAL fields carry the
# taxonomy, strict-when-present like the fields above:
# `role_category` (what the profile does on a project) and
# `domain_focus` (the design domain it serves). Neither
# replaces asset_class_focus — that axis still says which
# asset class the employer runs.
DEV_DESIGN_CATEGORIES: tuple[str, ...] = (
    "ARCHITECT",
    "INTERIOR_DESIGNER",
    "LIGHTING_TECHNOLOGY_INTEGRATOR",
    "WELLNESS_SPA_CONSULTANT",
    "CAD_DRAFTER",
    "PRE_SALES_BROKER",
)
# Project Side categories (owner tap, 2026-11-13): the
# execution roles of a development — where money meets the
# build.
PROJECT_SIDE_CATEGORIES: tuple[str, ...] = (
    "DEVELOPMENT_MANAGER",
    "GENERAL_CONTRACTOR",
    "CONSTRUCTION_PROJECT_MANAGER",
    "ENTITLEMENT_CONSULTANT",
    "DEVELOPMENT_FINANCE_ANALYST",
)
# Embedded-expertise categories (owner tap, 2026-11-13):
# traditional software and creative-intelligence capabilities
# carried invisibly in the taxonomy — no firm or affiliate
# name attaches to them on any surface.
SOFTWARE_CATEGORIES: tuple[str, ...] = (
    "GRAPHIC_DESIGNER",
    "WEB_DEVELOPER",
    "SOFTWARE_ENGINEER",
)
CREATIVE_CATEGORIES: tuple[str, ...] = (
    "ANIMATOR",
    "DRONE_OPERATOR",
    "FINE_ARTIST",
    "CREATIVE_INTELLIGENCE_ADVISOR",
    "FILMMAKER",
)
ROLE_CATEGORIES: tuple[str, ...] = (
    DEV_DESIGN_CATEGORIES
    + PROJECT_SIDE_CATEGORIES
    + SOFTWARE_CATEGORIES
    + CREATIVE_CATEGORIES
)
DOMAIN_FOCUS: tuple[str, ...] = (
    "COMMERCIAL_ARCHITECTURE",
    "LUXURY_RESIDENTIAL",
    "HOSPITALITY_RESORT_DESIGN",
    "WELLNESS_INFRASTRUCTURE",
    "TRADITIONAL_SOFTWARE_STACK",
    "VISUAL_ASSETS",
    "PROJECT_INCUBATION",
)
# The project lifecycle axis (owner tap, 2026-11-13): which
# phase of a development a profile serves. Optional,
# strict-when-present, like every taxonomy field here.
PROJECT_LIFECYCLE_STAGES: tuple[str, ...] = (
    "ACQUISITION_ENTITLEMENT",
    "DESIGN_ARCHITECTURE",
    "CONSTRUCTION_EXECUTION",
    "OPERATIONS_STABILIZATION",
)
PROJECT_SIDE_ROLES: tuple[tuple[str, str], ...] = (
    ("DEVELOPMENT_MANAGER", "Development Manager"),
    ("GENERAL_CONTRACTOR", "General Contractor"),
    ("CONSTRUCTION_PROJECT_MANAGER", "Construction Project Manager"),
    ("ENTITLEMENT_CONSULTANT", "Entitlement Consultant"),
    ("DEVELOPMENT_FINANCE_ANALYST", "Development Finance Analyst"),
)
# The standing project team a development routes to, by
# category: display names for surfaces, categories for code.
PROJECT_TEAM_ROLES: tuple[tuple[str, str], ...] = (
    ("ARCHITECT", "Architect"),
    ("INTERIOR_DESIGNER", "Interior Designer"),
    ("LIGHTING_TECHNOLOGY_INTEGRATOR", "Lighting Technology Integrator"),
    ("WELLNESS_SPA_CONSULTANT", "Wellness Spa Consultant"),
    ("CAD_DRAFTER", "CAD Drafter"),
    ("PRE_SALES_BROKER", "Pre-Sales Broker"),
)

# Stage routing (owner tap, 2026-11-13): when a project
# context is DECLARED — lifecycle stage, domain focus,
# asset-class focus — the development path names the
# categories that stage requires, instead of the generic
# standing list. Rules over declared inputs only: nothing
# about a development team is inferred from an asset's
# financials.
STAGE_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "ACQUISITION_ENTITLEMENT": (
        "ENTITLEMENT_CONSULTANT",
        "DEVELOPMENT_FINANCE_ANALYST",
        "DEVELOPMENT_MANAGER",
    ),
    "DESIGN_ARCHITECTURE": (
        "ARCHITECT",
        "INTERIOR_DESIGNER",
        "LIGHTING_TECHNOLOGY_INTEGRATOR",
        "CAD_DRAFTER",
        "PRE_SALES_BROKER",
    ),
    "CONSTRUCTION_EXECUTION": (
        "GENERAL_CONTRACTOR",
        "CONSTRUCTION_PROJECT_MANAGER",
        "DEVELOPMENT_MANAGER",
    ),
    "OPERATIONS_STABILIZATION": (),
}
_WELLNESS_DOMAINS: tuple[str, ...] = (
    "HOSPITALITY_RESORT_DESIGN",
    "WELLNESS_INFRASTRUCTURE",
)
_CATEGORY_DISPLAY: dict[str, str] = dict(
    PROJECT_TEAM_ROLES + PROJECT_SIDE_ROLES
)


def development_requirements(
    context: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """The development categories a DECLARED project context
    requires, in team order. A resort/wellness design domain
    adds the wellness spa consultant at the design stage.
    No context (or an unrecognized stage) yields no
    requirements — the caller then falls back to the
    standing offer."""
    ctx = context or {}
    stage = str(ctx.get("project_lifecycle_stage") or "").upper()
    domain = str(ctx.get("domain_focus") or "").upper()
    focus = str(ctx.get("asset_class_focus") or "").upper()
    cats = list(STAGE_REQUIREMENTS.get(stage, ()))
    if stage == "DESIGN_ARCHITECTURE" and domain in _WELLNESS_DOMAINS:
        cats.insert(3, "WELLNESS_SPA_CONSULTANT")
    return [
        {
            "role_category": c,
            "role": _CATEGORY_DISPLAY.get(c, c),
            "domain_focus": domain or None,
            "asset_class_focus": focus or None,
            "project_lifecycle_stage": stage or None,
        }
        for c in cats
    ]


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
    category = data.get("role_category")
    if category is not None and (
        not isinstance(category, str)
        or category.strip().upper() not in ROLE_CATEGORIES
    ):
        problems.append("role_category")
    domain = data.get("domain_focus")
    if domain is not None and (
        not isinstance(domain, str)
        or domain.strip().upper() not in DOMAIN_FOCUS
    ):
        problems.append("domain_focus")
    stage = data.get("project_lifecycle_stage")
    if stage is not None and (
        not isinstance(stage, str)
        or stage.strip().upper() not in PROJECT_LIFECYCLE_STAGES
    ):
        problems.append("project_lifecycle_stage")

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
            "role_category": (
                category.strip().upper()
                if isinstance(category, str) else None
            ),
            "domain_focus": (
                domain.strip().upper()
                if isinstance(domain, str) else None
            ),
            "project_lifecycle_stage": (
                stage.strip().upper()
                if isinstance(stage, str) else None
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


def derive_talent_placement(
    years: list[dict], context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """The B2B -> B2C bridge (Master Directive Part 2): from an
    underwrite's own line items, name the operational roles the
    asset's payroll already pays for, and point at Talent
    Placement. Roles are read from payroll/role line labels —
    never invented: no role lines, no requirement.

    Development routing (owner tap, 2026-11-13): when the
    caller DECLARES a project context (lifecycle stage,
    domain focus, asset-class focus), the development path
    names the categories that stage requires
    (development_requirements); without a context it remains
    the standing offer. The context is declared input, never
    inferred from the financials.
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
    _dev_requirements = development_requirements(context)
    _stage = str(
        (context or {}).get("project_lifecycle_stage") or ""
    ).upper()
    _routed = _stage in STAGE_REQUIREMENTS
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
            {
                # Third path (owner tap, 2026-11-13): the
                # Development & Design offer — the project team
                # that turns a development into a hospitality
                # asset. Not a payroll derivation: with a
                # DECLARED project context it is context-routed
                # (the categories the declared stage requires);
                # without one it is the standing offer of the
                # platform's project team.
                "kind": "development_design",
                "label": "Assemble the Development & Design project team",
                "mode": (
                    "context_routed" if _routed else "standing_offer"
                ),
                "requirements": _dev_requirements,
                "roles": (
                    [r["role"] for r in _dev_requirements]
                    if _routed
                    else [d for _, d in PROJECT_TEAM_ROLES]
                ),
                "cta_url": "/talent/placement?source=underwrite&path=development",
            },
        ],
    }


def role_family(profile: dict[str, Any]) -> str:
    """Which side of the marketplace a profile serves, by
    declared role_category first, then by the role text:
    'knowledge_work' (financial analysis), 'development_design'
    (the D→H&I project team), 'project_side' (development
    execution roles), 'software_development' (traditional
    software stack), 'creative_services' (visual assets and
    creative intelligence), else 'operations'."""
    category = profile.get("role_category")
    if category in DEV_DESIGN_CATEGORIES:
        return "development_design"
    if category in PROJECT_SIDE_CATEGORIES:
        return "project_side"
    if category in SOFTWARE_CATEGORIES:
        return "software_development"
    if category in CREATIVE_CATEGORIES:
        return "creative_services"
    role = str(profile.get("role", "")).lower()
    if "analyst" in role or "financial analysis" in role:
        return "knowledge_work"
    for needle in (
        "architect", "interior", "lighting", "spa", "wellness",
        "cad drafter", "cad_drafter", "pre-sales", "pre sales",
    ):
        if needle in role:
            return "development_design"
    for needle in (
        "general contractor", "construction project manager",
        "development manager", "entitlement",
    ):
        if needle in role:
            return "project_side"
    for needle in (
        "web developer", "software engineer", "graphic design",
    ):
        if needle in role:
            return "software_development"
    for needle in ("animator", "drone", "filmmaker", "fine artist"):
        if needle in role:
            return "creative_services"
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
    want_domain = need.get("domain_focus")
    want_category = need.get("role_category")
    want_stage = need.get("project_lifecycle_stage")
    for p in profiles:
        if role_family(p) != want_family:
            continue
        if want_role:
            have_role = str(p.get("role", "")).lower()
            if want_role not in have_role and have_role not in want_role:
                continue
        if want_category and p.get("role_category") != want_category:
            continue
        p_focus = p.get("asset_class_focus")
        if want_focus and p_focus and p_focus != want_focus:
            continue
        # Domain compatibility follows the focus rule: a
        # profile with no domain serves any domain; a need
        # with no domain accepts any.
        p_domain = p.get("domain_focus")
        if want_domain and p_domain and p_domain != want_domain:
            continue
        # Lifecycle-stage compatibility follows the same
        # rule: a profile with no stage serves any stage.
        p_stage = p.get("project_lifecycle_stage")
        if want_stage and p_stage and p_stage != want_stage:
            continue
        out.append(p)
    return out


def assemble_project_team(
    need: dict[str, Any], profiles: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Assemble a Development & Design project team: for each
    standing role category, the profiles that match the need
    (family, asset-class focus, and domain all applied by the
    matcher). Categories with no match are omitted — the team
    shows what the marketplace can actually staff, never a
    padded roster. Keyed by role_category, in the standing
    PROJECT_TEAM_ROLES order."""
    team: dict[str, list[dict[str, Any]]] = {}
    for category, _display in PROJECT_TEAM_ROLES:
        hits = match_profiles(
            {**need, "role_family": "development_design",
             "role_category": category},
            profiles,
        )
        if hits:
            team[category] = hits
    return team


def assemble_project_side(
    need: dict[str, Any], profiles: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Assemble the Project Side roster for a development:
    for each execution role category, the profiles matching
    the need — including its project_lifecycle_stage, when
    the need names one. Same honesty rule as the project
    team: unstaffable categories are omitted, never padded."""
    roster: dict[str, list[dict[str, Any]]] = {}
    for category, _display in PROJECT_SIDE_ROLES:
        hits = match_profiles(
            {**need, "role_family": "project_side",
             "role_category": category},
            profiles,
        )
        if hits:
            roster[category] = hits
    return roster


def evaluate_project_bids(
    brief: str, budget_usd: Any, bids: Any
) -> tuple[dict[str, Any] | None, list[str]]:
    """The agentic bidding mock (owner tap, 2026-11-13):
    evaluate design bids against a stated development
    budget. This is a MOCK budget check only — bids are
    ranked by amount, flagged against the budget, and the
    lowest in-budget bid is named. It is NOT an underwrite:
    no yield-on-cost or development appraisal is computed,
    and nothing is awarded. Returns (evaluation, []) or
    (None, [problem, ...])."""
    problems: list[str] = []
    if not isinstance(brief, str) or not brief.strip():
        problems.append("brief")
    if (
        not isinstance(budget_usd, (int, float))
        or isinstance(budget_usd, bool) or budget_usd <= 0
    ):
        problems.append("budget_usd")
    clean: list[dict[str, Any]] = []
    if not isinstance(bids, list) or not bids:
        problems.append("bids")
    else:
        for i, b in enumerate(bids):
            if not isinstance(b, dict):
                problems.append(f"bids[{i}]")
                continue
            bidder = b.get("bidder")
            amount = b.get("amount_usd")
            category = b.get("role_category")
            ok = True
            if not isinstance(bidder, str) or not bidder.strip():
                problems.append(f"bids[{i}].bidder")
                ok = False
            if (
                not isinstance(amount, (int, float))
                or isinstance(amount, bool) or amount <= 0
            ):
                problems.append(f"bids[{i}].amount_usd")
                ok = False
            if category is not None and (
                not isinstance(category, str)
                or category.strip().upper() not in ROLE_CATEGORIES
            ):
                problems.append(f"bids[{i}].role_category")
                ok = False
            if ok:
                clean.append({
                    "bidder": bidder.strip(),
                    "amount_usd": amount,
                    "role_category": (
                        category.strip().upper()
                        if isinstance(category, str) else None
                    ),
                })
    if problems:
        return None, problems
    ranked = sorted(clean, key=lambda b: b["amount_usd"])
    for b in ranked:
        b["within_budget"] = b["amount_usd"] <= budget_usd
    recommended = next(
        (b["bidder"] for b in ranked if b["within_budget"]), None
    )
    return (
        {
            "status": "mock_recorded",
            "mock": True,
            "brief": brief.strip(),
            "budget_usd": budget_usd,
            "ranked_bids": ranked,
            "recommended_bidder": recommended,
            "evaluation_basis": (
                "mock budget check only — ranked by amount "
                "against the stated budget; not an underwrite, "
                "no yield-on-cost calculation, nothing awarded"
            ),
        },
        [],
    )


# --- Referral edges (v1, mock storage) ---
#
# The dual-plane referral: a hired project member refers the
# next one — the Architect refers the Interior Designer, who
# refers the Spa Consultant. An edge is a record, not a
# payout: economics and standing-confirmation are the
# strategic audit's later sequencing, not this build. Storage
# follows the profiles pattern — append-only JSONL (env
# TALENT_REFERRALS_PATH); a database table is a later
# migration.

REFERRAL_FIELDS: tuple[str, ...] = (
    "referrer_name",
    "referred_name",
)


def validate_referral(data: Any) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate one referral edge. Returns (edge, []) or
    (None, [field, ...]) naming every missing/invalid field.
    A self-referral names 'referred_name' as the problem."""
    if not isinstance(data, dict):
        return None, list(REFERRAL_FIELDS)
    problems: list[str] = []
    referrer = data.get("referrer_name")
    if not isinstance(referrer, str) or not referrer.strip():
        problems.append("referrer_name")
    referred = data.get("referred_name")
    if not isinstance(referred, str) or not referred.strip():
        problems.append("referred_name")
    if (
        isinstance(referrer, str) and isinstance(referred, str)
        and referrer.strip() and referred.strip()
        and referrer.strip().lower() == referred.strip().lower()
    ):
        problems.append("referred_name")
    category = data.get("referred_role_category")
    if category is not None and (
        not isinstance(category, str)
        or category.strip().upper() not in ROLE_CATEGORIES
    ):
        problems.append("referred_role_category")
    context_ref = data.get("context_ref")
    if context_ref is not None and not isinstance(context_ref, str):
        problems.append("context_ref")
    if problems:
        return None, problems
    return (
        {
            "referrer_name": referrer.strip(),
            "referred_name": referred.strip(),
            "referred_role_category": (
                category.strip().upper()
                if isinstance(category, str) else None
            ),
            "context_ref": context_ref,
        },
        [],
    )


def _referrals_path() -> Path:
    return Path(
        os.environ.get(
            "TALENT_REFERRALS_PATH", "./data/talent-referrals.jsonl"
        )
    )


def record_referral(edge: dict[str, Any]) -> None:
    """Append one validated referral edge to the v1 store."""
    path = _referrals_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"edge": edge}) + "\n")


def referral_chain(
    edges: list[dict[str, Any]], start_name: str
) -> list[str]:
    """Walk a referral chain from a starting name: the names
    in referral order, following each person's outgoing edge
    (first edge wins), stopping at the end of the chain or
    before a repeat. The start name is not included."""
    by_referrer: dict[str, str] = {}
    for e in edges:
        by_referrer.setdefault(
            str(e.get("referrer_name", "")).lower(),
            str(e.get("referred_name", "")),
        )
    chain: list[str] = []
    seen = {start_name.lower()}
    current = start_name
    while True:
        nxt = by_referrer.get(current.lower())
        if not nxt or nxt.lower() in seen:
            return chain
        chain.append(nxt)
        seen.add(nxt.lower())
        current = nxt
