"""Comp-set benchmarking for UZE Underwrite — D5 directive build.

Built 2026-11-13 executing the HiCRE principal's direct email
directive (D5, dugan.hjd5@gmail.com, 2026-11-13 16:20 ET —
"SoSem run this"). The directive, in substance:

  Compare the subject asset's rental revenue, other income, and
  operating expenses against nearby properties of the same
  multifamily type (low-rise, mid-rise, high-rise, garden style,
  townhouse community), age (year built), and class (A/B/C), in
  the same local market — on a PER-UNIT basis, because comp
  properties inevitably carry a different unit count. Cover
  every revenue line (market rent including per unit type where
  the data carries it, parking income, fees, utility
  reimbursements, credit loss, bad debt, vacancy) and every
  operating expense line (including repairs & maintenance).
  Flag the discrepancies as potential areas for improvement or
  irregularities, note that each should be further analyzed,
  and turn the flagged areas into a clear value-creation plan
  with the evidence and basis for each improvement.

How it fits the standing architecture:

  - Lines are identified through the ratified seven-bucket
    chart of accounts (chart_of_accounts.bucket_for, Yardi
    dialect fallback included). The taxonomy is NOT extended
    or altered here; this module only groups raw labels into
    canonical comparable lines inside their existing buckets.
    Unmapped labels are surfaced, never guessed — the same
    doctrine as the normalization layer.
  - SURA doctrine holds: judging happens ONLY against
    same-micro-region benchmarks. A comp outside the subject's
    micro-region is excluded with the reason stated; there is
    no cross-region fallback and no silent substitution.
  - HONESTY: there is no market database behind this module.
    The comp set is whatever the caller supplies in the
    request (or an existing labelled fixture the caller
    passes). With no comp set, the analysis returns the
    labelled state NO_COMP_SET_SUPPLIED — it never invents
    comps, medians, or market facts.
  - Only Revenue and Operating Expenses lines are benchmarked:
    the directive scopes itself to revenue and operating
    expenses. Taxes, Insurance, Interest, and Miscellaneous
    are jurisdiction- or contract-specific and stay in the
    subject's bucket summary (analyze_multiyear), unflagged
    here by design.

Matching: comps in the subject's micro-region are tiered by
profile closeness — tier A: same property type + class +
vintage band; tier B: same type + class; tier C: region only.
The benchmark set is the highest tier that yields at least one
comp, and the output states the tier used for every line's
evidence. Benchmarks are per-unit MEDIANS across the set.

Vintage bands (from year_built), documented policy:
  PRE_1980          year < 1980
  VINTAGE_1980_1999 1980-1999
  VINTAGE_2000_2009 2000-2009
  VINTAGE_2010_2019 2010-2019
  VINTAGE_2020_PLUS year >= 2020
A missing year_built yields band None ("unknown") and the comp
can match at tier B at best.

Flagging: a line is flagged when the subject's per-unit figure
diverges from the benchmark by more than the threshold
(DEFAULT_FLAG_THRESHOLD_PCT = 10%, a named policy default and
a per-call parameter — the same pattern as the Tier 3 variance
threshold in underwrite_engine). Classifications:

  revenue_opportunity  Revenue line earning below benchmark
                       (or a contra-revenue loss running
                       above benchmark) — value at stake.
  expense_opportunity  Operating expense line running above
                       benchmark — reduction at stake.
  irregularity         Divergence in the "favorable"
                       direction (revenue above benchmark,
                       expense or loss well below it). Favorable
                       is not assumed benign: an R&M line far
                       below comps can be deferred maintenance,
                       so it is flagged for verification, not
                       booked as performance.

Contra-revenue lines (Vacancy Loss, Credit Loss, Bad Debt)
are compared on LOSS MAGNITUDE per unit, because the caller's
sign convention for deductions varies (negative amounts or
positive deduction lines) and magnitude is the comparable
quantity. Annualized impact = |per-unit variance| x subject
units. Findings are ranked by annualized dollars, largest
first. Every finding carries its evidence (subject figure,
benchmark figure, comp count, match basis) and the standing
note "for further analysis" from the directive.
"""

