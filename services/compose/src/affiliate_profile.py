"""AffiliateProfile — affiliate onboarding (owner tap,
2026-11-13: "integration of affiliates as their onboarding
at Hack launch").

An affiliate onboards by declaring what it supplies: creative
services, software development, and a portfolio. There is no
Entity or Affiliate database table in this codebase — the
relay directives that presupposed one were corrected on the
record — so onboarding follows the platform's v1 pattern
(same as TalentProfile and the alpha intake): a validated
schema module with an append-only JSONL store, and a database
table as a later migration.

Positioning (owner correction, 2026-11-13): capabilities are
embedded invisibly. No affiliate name is badged or featured
on public surfaces by this module; the one ordering signal,
sponsorship_status, only orders the affiliate directory —
and says so.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

VISUALIZATION_TYPES: tuple[str, ...] = (
    "DRONE",
    "MOTION_GRAPHICS",
    "3D_RENDER",
)
APP_TYPES: tuple[str, ...] = (
    "BOOKING_ENGINE",
    "TENANT_PORTAL",
    "CRM_FRONTEND",
    "PROPERTY_DASHBOARD",
)

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


def _str_list(v: Any) -> bool:
    return isinstance(v, list) and all(
        isinstance(s, str) and s.strip() for s in v
    )


def _enum_list(v: Any, allowed: tuple[str, ...]) -> list[str] | None:
    if not isinstance(v, list) or not v:
        return None
    out = []
    for s in v:
        if not isinstance(s, str) or s.strip().upper() not in allowed:
            return None
        out.append(s.strip().upper())
    return out


def validate_affiliate_profile(
    data: Any,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate one affiliate onboarding payload. Returns
    (normalized_profile, []) or (None, [field, ...]) naming
    every missing/invalid field by path — the platform
    discipline: refuse and name, never guess."""
    if not isinstance(data, dict):
        return None, ["name", "slug"]
    problems: list[str] = []

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        problems.append("name")
    slug = data.get("slug")
    if slug is None and isinstance(name, str) and name.strip():
        slug = slugify(name)
    if not isinstance(slug, str) or not _SLUG_RE.match(slug or ""):
        problems.append("slug")

    creative = data.get("creative_services")
    creative_out = None
    if creative is not None:
        if not isinstance(creative, dict):
            problems.append("creative_services")
        else:
            viz = _enum_list(
                creative.get("visualization"), VISUALIZATION_TYPES
            )
            if viz is None:
                problems.append("creative_services.visualization")
            else:
                creative_out = {"visualization": viz}

    software = data.get("software_development")
    software_out = None
    if software is not None:
        if not isinstance(software, dict):
            problems.append("software_development")
        else:
            apps = _enum_list(software.get("app_types"), APP_TYPES)
            if apps is None:
                problems.append("software_development.app_types")
            stack = software.get("stack_preference")
            if stack is not None and not isinstance(stack, str):
                problems.append("software_development.stack_preference")
            if apps is not None and (
                stack is None or isinstance(stack, str)
            ):
                software_out = {
                    "app_types": apps,
                    "stack_preference": stack,
                }

    portfolio = data.get("portfolio")
    portfolio_out = None
    if portfolio is not None:
        if not isinstance(portfolio, dict):
            problems.append("portfolio")
        else:
            portfolio_out = {
                "media_assets": [],
                "historical_projects": [],
                "awards": [],
                "specialties": [],
            }
            media = portfolio.get("media_assets", [])
            if not _str_list(media) and media != []:
                problems.append("portfolio.media_assets")
            else:
                portfolio_out["media_assets"] = list(media)
            projects = portfolio.get("historical_projects", [])
            if not isinstance(projects, list):
                problems.append("portfolio.historical_projects")
            else:
                for i, pr in enumerate(projects):
                    if (
                        not isinstance(pr, dict)
                        or not isinstance(pr.get("project_name"), str)
                        or not isinstance(pr.get("location"), str)
                        or not isinstance(pr.get("year"), int)
                        or not isinstance(pr.get("asset_type"), str)
                    ):
                        problems.append(
                            f"portfolio.historical_projects[{i}]"
                        )
                    else:
                        portfolio_out["historical_projects"].append(pr)
            awards = portfolio.get("awards", [])
            if not isinstance(awards, list):
                problems.append("portfolio.awards")
            else:
                for i, aw in enumerate(awards):
                    if (
                        not isinstance(aw, dict)
                        or not isinstance(aw.get("award_name"), str)
                        or not isinstance(aw.get("year"), int)
                        or not isinstance(aw.get("organization"), str)
                    ):
                        problems.append(f"portfolio.awards[{i}]")
                    else:
                        portfolio_out["awards"].append(aw)
            specialties = portfolio.get("specialties", [])
            if not _str_list(specialties) and specialties != []:
                problems.append("portfolio.specialties")
            else:
                portfolio_out["specialties"] = list(specialties)

    sponsorship = data.get("sponsorship_status", False)
    if not isinstance(sponsorship, bool):
        problems.append("sponsorship_status")

    if problems:
        return None, problems
    return (
        {
            "name": name.strip(),
            "slug": slug,
            "creative_services": creative_out,
            "software_development": software_out,
            "portfolio": portfolio_out,
            "sponsorship_status": sponsorship,
        },
        [],
    )


def _store_path() -> Path:
    return Path(
        os.environ.get(
            "AFFILIATE_PROFILES_PATH", "./data/affiliate-profiles.jsonl"
        )
    )


def record_affiliate_profile(profile: dict[str, Any]) -> None:
    """Append one validated affiliate profile to the v1 store."""
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"profile": profile}) + "\n")


def order_affiliates(
    profiles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Directory ordering (mock logic): sponsored affiliates
    first, input order preserved within each group. This is
    the only effect sponsorship_status has anywhere."""
    return sorted(
        profiles, key=lambda p: 0 if p.get("sponsorship_status") else 1
    )
