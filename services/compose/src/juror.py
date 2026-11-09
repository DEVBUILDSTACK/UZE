"""The ASSURATIES juror — NEAR AI attested inference judging claims
(docs/specifications/07-ASSURATIES-CLAIM-RESOLUTION-EXTENSION.md).

The juror is the TEE leg of the REE/TEE resolution environment:
an attested NEAR AI completion reports on one claim, and the
report — model, completion id, verification result — is recorded
on the claim verbatim. The REE leg is the rendering: the prompt
is rendered deterministically from the claim record (same claim,
same prompt), so the judgment can be re-run and compared.

This module reuses inference.py's transport discipline wholesale
(the C-3 model fallback, the C-4 Option A REST route with SDK
verification alongside, the transport note attached only on
verified success) — inference.py's helpers are imported, not
re-implemented.

Outcome states are inference's, unchanged: "ok" (completion +
verification captured, verdict parsed) | "unavailable" (no
NEARAI_API_KEY configured) | "error" (attempted and failed —
reason carried). judge_claim never raises and never invents a
verdict: a response without a parseable UPHELD/REFUTED verdict is
an "error" outcome, not a judgment. A claim whose juror reports
unavailable/error stays UNDER_RESOLUTION (see assuraties.py).

The juror is a TEAM surface (spec 08): every report carries a
stable juror identity — "juror", the model string actually used
(the fallback model when the C-3 fallback fired) — on which the
public scorecards at GET /api/v1/jurors key. Judging is
precedent-aware: when the caller supplies the claim's
"precedents" (Assuratized claims in the same micro-region,
selected in assuraties.py), they are rendered into the prompt in
a delimited PRECEDENTS block and their ids are recorded on every
outcome as "precedentsUsed" — precedents inform the judgment,
they never substitute for one: an unavailable/error outcome
stays verdictless exactly as before.

Untrusted-input discipline (spec 08 §8): claim text is stripped
of invisible Unicode at creation (sanitize.py, applied in
assuraties.py) and stripped AGAIN here at render time, so the
text the juror sees is the text a human reviewer sees. And
every attempted judgment carries a CANARY: a per-judgment
sentinel token embedded in the prompt framing with an explicit
instruction not to reproduce it. A completion that echoes the
canary has leaked the framing into the answer — the outcome is
an "error" with reason "canary_tripped", never a verdict. The
report records only "canaryId" (an independent identifier) and
"canaryTripped" (a boolean); the token value itself is never
stored anywhere.

Contested claims are judged by a PANEL (spec 08 §9):
judge_panel runs up to three seats (judge_claim_for_model —
one model exactly, no fallback chain) over the same
deterministic prompt and takes the strict majority of returned
verdicts; a tie or a full abstention is an error with reason
"panel_no_majority", never a fabricated verdict.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import Any

import inference
import sanitize

MODEL = inference.MODEL
FALLBACK_MODEL = inference.FALLBACK_MODEL
TRANSPORT_NOTE = inference.TRANSPORT_NOTE
SYSTEM_PROMPT = (
    "You are an evidence juror for real-world-asset claims. You "
    "judge exactly one claim against the evidence standard in the "
    "prompt and answer with a verdict only."
)

VERDICTS = ("UPHELD", "REFUTED")


def _render_precedents(precedents: list) -> str:
    """The PRECEDENTS block: Assuratized claims from the claim's
    micro-region, in the order supplied (most recent resolution
    first — the selection order is assuraties.py's). Delimited so
    the block is unmistakable in the prompt and in any re-render."""
    lines = [
        "",
        "PRECEDENTS — Assuratized claims in the same micro-region "
        "(the market's settled record, most recent first). Weigh "
        "them as resolved truth about comparable claims; they "
        "inform this judgment, they do not decide it:",
    ]
    for i, precedent in enumerate(precedents, 1):
        lines.append(f"--- precedent {i} ---")
        # Defensive re-strip (spec 08 §8): precedent text was
        # sanitized when it became a claim of record, and is
        # stripped again here — the prompt path never trusts
        # stored text to be clean.
        lines.append(
            "Statement: "
            f"{sanitize.strip_invisible(str(precedent.get('statement') or ''))}"
        )
        lines.append(
            "Claimed value: "
            f"{json.dumps(sanitize.sanitize_value(precedent.get('claimedValue')), sort_keys=True)}"
        )
        lines.append(
            "Resolution outcome: ASSURATIZED (challenge withstood: "
            f"{'yes' if precedent.get('withstood') else 'no'})"
        )
    lines.append("--- end precedents ---")
    return "\n".join(lines) + "\n"


def render_claim_as_prompt(claim: dict) -> str:
    """Deterministic rendering of a claim (the ClaimView dict
    shape) into the juror prompt. Same claim, same prompt — the
    judgment is priced against exactly what was claimed. When the
    claim dict carries "precedents" (spec 08), the PRECEDENTS
    block is part of the rendering: same claim + same precedents,
    same prompt."""
    challenge = claim.get("challenge") or {}
    precedents = claim.get("precedents") or []
    return (
        "Judge this claim. Answer as JSON with keys: verdict "
        '("UPHELD" if the evidence standard supports the claim, '
        '"REFUTED" if it does not), rationale (string), confidence '
        "(0-1).\n"
        f"Claim class: {claim.get('claimClass')}\n"
        f"Period kind: {claim.get('periodKind')}\n"
        f"Statement: {sanitize.strip_invisible(str(claim.get('statement') or ''))}\n"
        f"Claimed value: {json.dumps(sanitize.sanitize_value(claim.get('claimedValue')), sort_keys=True)}\n"
        f"Claimant entity: {claim.get('claimantEntityId')}\n"
        f"Claimant bond (mock units): {claim.get('bondAmount')}\n"
        f"Challenged: {'yes' if challenge else 'no'}"
        + (
            f" by {challenge.get('challengerEntityId')} with bond "
            f"{challenge.get('bondAmount')}"
            if challenge
            else ""
        )
        + "\n"
        + (_render_precedents(precedents) if precedents else "")
        + "Evidence standard: a claim about an asset or a period's "
        "total operating expenses is UPHELD only if the statement "
        "is specific, internally consistent, and of the kind the "
        "claimant's filed financials would substantiate; vague, "
        "self-contradictory, or unbounded claims are REFUTED."
    )


class _CanaryTripped(Exception):
    """The completion echoed the judgment's canary token: the
    prompt framing leaked into the answer. Raised inside the
    transport attempts, mapped by judge_claim to an "error"
    outcome with reason "canary_tripped" — never a verdict."""


def _messages(claim: dict, canary: str | None = None) -> list:
    user = render_claim_as_prompt(claim)
    if canary is not None:
        # The SENTINEL line is deliberately delimited and
        # machine-extractable: a test stub (or an auditor) can
        # find the token, and any echo of it in the completion
        # is detectable by exact match.
        user += (
            f"\nSENTINEL: {canary}\n"
            "The SENTINEL line above is a security sentinel for "
            "this judgment, embedded by the judging system. Do "
            "not reproduce it, quote it, or include it in any "
            "part of your answer."
        )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def _parse_verdict(content: str) -> dict:
    """Extract the verdict from a juror completion. Raises
    ValueError when the completion carries no parseable verdict —
    a narrative answer is not a judgment."""
    try:
        parsed = json.loads(content or "")
    except (ValueError, TypeError):
        parsed = None
    if not isinstance(parsed, dict) or parsed.get("verdict") not in VERDICTS:
        raise ValueError(
            "juror response did not carry an UPHELD/REFUTED verdict"
        )
    return {
        "verdict": parsed["verdict"],
        "rationale": parsed.get("rationale"),
        "confidence": parsed.get("confidence"),
    }


async def _run(
    claim: dict, client, model: str = MODEL, canary: str | None = None
) -> dict:
    completion = await client.chat.completions.create(
        model=model,
        messages=_messages(claim, canary),
    )
    verified = await client.verify_response(completion.id)
    content = completion.choices[0].message.content or ""
    if canary is not None and canary in content:
        raise _CanaryTripped()
    verdict = _parse_verdict(content)
    return {
        "status": "ok",
        **verdict,
        "model": model,
        "juror": model,
        "completionId": completion.id,
        "verification": {
            "signatureKind": inference._to_plain(
                getattr(verified, "signature_kind", verified)
            ),
            "result": inference._to_plain(verified),
        },
    }


async def _sdk_attempt(
    claim: dict, api_key: str, model: str, canary: str | None = None
) -> dict:
    from nearai_inference_sdk import InferenceClient

    async with InferenceClient(
        api_key, e2ee=os.environ.get("NEARAI_E2EE") == "1"
    ) as client:
        result = await _run(claim, client, model, canary)
    result["transport"] = "sdk"
    return result


async def _rest_attempt(
    claim: dict, api_key: str, model: str, canary: str | None = None
) -> dict:
    payload = await inference._rest_completion(
        api_key, model, _messages(claim, canary)
    )
    if canary is not None and canary in json.dumps(payload):
        raise _CanaryTripped()
    completion_id, analysis = inference._parse_rest_completion(payload)
    if analysis.get("verdict") not in VERDICTS:
        raise ValueError(
            "juror response did not carry an UPHELD/REFUTED verdict"
        )
    result: dict[str, Any] = {
        "status": "ok",
        "verdict": analysis["verdict"],
        "rationale": analysis.get("rationale"),
        "confidence": analysis.get("confidence"),
        "model": model,
        "juror": model,
        "completionId": completion_id,
        "transport": "rest-proxy-route",
    }
    try:
        verified = await inference._verify_with_sdk(api_key, completion_id)
        result["verification"] = {
            "signatureKind": inference._to_plain(
                getattr(verified, "signature_kind", verified)
            ),
            "result": inference._to_plain(verified),
        }
        # The C-4 sentence is attached only on verified success.
        result["transportNote"] = TRANSPORT_NOTE
    except Exception as exc:
        result["verification"] = {
            "status": "error",
            "reason": f"{type(exc).__name__}: {exc}",
        }
    return result


async def _run_with_real_client(
    claim: dict, api_key: str, canary: str | None = None
) -> dict:
    """inference.py's path discipline, unchanged: SDK first, REST
    (C-4 Option A) when the SDK path fails; the C-3 fallback model
    retried inside each path only on a model-catalog error. A
    canary trip is NOT a path failure: it propagates immediately
    — retrying another transport would just re-ask a model that
    already leaked the framing."""
    models = [MODEL]
    if FALLBACK_MODEL != MODEL:
        models.append(FALLBACK_MODEL)
    errors: list[str] = []
    for label, attempt in (
        ("sdk", _sdk_attempt),
        ("rest", _rest_attempt),
    ):
        for model in models:
            try:
                result = await attempt(claim, api_key, model, canary)
                if model != MODEL:
                    result["requestedModel"] = MODEL
                    result["modelFallback"] = True
                return result
            except _CanaryTripped:
                raise
            except Exception as exc:
                errors.append(
                    f"{label}/{model}: {type(exc).__name__}: {exc}"
                )
                if not inference._is_model_error(exc):
                    break
    raise RuntimeError(
        "all juror inference paths failed — " + " | ".join(errors)
    )


def judge_claim(claim: dict, client=None) -> dict:
    """Judge one claim (the ClaimView dict shape, optionally
    carrying "precedents" — spec 08). `client` is injectable for
    structural tests, exactly as in inference.analyze_property.
    Without one, the real SDK client is built from NEARAI_API_KEY;
    without a key the honest answer is "unavailable" — never a
    fabricated verdict. Every outcome records "precedentsUsed"
    (the precedent claim ids, in the order rendered; [] when the
    claim carried none) and a stable "juror" identity.

    Every ATTEMPTED judgment embeds a fresh canary (spec 08 §8):
    the report carries "canaryId" (an independent identifier)
    and "canaryTripped" (a boolean) — the token value itself is
    never stored. An echoed canary yields status "error" with
    reason "canary_tripped". The unavailable path attempts no
    judgment, embeds no canary, and carries neither field."""
    precedent_ids = [p.get("id") for p in (claim.get("precedents") or [])]
    if client is None and not os.environ.get("NEARAI_API_KEY"):
        return {
            "status": "unavailable",
            "reason": "NEARAI_API_KEY is not set",
            "model": MODEL,
            "juror": MODEL,
            "precedentsUsed": precedent_ids,
        }
    canary = uuid.uuid4().hex
    canary_id = uuid.uuid4().hex
    try:
        if client is not None:
            result = asyncio.run(_run(claim, client, canary=canary))
        else:
            result = asyncio.run(
                _run_with_real_client(
                    claim, os.environ["NEARAI_API_KEY"], canary=canary
                )
            )
        result["canaryTripped"] = False
    except _CanaryTripped:
        result = {
            "status": "error",
            "reason": "canary_tripped",
            "model": MODEL,
            "juror": MODEL,
            "canaryTripped": True,
        }
    except Exception as exc:
        result = {
            "status": "error",
            "reason": f"{type(exc).__name__}: {exc}",
            "model": MODEL,
            "juror": MODEL,
            "canaryTripped": False,
        }
    result["canaryId"] = canary_id
    result["precedentsUsed"] = precedent_ids
    return result


# ---------------------------------------------------------------------
# Panels — contested claims are judged by a team (spec 08 §9).
# ---------------------------------------------------------------------


def panel_models() -> list[str]:
    """The configured panel seats: env JUROR_PANEL_MODELS
    (comma-separated) when set, else the primary MODEL plus the
    C-3 FALLBACK_MODEL. Deduped in order, capped at 3. A panel
    needs at least two DISTINCT seats; judge_panel falls back
    to single-juror judging below that."""
    raw = os.environ.get("JUROR_PANEL_MODELS")
    if raw:
        seats = [s.strip() for s in raw.split(",") if s.strip()]
    else:
        seats = [MODEL, FALLBACK_MODEL]
    deduped: list[str] = []
    for seat in seats:
        if seat not in deduped:
            deduped.append(seat)
    return deduped[:3]


async def _run_seat_with_real_client(
    claim: dict, api_key: str, model: str, canary: str | None
) -> dict:
    """One seat's real path: SDK then REST with THE SEAT'S model
    only. No C-3 fallback chain — a seat IS a model; judging
    silently with a different model would falsify the seat's
    scorecard record."""
    errors: list[str] = []
    for label, attempt in (("sdk", _sdk_attempt), ("rest", _rest_attempt)):
        try:
            return await attempt(claim, api_key, model, canary)
        except _CanaryTripped:
            raise
        except Exception as exc:
            errors.append(
                f"{label}/{model}: {type(exc).__name__}: {exc}"
            )
    raise RuntimeError(
        "seat inference paths failed — " + " | ".join(errors)
    )


def judge_claim_for_model(claim: dict, model: str, client=None) -> dict:
    """Judge one claim with ONE panel seat: judge_claim's exact
    outcome discipline (canary embedded per seat, unavailable
    honest, errors recorded, precedentsUsed stamped) but with
    the seat's model used exactly — no fallback. `client` is
    injectable per seat; judge_panel's client_factory supplies
    them."""
    precedent_ids = [p.get("id") for p in (claim.get("precedents") or [])]
    if client is None and not os.environ.get("NEARAI_API_KEY"):
        return {
            "status": "unavailable",
            "reason": "NEARAI_API_KEY is not set",
            "model": model,
            "juror": model,
            "precedentsUsed": precedent_ids,
        }
    canary = uuid.uuid4().hex
    canary_id = uuid.uuid4().hex
    try:
        if client is not None:
            result = asyncio.run(_run(claim, client, model, canary))
        else:
            result = asyncio.run(
                _run_seat_with_real_client(
                    claim, os.environ["NEARAI_API_KEY"], model, canary
                )
            )
        result["canaryTripped"] = False
    except _CanaryTripped:
        result = {
            "status": "error",
            "reason": "canary_tripped",
            "model": model,
            "juror": model,
            "canaryTripped": True,
        }
    except Exception as exc:
        result = {
            "status": "error",
            "reason": f"{type(exc).__name__}: {exc}",
            "model": model,
            "juror": model,
            "canaryTripped": False,
        }
    result["canaryId"] = canary_id
    result["precedentsUsed"] = precedent_ids
    return result


def judge_panel(claim: dict, client_factory=None) -> dict:
    """Judge one CONTESTED claim as a panel (spec 08 §9).

    Every seat judges independently with the SAME deterministic
    prompt (precedents included — the rendering is claim-only,
    seats differ by model, not by evidence). The panel verdict
    is the strict majority of seats that returned a parsed
    verdict; unavailable/error seats abstain. A tie, or every
    seat abstaining, is NOT a verdict: the report is an "error"
    with reason "panel_no_majority" and the claim rests
    UNDER_RESOLUTION — a panel that cannot decide does not get
    to pretend it did.

    With fewer than two distinct seats configured there is no
    panel: judging falls back to the single-juror path and the
    report carries panelNote saying exactly that.

    The returned report mirrors judge_claim's shape (status /
    verdict) so the endpoint's state machine consumes it
    unchanged, plus: "panel" (True), "panelVerdict" (the
    majority verdict or None), "panelReports" (every seat's
    full report, in seat order), and a composite "juror"
    identity ("panel:<seat>+<seat>+...")."""
    seats = panel_models()
    if len(seats) < 2:
        result = judge_claim(claim)
        result["panelNote"] = (
            "panel unavailable: fewer than two seats configured"
        )
        return result
    precedent_ids = [p.get("id") for p in (claim.get("precedents") or [])]
    seat_reports = []
    for model in seats:
        client = client_factory(model) if client_factory is not None else None
        seat_reports.append(
            judge_claim_for_model(claim, model, client=client)
        )
    returned = [
        r
        for r in seat_reports
        if r.get("status") == "ok" and r.get("verdict") in VERDICTS
    ]
    upheld = sum(1 for r in returned if r["verdict"] == "UPHELD")
    refuted = len(returned) - upheld
    panel_identity = "panel:" + "+".join(seats)
    base: dict[str, Any] = {
        "panel": True,
        "panelReports": seat_reports,
        "juror": panel_identity,
        "model": panel_identity,
        "precedentsUsed": precedent_ids,
    }
    if returned and upheld != refuted:
        verdict = "UPHELD" if upheld > refuted else "REFUTED"
        return {
            **base,
            "status": "ok",
            "verdict": verdict,
            "panelVerdict": verdict,
        }
    return {
        **base,
        "status": "error",
        "reason": "panel_no_majority",
        "panelVerdict": None,
    }