from __future__ import annotations

from statistics import median
from typing import Any

import chart_of_accounts as coa

DIRECTIVE_REF = (
    "D5 directive, 2026-11-13: comp-set benchmarking by "
    "multifamily type, vintage, and class, per-unit, with a "
    "value-creation plan"
)

# Policy default (per-call adjustable; labelled in output).
DEFAULT_FLAG_THRESHOLD_PCT = 10.0

PROPERTY_TYPES: tuple[str, ...] = (
    "LOW_RISE",
    "MID_RISE",
    "HIGH_RISE",
    "GARDEN_STYLE",
    "TOWNHOUSE_COMMUNITY",
    "OTHER",
)

PROPERTY_CLASSES: tuple[str, ...] = ("A", "B", "C")

# Only these buckets are benchmarked (directive scope: revenue
# and operating expenses). The other five buckets are untouched.
_BENCHMARK_BUCKETS = ("Revenue", "Operating Expenses")

# Canonical revenue lines that are LOSSES (deductions): lower
# magnitude is better, and comparison is on magnitude per unit.
_CONTRA_REVENUE_LINES = ("Vacancy Loss", "Credit Loss", "Bad Debt")

# Raw-label alias groups -> canonical comparable line. Keys are
# chart_of_accounts._key-normalized forms. Lines not in any
# group keep their own identity (title-cased normalized key),
# so distinct lines never merge silently.
_LINE_ALIASES: dict[str, str] = {
    "market rent": "Market Rent",
    "market rent potential": "Market Rent",
    "gross potential rent": "Market Rent",
    "gross potential": "Market Rent",
    "parking": "Parking Income",
    "parking income": "Parking Income",
    "vacancy": "Vacancy Loss",
    "vacancy loss": "Vacancy Loss",
    "vacancy losses": "Vacancy Loss",
    "credit loss": "Credit Loss",
    "credit losses": "Credit Loss",
    "credit loss bad debt": "Credit Loss",
    "vacancy credit loss": "Credit Loss",
    "vacancy and credit loss": "Credit Loss",
    "vacancy loss credit loss": "Credit Loss",
    "bad debt": "Bad Debt",
    "bad debt expense": "Bad Debt",
    "utility reimbursement": "Utility Reimbursements",
    "utility reimbursements": "Utility Reimbursements",
    "utility reimbursements income": "Utility Reimbursements",
    "repairs maintenance": "Repairs & Maintenance",
    "rm": "Repairs & Maintenance",
    "maintenance expense": "Repairs & Maintenance",
    "maintenance": "Repairs & Maintenance",
}

_TYPE_ALIASES: dict[str, str] = {
    "low rise": "LOW_RISE",
    "lowrise": "LOW_RISE",
    "mid rise": "MID_RISE",
    "midrise": "MID_RISE",
    "high rise": "HIGH_RISE",
    "highrise": "HIGH_RISE",
    "garden style": "GARDEN_STYLE",
    "garden": "GARDEN_STYLE",
    "townhouse community": "TOWNHOUSE_COMMUNITY",
    "townhouse": "TOWNHOUSE_COMMUNITY",
    "townhome community": "TOWNHOUSE_COMMUNITY",
    "townhome": "TOWNHOUSE_COMMUNITY",
    "other": "OTHER",
}


def normalize_property_type(value: Any) -> str | None:
    """Canonical property type or None when the supplied value
    names none of the directive's multifamily types."""
    if value is None:
        return None
    key = coa._key(str(value))
    if str(value).strip().upper() in PROPERTY_TYPES:
        return str(value).strip().upper()
    return _TYPE_ALIASES.get(key) or _TYPE_ALIASES.get(key.replace(" ", ""))


def normalize_property_class(value: Any) -> str | None:
    if value is None:
        return None
    v = str(value).strip().upper().removeprefix("CLASS ")
    return v if v in PROPERTY_CLASSES else None


