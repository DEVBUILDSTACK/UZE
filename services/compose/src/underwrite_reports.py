"""UZE Underwrite reports — persistence, receipts, claims, the
comp pool, and change tracking for underwrite runs (2026-11-13
night sprint).

This module is the data layer behind every underwrite door
(multiyear JSON, MCP, and the email gateway): a run is analyzed
by email_gateway.analyze_multiyear, persisted as an
UnderwriteReport with a verifiable receipt (sha256 of the
payload's canonical JSON + engine version), and — where the
rules below allow — turned into an Assuraties NOI claim.

HONESTY RULES (product, never weakened):

  - Claims are NEVER issued from mock data. The email door's
    extraction is a labelled mock in this build, so email-door
    reports are recorded NOT_APPLICABLE and issue no claim,
    ever. Claims issue only from the multiyear / mcp doors,
    only against a declared micro-region that exists in the
    reference table, and only for a computed (unlevered) NOI
    figure from a real analysis run.
  - The comp pool is OPT-IN and ANONYMIZED. A run contributes
    only when the caller sets contribute_comps, and what is
    stored is per-unit canonical lines (Revenue and Operating
    Expenses only — the benchmark scope) under a sha256
    contributor reference. No property name, no raw total, and
    no sender string is ever written to the pool.
  - Notifications are QUEUED, never claimed sent. This service
    composes notification records; delivery happens, if at
    all, on the UZEmarkets operator rail outside the service,
    and no body in this module says otherwise.
"""

from __future__ import annotations

import copy
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

import assuraties
import chart_of_accounts as coa
import comp_benchmark
import email_gateway
import models

ENGINE_VERSION = "underwrite-engine-2026.11.13.1"

DOOR_EMAIL = "email"
DOOR_MULTIYEAR = "multiyear"
DOOR_MCP = "mcp"
DOORS = (DOOR_MULTIYEAR, DOOR_MCP, DOOR_EMAIL)

_CLAIM_DOORS = (DOOR_MULTIYEAR, DOOR_MCP)
_POOL_BUCKETS = ("Revenue", "Operating Expenses")

# Representative year_built for a stored vintage band, used to
# rebuild a comp profile the benchmark engine can match on.
_BAND_REPRESENTATIVE_YEAR: dict[str, int] = {
    "PRE_1980": 1975,
    "VINTAGE_1980_1999": 1990,
    "VINTAGE_2000_2009": 2005,
    "VINTAGE_2010_2019": 2015,
    "VINTAGE_2020_PLUS": 2022,
}


# ------------------------------------------------------------------
# Receipts and hashing
# ------------------------------------------------------------------


def canonical_json(obj: Any) -> str:
    """The canonical JSON form a receipt hash commits to:
    sorted keys, compact separators, non-JSON scalars rendered
    with str() rather than refused."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def compute_input_hash(payload: Any) -> str:
    """sha256 hex of the payload's canonical JSON."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def receipt_for(report: models.UnderwriteReport) -> dict[str, Any]:
    issued_at = datetime.fromtimestamp(
        int(report.created_at), tz=timezone.utc
    ).isoformat().replace("+00:00", "Z")
    return {
        "report_id": report.id,
        "input_hash": report.input_hash,
        "engine_version": report.engine_version,
        "issued_at": issued_at,
        "claim_id": report.claim_id,
    }


# ------------------------------------------------------------------
# Reads
# ------------------------------------------------------------------


def get_report(session, report_id: str) -> models.UnderwriteReport | None:
    if not report_id:
        return None
    return session.get(models.UnderwriteReport, report_id)


def report_view(session, report: models.UnderwriteReport) -> dict[str, Any]:
    """The stored result, its receipt, and the report's own
    metadata (door, sender, claim outcome) side by side."""
    return {
        **(report.result or {}),
        "receipt": receipt_for(report),
        "report": {
            "id": report.id,
            "door": report.door,
            "sender": report.sender,
            "subject_profile": report.subject_profile,
            "contribute_comps": report.contribute_comps,
            "claim_status": report.claim_status,
            "claim_note": report.claim_note,
            "created_at": report.created_at,
        },
    }