def vintage_band(year_built: Any) -> str | None:
    """The documented vintage band for a year built (see the
    module docstring). Missing/invalid years yield None."""
    try:
        year = int(year_built)
    except (TypeError, ValueError):
        return None
    if year < 1980:
        return "PRE_1980"
    if year <= 1999:
        return "VINTAGE_1980_1999"
    if year <= 2009:
        return "VINTAGE_2000_2009"
    if year <= 2019:
        return "VINTAGE_2010_2019"
    return "VINTAGE_2020_PLUS"


def normalize_profile(profile: dict | None) -> dict[str, Any]:
    """A caller-supplied property profile, normalized: the
    attributes the directive matches on, with the vintage band
    derived from year_built."""
    p = dict(profile or {})
    year = p.get("year_built")
    try:
        year = int(year) if year is not None else None
    except (TypeError, ValueError):
        year = None
    units = p.get("unit_count")
    try:
        units = int(units) if units is not None else None
    except (TypeError, ValueError):
        units = None
    return {
        "property_type": normalize_property_type(p.get("property_type")),
        "year_built": year,
        "vintage_band": vintage_band(year),
        "property_class": normalize_property_class(p.get("property_class")),
        "unit_count": units,
        "micro_region": (str(p.get("micro_region")).strip() or None)
        if p.get("micro_region") is not None
        else None,
    }


def _bucket_for_canonical(name: str) -> str | None:
    """The ratified bucket for a canonical line, resolved
    through the chart of accounts from any filed label variant
    in its alias group ("market rent" itself is unfiled, but
    its sibling "market rent potential" is filed as Revenue in
    the Yardi pack). None when no variant in the group is
    filed anywhere — the line is then treated as unmapped."""
    for key, alias_name in _LINE_ALIASES.items():
        if alias_name == name:
            bucket = coa.bucket_for(key)
            if bucket is not None:
                return bucket
    return None


def canonical_line(label: str) -> tuple[str, str] | None:
    """(canonical comparable line, ratified bucket) for a raw
    P&L label, or None when the label is unmapped in the chart
    of accounts (surfaced by callers, never guessed).

    Market rent stated per unit type ("Market Rent — 1BR")
    canonicalizes to "Market Rent (1BR)" so unit-type rent
    lines benchmark separately from the blended market-rent
    line, exactly as the directive asks where the data
    carries unit types."""
    key = coa._key(label)
    # "&" and the word "and" produce different raw keys for the
    # same filed line ("Repairs & Maintenance" files as
    # "repairs maintenance"; "Repairs and Maintenance" keeps
    # its "and") — try the "and"-collapsed form as well.
    candidates = [key, key.replace(" and ", " "), key.replace(" ", "")]
    for cand in candidates:
        hit = _LINE_ALIASES.get(cand)
        if hit is not None:
            bucket = coa.bucket_for(label) or _bucket_for_canonical(hit)
            if bucket is not None:
                return hit, bucket
    for alias in ("market rent potential", "market rent", "gross potential rent"):
        if key.startswith(alias + " "):
            suffix = key[len(alias) + 1 :].strip()
            # The base label is a filed Revenue line; the
            # suffix is a unit-type qualifier, not a new label.
            base_bucket = coa.bucket_for(label) or _bucket_for_canonical(
                "Market Rent"
            )
            if suffix and base_bucket is not None:
                return f"Market Rent ({suffix.upper()})", base_bucket
    bucket = coa.bucket_for(label)
    if bucket is None:
        return None
    return key.title(), bucket


def _canonical_lines(line_items: dict) -> tuple[dict[str, dict], list[dict]]:
    """Group one property's raw line items into canonical
    lines: {line: {bucket, amount}}. Unmapped labels come back
    separately in the filing layer's own shape."""
    lines: dict[str, dict[str, Any]] = {}
    unmapped: list[dict[str, Any]] = []
    for label, amount in (line_items or {}).items():
        found = canonical_line(label)
        if found is None:
            unmapped.append({"label": label, "amount": amount})
            continue
        name, bucket = found
        entry = lines.setdefault(name, {"bucket": bucket, "amount": 0.0})
        entry["amount"] += float(amount)
    return lines, unmapped


def _match_tier(subject: dict, comp: dict) -> str | None:
    """A/B/C closeness of a comp profile to the subject, or
    None when the comp is outside the subject's micro-region
    (SURA doctrine: no cross-region judging, ever)."""
    if not subject["micro_region"] or not comp["micro_region"]:
        return None
    if subject["micro_region"].lower() != comp["micro_region"].lower():
        return None
    same_type = (
        subject["property_type"] is not None
        and subject["property_type"] == comp["property_type"]
    )
    same_class = (
        subject["property_class"] is not None
        and subject["property_class"] == comp["property_class"]
    )
    same_band = (
        subject["vintage_band"] is not None
        and subject["vintage_band"] == comp["vintage_band"]
    )
    if same_type and same_class and same_band:
        return "A"
    if same_type and same_class:
        return "B"
    return "C"


_TIER_BASIS = {
    "A": "same micro-region + property type + class + vintage band",
    "B": "same micro-region + property type + class",
    "C": "same micro-region only",
}

# Plain-language actions for the value-creation plan, keyed by
# canonical line; the generic fallbacks keep every plan entry
# concrete without inventing facts — all figures cited in a
# plan entry come from the comp-set evidence itself.
_PLAN_ACTIONS: dict[str, str] = {
    "Market Rent": (
        "Test market-rent movement toward the comp-set per-unit "
        "median at renewal and on unit turns; validate against "
        "the subject's unit mix before underwriting any uplift."
    ),
    "Parking Income": (
        "Audit parking inventory, pricing, and collections "
        "against the comp set's per-unit parking income; close "
        "the collection or pricing gap the audit isolates."
    ),
    "Vacancy Loss": (
        "Attack the vacancy gap: turn time, concessions, and "
        "renewal capture, measured against the comp set's "
        "per-unit vacancy loss."
    ),
    "Credit Loss": (
        "Tighten screening and collections cadence to move the "
        "credit-loss rate toward the comp-set benchmark."
    ),
    "Bad Debt": (
        "Review bad-debt write-off drivers and recovery process "
        "against the comp set's per-unit experience."
    ),
    "Utility Reimbursements": (
        "Audit utility billing-back coverage and recovery rates "
        "against the comp set's per-unit reimbursements."
    ),
    "Repairs & Maintenance": (
        "Re-bid recurring R&M contracts and audit the work-order "
        "mix against the comp-set per-unit norm."
    ),
}

_PLAN_ACTIONS_IRREGULARITY: dict[str, str] = {
    "Repairs & Maintenance": (
        "Verify the R&M gap is not deferred maintenance: "
        "inspect unit and systems condition before treating "
        "below-benchmark spend as performance."
    ),
}


def _plan_action(line: str, bucket: str, classification: str) -> str:
    if classification == "irregularity":
        if line in _PLAN_ACTIONS_IRREGULARITY:
            return _PLAN_ACTIONS_IRREGULARITY[line]
        return (
            "Verify the divergence is real and sustainable — "
            "confirm scope, one-off items, and accounting "
            "treatment before relying on it."
        )
    if line in _PLAN_ACTIONS:
        return _PLAN_ACTIONS[line]
    if bucket == "Revenue":
        return (
            "Test pricing and fee capture toward the comp-set "
            "per-unit median where the subject trails it, and "
            "document the basis before presenting it."
        )
    return (
        "Re-bid or renegotiate this line toward the comp-set "
        "per-unit median, verifying scope parity with the comps."
    )