def render_report_pdf(session, report: models.UnderwriteReport) -> bytes:
    """The human-facing PDF for a stored report. Email-door
    reports have no PDF here BY DESIGN: their assessment PDF
    accompanied the original gateway response, and re-rendering
    one from the stored (mock-labelled) extraction would
    misstate what the report is."""
    if report.door == DOOR_EMAIL:
        raise ValueError(
            "REPORT_PDF_NOT_APPLICABLE: email-door assessments "
            "carry their PDF in the original gateway response"
        )
    return email_gateway.render_multiyear_pdf(report.result)


# ------------------------------------------------------------------
# Notifications — composed by the service, QUEUED, never sent here
# ------------------------------------------------------------------


def list_notifications(session, report_id: str) -> list[dict[str, Any]]:
    rows = (
        session.query(models.ReportNotification)
        .filter(models.ReportNotification.report_id == report_id)
        .order_by(models.ReportNotification.beat)
        .all()
    )
    return [
        {
            "id": row.id,
            "report_id": row.report_id,
            "beat": row.beat,
            "to": row.recipient,
            "subject": row.subject,
            "body": row.body,
            "status": row.status,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def _periods_of(result: dict | None) -> list[dict]:
    return list((result or {}).get("periods") or [])


def _latest_noi(result: dict | None) -> Any:
    periods = _periods_of(result)
    if periods:
        return periods[-1].get("noi")
    extracted = (result or {}).get("extracted") or {}
    if isinstance(extracted, dict) and extracted.get("netOperatingIncome") is not None:
        return extracted["netOperatingIncome"]
    return (result or {}).get("netOperatingIncome")


def _money(value: Any) -> str:
    return f"${float(value):,.2f}"


def compose_notifications(session, report, sender_email, result):
    """Compose beat 1 (submission received) and beat 2 (report
    ready) for a report and store them as QUEUED
    ReportNotification rows. Generic product templates only —
    no personalized correspondence. The bodies describe the
    record truthfully: this service queues notifications; it
    does not send email."""
    result = result or {}
    periods = _periods_of(result)
    latest_noi = _latest_noi(result)
    report_path = f"/api/v1/underwrite/reports/{report.id}"
    now = int(time.time())

    beat1_lines = [
        f"Your UZE Underwrite submission was received (report {report.id}).",
        f"Door: {report.door}.",
    ]
    if periods:
        beat1_lines.append(f"Periods analyzed: {len(periods)}.")
        if latest_noi is not None:
            beat1_lines.append(
                f"Latest period ({periods[-1].get('period')}) net operating "
                f"income (unlevered): {_money(latest_noi)}."
            )
    elif latest_noi is not None:
        beat1_lines.append(
            f"Net operating income in the assessment: {_money(latest_noi)}."
        )
    beat1_lines += [
        f"Input hash: {report.input_hash}.",
        f"Engine version: {report.engine_version}.",
        (
            "What happens next: a delivery email follows from the "
            "UZEmarkets operator rail. This notification is a QUEUED "
            "record composed by the service; the service itself does "
            "not send email."
        ),
        f"The report is retrievable at GET {report_path}.",
    ]
    beat1 = models.ReportNotification(
        report_id=report.id,
        beat=1,
        recipient=sender_email,
        subject=f"UZE Underwrite — submission received (report {report.id})",
        body="\n".join(beat1_lines),
        status="QUEUED",
        created_at=now,
    )

    beat2_lines = [f"Your UZE Underwrite report is ready (report {report.id})."]
    if latest_noi is not None:
        if periods:
            beat2_lines.append(
                f"Latest period ({periods[-1].get('period')}) net operating "
                f"income (unlevered): {_money(latest_noi)}."
            )
        else:
            beat2_lines.append(
                f"Net operating income in the assessment: {_money(latest_noi)}."
            )
    section = result.get("comp_benchmark") or {}
    findings = section.get("findings") or []
    if findings:
        top = findings[0]
        beat2_lines.append(
            f"Top benchmarking finding: {top.get('line')} "
            f"({top.get('classification')})."
        )
    if report.door == DOOR_EMAIL:
        beat2_lines.append(
            "The assessment PDF accompanied the original gateway response."
        )
    else:
        beat2_lines.append(f"PDF: {report_path}/pdf.")
    beat2_lines.append(f"Report: {report_path}.")
    beat2_lines.append(
        "This notification is a QUEUED record composed by the service; "
        "the service itself does not send email."
    )
    beat2 = models.ReportNotification(
        report_id=report.id,
        beat=2,
        recipient=sender_email,
        subject=f"UZE Underwrite — your report is ready (report {report.id})",
        body="\n".join(beat2_lines),
        status="QUEUED",
        created_at=now,
    )

    session.add_all([beat1, beat2])
    session.flush()
    return [beat1, beat2]


# ------------------------------------------------------------------
# NOI claim issuance — never raises, never from mock data
# ------------------------------------------------------------------


def issue_noi_claim(session, report, result, subject_profile):
    """Issue the report's NOI claim through the Assuraties
    service function, or record plainly why not.

    Returns (claim_id | None, status, note) and NEVER raises:
    status is ISSUED (a claim row exists and claim_id is its
    id), NOT_ISSUED (a plain-language reason in note), or
    NOT_APPLICABLE (a door claims never issue from). The claim
    hangs off a carrier Intent the engine posts for exactly
    this purpose, in the subject's declared micro-region."""
    try:
        if report.door not in _CLAIM_DOORS:
            return (
                None,
                "NOT_APPLICABLE",
                f"claims are issued only from the multiyear/mcp doors, "
                f"not the {report.door!r} door",
            )
        periods = _periods_of(result)
        if not periods:
            return (
                None,
                "NOT_ISSUED",
                "the analysis produced no periods, so there is no "
                "NOI figure to claim",
            )
        if not subject_profile or not subject_profile.get("micro_region"):
            return (
                None,
                "NOT_ISSUED",
                "no declared micro-region in the subject profile; "
                "claims are judged only against a declared micro-region",
            )
        slug = subject_profile["micro_region"]
        region = session.get(models.MicroRegion, slug)
        if region is None:
            return (
                None,
                "NOT_ISSUED",
                f"declared micro-region {slug!r} is not in the "
                f"reference table",
            )
        latest = periods[-1]
        latest_period = latest.get("period")
        noi = latest.get("noi")
        if noi is None:
            return (
                None,
                "NOT_ISSUED",
                "the latest period carries no NOI figure to claim",
            )
        now = int(time.time())
        intent = models.Intent(
            kind=models.IntentKind.DEMAND,
            poster_kind=models.PosterKind.INTERNAL_AGENT,
            poster_account="uze-underwrite-engine",
            domain=models.IntentDomain.CRE_INCOME_ANALYSIS,
            work_product=models.WorkProduct.BENCHMARK_ANALYSIS,
            deliverable={
                "kind": "underwrite_report",
                "reportId": report.id,
                "metric": "NOI",
            },
            micro_region_id=slug,
            asset_context={"subject_profile": subject_profile},
            budget_min_usdc=0,
            budget_max_usdc=0,
            available_from=now,
            available_until=now + 30 * 86400,
            tier=models.IntentTier.ANY,
        )
        session.add(intent)
        session.flush()
        section = (result or {}).get("comp_benchmark")
        comp_summary = (
            {"status": section.get("status"), "match": section.get("match")}
            if isinstance(section, dict)
            else None
        )
        view = assuraties.issue_claim(
            assuraties.ClaimIn(
                intentId=intent.id,
                claimClass=models.ClaimClass.HICRE_ASSET,
                periodKind=None,
                statement=(
                    f"Net operating income (unlevered) for period "
                    f"{latest_period} is ${noi:,.2f}, as computed by "
                    f"the UZE Underwrite engine in report {report.id}."
                ),
                claimedValue={
                    "metric": "NOI",
                    "basis": "unlevered",
                    "amount": noi,
                    "currency": "USD",
                    "period": latest_period,
                    "reportId": report.id,
                    "subjectProfile": subject_profile,
                    "compBenchmark": comp_summary,
                },
                claimantEntityId="uze-underwrite-engine",
                bondAmount=0,
            ),
            session,
        )
        return view.id, "ISSUED", None
    except HTTPException as exc:
        try:
            session.rollback()
        except Exception:  # noqa: BLE001 — the no-raise rule governs
            pass
        return None, "NOT_ISSUED", f"claim issuance was refused: {exc.detail}"
    except Exception as exc:  # noqa: BLE001 — the no-raise rule governs
        try:
            session.rollback()
        except Exception:  # noqa: BLE001
            pass
        return (
            None,
            "NOT_ISSUED",
            f"claim issuance failed: {type(exc).__name__}: {exc}",
        )


# ------------------------------------------------------------------
# Delta — this run against a prior report
# ------------------------------------------------------------------


def _latest_line_items(years: list | None) -> dict:
    if not years:
        return {}
    ordered = sorted(years, key=lambda y: str(y.get("period", "")))
    return dict(ordered[-1].get("line_items") or {})


def _latest_period_label(years: list | None) -> str | None:
    if not years:
        return None
    ordered = sorted(years, key=lambda y: str(y.get("period", "")))
    return ordered[-1].get("period")


def _unit_count(profile: dict | None) -> int | None:
    if not profile:
        return None
    units = comp_benchmark.normalize_profile(profile)["unit_count"]
    return units if units and units > 0 else None


def _change_block(prior: Any, current: Any) -> dict[str, Any]:
    if prior is None or current is None:
        return {
            "prior": prior,
            "current": current,
            "change_abs": None,
            "change_pct": None,
        }
    change_abs = round(float(current) - float(prior), 2)
    change_pct = (
        round((float(current) - float(prior)) / abs(float(prior)) * 100, 2)
        if prior
        else None
    )
    return {
        "prior": prior,
        "current": current,
        "change_abs": change_abs,
        "change_pct": change_pct,
    }


def compute_delta(prior_report, new_result, new_payload) -> dict[str, Any]:
    """Change tracking between a prior report and a new run:
    NOI and bucket movement on the latest periods, canonical
    per-unit line movement, and — for every line the prior
    run's value-creation plan named — whether the subject
    moved toward or away from the prior benchmark.

    Plan tracking compares DISTANCE TO BENCHMARK on the
    subject (non-contra) per-unit figures for every
    classification alike: the distance rule handles revenue,
    expense, and contra-revenue lines uniformly, because a
    contra line's benchmark and subject figures carry the
    same sign convention on both sides of the comparison."""
    prior_result = prior_report.result or {}
    prior_periods = _periods_of(prior_result)
    new_periods = _periods_of(new_result)
    prior_latest = prior_periods[-1] if prior_periods else {}
    new_latest = new_periods[-1] if new_periods else {}

    buckets = {
        bucket: _change_block(
            (prior_latest.get("buckets") or {}).get(bucket),
            (new_latest.get("buckets") or {}).get(bucket),
        )
        for bucket in coa.BUCKETS
    }

    prior_items = _latest_line_items(
        (prior_report.request_payload or {}).get("years")
    )
    new_items = _latest_line_items((new_payload or {}).get("years"))
    prior_canon, _ = comp_benchmark._canonical_lines(prior_items)
    new_canon, _ = comp_benchmark._canonical_lines(new_items)
    prior_units = _unit_count(prior_report.subject_profile)
    new_units = _unit_count((new_payload or {}).get("subject_profile"))

    def _per_unit(canon: dict, name: str, units: int | None):
        if units is None or name not in canon:
            return None
        return round(float(canon[name]["amount"]) / units, 4)

    line_names = sorted(set(prior_canon) | set(new_canon))
    lines: list[dict[str, Any]] = []
    if prior_units and new_units:
        for name in line_names:
            bucket = (prior_canon.get(name) or new_canon.get(name))["bucket"]
            prior_pu = _per_unit(prior_canon, name, prior_units) or 0.0
            current_pu = _per_unit(new_canon, name, new_units) or 0.0
            lines.append(
                {
                    "line": name,
                    "bucket": bucket,
                    "prior_per_unit": prior_pu,
                    "current_per_unit": current_pu,
                    "change_per_unit": round(current_pu - prior_pu, 4),
                }
            )
    else:
        for name in line_names:
            bucket = (prior_canon.get(name) or new_canon.get(name))["bucket"]
            prior_total = (
                float(prior_canon[name]["amount"]) if name in prior_canon else 0.0
            )
            current_total = (
                float(new_canon[name]["amount"]) if name in new_canon else 0.0
            )
            lines.append(
                {
                    "line": name,
                    "bucket": bucket,
                    "prior_total": prior_total,
                    "current_total": current_total,
                    "change_total": round(current_total - prior_total, 2),
                    "basis": "totals — unit count not declared on one side",
                }
            )

    prior_section = prior_result.get("comp_benchmark") or {}
    plan = prior_section.get("value_creation_plan") or []
    findings = {
        f["line"]: f for f in (prior_section.get("findings") or [])
    }
    plan_tracking: list[dict[str, Any]] = []
    for entry in plan:
        line = entry.get("line")
        finding = findings.get(line) or {}
        benchmark = finding.get("benchmark_per_unit")
        prior_pu = _per_unit(prior_canon, line, prior_units)
        if prior_pu is None:
            prior_pu = finding.get("subject_per_unit")
        current_pu = _per_unit(new_canon, line, new_units)
        if line not in new_canon:
            status = "line_absent"
            current_pu = None
            annualized = None
        elif benchmark is None or prior_pu is None or current_pu is None:
            status = "unchanged"
            annualized = None
        else:
            eps = max(0.005 * abs(float(prior_pu)), 0.01)
            prior_dist = abs(float(prior_pu) - float(benchmark))
            new_dist = abs(float(current_pu) - float(benchmark))
            if new_dist < prior_dist - eps:
                status = "improved"
            elif new_dist > prior_dist + eps:
                status = "worsened"
            else:
                status = "unchanged"
            annualized = (
                round((float(current_pu) - float(prior_pu)) * new_units, 2)
                if new_units
                else None
            )
        plan_tracking.append(
            {
                "line": line,
                "classification": entry.get("classification"),
                "benchmark_per_unit": benchmark,
                "prior_per_unit": prior_pu,
                "current_per_unit": current_pu,
                "status": status,
                "annualized_change_usd": annualized,
            }
        )

    return {
        "status": "OK",
        "prior_report_id": prior_report.id,
        "noi": _change_block(prior_latest.get("noi"), new_latest.get("noi")),
        "buckets": buckets,
        "lines": lines,
        "plan_tracking": plan_tracking,
    }


# ------------------------------------------------------------------
# The comp pool — opt-in, anonymized, per-unit only
# ------------------------------------------------------------------


def record_pool_contribution(session, report, payload) -> int:
    """Write one CompPoolEntry for this report when — and only
    when — the caller opted in (contribute_comps), declared a
    subject profile with micro_region and unit_count, and the
    report carries a sender identity to credit. Returns 1 when
    a row was written, else 0. The row stores per-unit figures
    only; the caller commits."""
    payload = payload or {}
    if not payload.get("contribute_comps"):
        return 0
    profile = payload.get("subject_profile")
    if not profile:
        return 0
    normalized = comp_benchmark.normalize_profile(profile)
    if not normalized.get("micro_region") or not normalized.get("unit_count"):
        return 0
    if not report.sender:
        return 0
    years = payload.get("years") or []
    items = _latest_line_items(years)
    if not items:
        return 0
    canon, _unmapped = comp_benchmark._canonical_lines(items)
    first_label: dict[str, str] = {}
    for raw_label in items:
        found = comp_benchmark.canonical_line(raw_label)
        if found is not None and found[0] not in first_label:
            first_label[found[0]] = raw_label
    lines: dict[str, Any] = {}
    for name, info in canon.items():
        if info["bucket"] not in _POOL_BUCKETS:
            continue
        lines[name] = {
            "bucket": info["bucket"],
            "per_unit": round(
                float(info["amount"]) / normalized["unit_count"], 4
            ),
            "label": first_label.get(name, name),
        }
    if not lines:
        return 0
    session.add(
        models.CompPoolEntry(
            micro_region=normalized["micro_region"],
            property_type=normalized.get("property_type"),
            property_class=normalized.get("property_class"),
            vintage_band=normalized.get("vintage_band"),
            unit_count=normalized["unit_count"],
            period=_latest_period_label(years),
            lines=lines,
            contributor_ref=hashlib.sha256(
                report.sender.encode("utf-8")
            ).hexdigest(),
            credit_units=1,
            created_at=int(time.time()),
        )
    )
    return 1


def load_pool_comps(session, micro_region: str) -> list[dict[str, Any]]:
    """The pool's entries for one micro-region, reshaped as the
    comp dicts analyze_comp_set consumes. Stored per-unit
    figures are re-expanded by the entry's own unit count, so
    the engine's per-unit math returns exactly the stored
    per-unit figures. The stored vintage band is represented
    by a year inside the band, so tier matching sees the band
    the contribution declared."""
    rows = (
        session.query(models.CompPoolEntry)
        .filter(models.CompPoolEntry.micro_region == micro_region)
        .order_by(models.CompPoolEntry.created_at, models.CompPoolEntry.id)
        .all()
    )
    comps: list[dict[str, Any]] = []
    for i, entry in enumerate(rows, start=1):
        line_items: dict[str, float] = {}
        for name, info in (entry.lines or {}).items():
            per_unit = info.get("per_unit")
            if per_unit is None or not entry.unit_count:
                continue
            label = info.get("label") or name
            line_items[label] = round(float(per_unit) * entry.unit_count, 2)
        comps.append(
            {
                "name": f"Pooled comp {i}",
                "profile": {
                    "property_type": entry.property_type,
                    "year_built": _BAND_REPRESENTATIVE_YEAR.get(
                        entry.vintage_band
                    ),
                    "property_class": entry.property_class,
                    "unit_count": entry.unit_count,
                    "micro_region": entry.micro_region,
                },
                "line_items": line_items,
            }
        )
    return comps


# ------------------------------------------------------------------
# The pipelines
# ------------------------------------------------------------------


def run_multiyear_ingest(session, payload: dict, *, door: str) -> dict:
    """The full multiyear pipeline the HTTP handler and the MCP
    tool both call: pool injection, analysis, delta against a
    prior report, persistence + notifications + pool
    contribution in ONE commit, then NOI claim issuance and a
    second commit recording its outcome. A pool/persist
    failure rolls back loudly (nothing is caught in that step);
    a failure of the claim-outcome commit likewise propagates.
    Claim issuance itself never raises (see issue_noi_claim)."""
    payload = payload or {}
    years = payload.get("years")
    context = payload.get("context")
    subject_profile = payload.get("subject_profile")
    sender_email = payload.get("sender_email")

    # (a) Pool injection: only when the caller supplied no comps
    # of their own, and only once the pool can actually
    # benchmark (>= 2 entries in the declared micro-region).
    comps_used = payload.get("comps")
    pooled_count = 0
    if comps_used is None and subject_profile and subject_profile.get("micro_region"):
        pool = load_pool_comps(session, subject_profile["micro_region"])
        if len(pool) >= 2:
            comps_used = pool
            pooled_count = len(pool)

    # (b) The analysis itself.
    result = email_gateway.analyze_multiyear(
        years,
        context,
        subject_profile=subject_profile,
        comps=comps_used,
        comp_threshold_pct=payload.get("comp_threshold_pct"),
    )
    if pooled_count and "comp_benchmark" in result:
        result["comp_benchmark"]["source"] = "contributed_pool"
        result["comp_benchmark"]["pool_size"] = pooled_count

    # (c) Delta against a prior report, when one is named.
    prior_report_id = payload.get("prior_report_id")
    if prior_report_id:
        prior = get_report(session, prior_report_id)
        if prior is None:
            result["delta"] = {
                "status": "PRIOR_NOT_FOUND",
                "prior_report_id": prior_report_id,
            }
        else:
            result["delta"] = compute_delta(prior, result, payload)

    # (d) Persist — report, notifications, pool contribution,
    # ONE commit. Nothing in this step is caught: a failure
    # here is a loud rollback, not a half-written report.
    report = models.UnderwriteReport(
        door=door,
        sender=sender_email,
        subject_profile=subject_profile,
        input_hash=compute_input_hash(payload),
        engine_version=ENGINE_VERSION,
        request_payload=copy.deepcopy(payload),
        result=result,
        contribute_comps=bool(payload.get("contribute_comps")),
        claim_status="PENDING",
        created_at=int(time.time()),
    )
    session.add(report)
    session.flush()
    notifications: list = []
    if sender_email:
        notifications = compose_notifications(session, report, sender_email, result)
    record_pool_contribution(session, report, payload)
    session.commit()

    # (e) The NOI claim. Issuance never raises; its outcome is
    # recorded on the report and committed — and if THIS
    # commit fails, it propagates.
    claim_id, claim_status, claim_note = issue_noi_claim(
        session, report, result, subject_profile
    )
    report.claim_id = claim_id
    report.claim_status = claim_status
    report.claim_note = claim_note
    session.commit()

    # (f) The response: the analysis, its receipt, and the
    # first notification beat (QUEUED — composed, not sent).
    response: dict[str, Any] = {**result, "receipt": receipt_for(report)}
    if notifications:
        beat1 = notifications[0]
        response["notification_beat1"] = {
            "to": beat1.recipient,
            "subject": beat1.subject,
            "body": beat1.body,
            "status": "QUEUED",
        }
    return response


def persist_email_report(session, *, sender, subject, response, attachment_bytes):
    """Persist an email-door gateway assessment as a report.

    The email door's extraction is a labelled mock in this
    build, so: the stored result is the gateway response
    WITHOUT its pdf_base64 (the PDF accompanied the original
    response — the row says so), the request payload records
    only the attachment's byte count (never its content), and
    the claim fields are NOT_APPLICABLE with the reason stated
    — no claim is ever issued from mock-extracted data."""
    stored_result = copy.deepcopy(
        {k: v for k, v in (response or {}).items() if k != "pdf_base64"}
    )
    stored_result["pdf_in_original_response"] = True
    request_payload = {
        "subject": subject,
        "sender": sender,
        "attachment_bytes": attachment_bytes,
    }
    report = models.UnderwriteReport(
        door=DOOR_EMAIL,
        sender=sender,
        subject_profile=None,
        input_hash=compute_input_hash(request_payload),
        engine_version=ENGINE_VERSION,
        request_payload=request_payload,
        result=stored_result,
        contribute_comps=False,
        claim_status="NOT_APPLICABLE",
        claim_note=(
            "email-door extraction is a labelled mock in this "
            "build; claims are never issued from mock-extracted data"
        ),
        created_at=int(time.time()),
    )
    session.add(report)
    session.flush()
    notifications = compose_notifications(session, report, sender, stored_result)
    session.commit()
    beat1 = notifications[0]
    return {
        "receipt": receipt_for(report),
        "notification_beat1": {
            "to": beat1.recipient,
            "subject": beat1.subject,
            "body": beat1.body,
            "status": "QUEUED",
        },
    }