def analyze_comp_set(
    subject_profile: dict | None,
    subject_line_items: dict | None,
    comps: list[dict] | None,
    *,
    threshold_pct: float = DEFAULT_FLAG_THRESHOLD_PCT,
) -> dict[str, Any]:
    """The comp-set benchmark analysis (see module docstring).

    subject_profile: {property_type, year_built,
    property_class, unit_count, micro_region} for the subject.
    comps: [{name?, profile: {...}, line_items: {label:
    amount}}] — supplied by the caller; never sourced here."""
    base: dict[str, Any] = {
        "directive": DIRECTIVE_REF,
        "threshold_pct": threshold_pct,
        "benchmark_buckets": list(_BENCHMARK_BUCKETS),
        "note": (
            "Benchmarks are per-unit medians of the comp set "
            "supplied in the request. No market database is "
            "consulted; nothing here is a market fact beyond "
            "the supplied comps."
        ),
    }
    if subject_profile is None:
        return {
            **base,
            "status": "SUBJECT_PROFILE_REQUIRED",
            "note": (
                "A subject property profile (property_type, "
                "year_built, property_class, unit_count, "
                "micro_region) is required to match a comp set."
            ),
        }
    subject = normalize_profile(subject_profile)
    base["subject"] = subject
    if not subject["unit_count"]:
        raise ValueError(
            "subject profile requires a positive unit_count — "
            "per-unit comparison is impossible without it"
        )
    if not comps:
        return {
            **base,
            "status": "NO_COMP_SET_SUPPLIED",
            "note": (
                "No comparable set was supplied with this "
                "request, so no benchmarking was performed and "
                "none is implied. Supply comps (profile + "
                "line_items per property) to run the analysis."
            ),
            "findings": [],
            "value_creation_plan": [],
        }

    subject_lines, subject_unmapped = _canonical_lines(subject_line_items or {})
    subject_units = subject["unit_count"]

    # --- match and tier the supplied comps -------------------
    usable: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for comp in comps:
        name = comp.get("name") or "unnamed comp"
        profile = normalize_profile(comp.get("profile"))
        tier = _match_tier(subject, profile)
        if tier is None:
            excluded.append(
                {
                    "name": name,
                    "reason": (
                        "outside the subject's micro-region "
                        f"({profile['micro_region']!r} vs "
                        f"{subject['micro_region']!r}) — comps "
                        "are judged only within the micro-region"
                    ),
                }
            )
            continue
        if not profile["unit_count"]:
            excluded.append(
                {
                    "name": name,
                    "reason": (
                        "no unit_count — per-unit comparison is "
                        "impossible for this comp"
                    ),
                }
            )
            continue
        lines, unmapped = _canonical_lines(comp.get("line_items") or {})
        usable.append(
            {
                "name": name,
                "profile": profile,
                "tier": tier,
                "lines": lines,
                "unmapped": unmapped,
            }
        )
    if not usable:
        return {
            **base,
            "status": "NO_REGION_MATCHES",
            "note": (
                "The supplied comp set contains no property in "
                "the subject's micro-region with a usable unit "
                "count, so no benchmark was computed. Cross-"
                "region benchmarks are never substituted."
            ),
            "excluded_comps": excluded,
            "findings": [],
            "value_creation_plan": [],
        }
    best_tier = min(c["tier"] for c in usable)
    comp_set = [c for c in usable if c["tier"] == best_tier]
    match_basis = _TIER_BASIS[best_tier]

    # --- per-unit benchmarks ---------------------------------
    line_names: set[str] = set()
    for name_, info in subject_lines.items():
        if info["bucket"] in _BENCHMARK_BUCKETS:
            line_names.add(name_)
    for comp in comp_set:
        for name_, info in comp["lines"].items():
            if info["bucket"] in _BENCHMARK_BUCKETS:
                line_names.add(name_)

    lines_out: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for line in sorted(line_names):
        contra = line in _CONTRA_REVENUE_LINES
        subj_info = subject_lines.get(line)
        bucket = (
            subj_info["bucket"]
            if subj_info
            else next(
                c["lines"][line]["bucket"] for c in comp_set if line in c["lines"]
            )
        )
        subj_amount = subj_info["amount"] if subj_info else 0.0
        subj_pu = subj_amount / subject_units
        comp_pus: list[float] = []
        for comp in comp_set:
            info = comp["lines"].get(line)
            if info is not None:
                comp_pus.append(info["amount"] / comp["profile"]["unit_count"])
        if not comp_pus:
            continue
        bench_pu = median(comp_pus)
        # Contra-revenue lines compare on loss magnitude.
        s_cmp = abs(subj_pu) if contra else subj_pu
        b_cmp = abs(bench_pu) if contra else bench_pu
        variance_pu = round(subj_pu - bench_pu, 2)
        if b_cmp:
            variance_pct = round((s_cmp - b_cmp) / abs(b_cmp) * 100, 2)
        else:
            variance_pct = None
        row: dict[str, Any] = {
            "line": line,
            "bucket": bucket,
            "subject_per_unit": round(subj_pu, 2),
            "benchmark_per_unit": round(bench_pu, 2),
            "variance_per_unit": variance_pu,
            "variance_pct": variance_pct,
            "comp_count": len(comp_pus),
            "match_basis": match_basis,
            "compared_on": "loss magnitude per unit" if contra else "per unit",
            "in_subject": subj_info is not None,
        }
        lines_out.append(row)

        flagged = variance_pct is None or abs(variance_pct) > threshold_pct
        if b_cmp == 0 and s_cmp == 0:
            flagged = False
        if not flagged:
            continue
        expense_like = bucket == "Operating Expenses" or contra
        if variance_pct is None:
            classification = "irregularity"
        elif expense_like:
            classification = (
                "expense_opportunity"
                if bucket == "Operating Expenses" and variance_pct > 0
                else "revenue_opportunity"
                if contra and variance_pct > 0
                else "irregularity"
            )
        else:
            classification = (
                "revenue_opportunity" if variance_pct < 0 else "irregularity"
            )
        annualized = round(abs(variance_pu) * subject_units, 2)
        findings.append(
            {
                **row,
                "classification": classification,
                "annualized_impact_usd": annualized,
                "evidence": {
                    "subject_per_unit": round(subj_pu, 2),
                    "benchmark_per_unit": round(bench_pu, 2),
                    "benchmark_statistic": "median of per-unit figures",
                    "comp_count": len(comp_pus),
                    "match_basis": match_basis,
                    "subject_units": subject_units,
                },
                "note": "for further analysis",
            }
        )
    findings.sort(key=lambda f: -f["annualized_impact_usd"])

    # --- the value-creation plan ------------------------------
    plan: list[dict[str, Any]] = []
    for f in findings:
        plan.append(
            {
                "line": f["line"],
                "bucket": f["bucket"],
                "classification": f["classification"],
                "gap_per_unit": f["variance_per_unit"],
                "annualized_value_at_stake_usd": f["annualized_impact_usd"],
                "evidence_basis": (
                    f"Subject runs ${f['subject_per_unit']:,.2f}/unit "
                    f"against a comp-set median of "
                    f"${f['benchmark_per_unit']:,.2f}/unit "
                    f"({f['comp_count']} comp(s), {match_basis}). "
                    "The basis for the improvement is the comp "
                    "set's own demonstrated per-unit figure."
                ),
                "action": _plan_action(f["line"], f["bucket"], f["classification"]),
                "note": "for further analysis",
            }
        )

    return {
        **base,
        "status": "OK",
        "match": {
            "basis": match_basis,
            "tier": best_tier,
            "comp_set": [
                {
                    "name": c["name"],
                    "property_type": c["profile"]["property_type"],
                    "year_built": c["profile"]["year_built"],
                    "vintage_band": c["profile"]["vintage_band"],
                    "property_class": c["profile"]["property_class"],
                    "unit_count": c["profile"]["unit_count"],
                    "micro_region": c["profile"]["micro_region"],
                    "tier": c["tier"],
                }
                for c in comp_set
            ],
            "other_region_or_unusable_comps": excluded,
            "lower_tier_region_comps_not_used": [
                c["name"] for c in usable if c["tier"] != best_tier
            ],
        },
        "lines": lines_out,
        "findings": findings,
        "value_creation_plan": plan,
        "unmapped": {
            "subject": subject_unmapped,
            "comps": [
                {"name": c["name"], "unmapped": c["unmapped"]}
                for c in comp_set
                if c["unmapped"]
            ],
        },
    }
