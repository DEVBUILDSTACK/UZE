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
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import inference

MODEL = inference.MODEL
FALLBACK_MODEL = inference.FALLBACK_MODEL
TRANSPORT_NOTE = inference.TRANSPORT_NOTE
SYSTEM_PROMPT = (
    "You are an evidence juror for real-world-asset claims. You "
    "judge exactly one claim against the evidence standard in the "
    "prompt and answer with a verdict only."
)

VERDICTS = ("UPHELD", "REFUTED")


def render_claim_as_prompt(claim: dict) -> str:
    """Deterministic rendering of a claim (the ClaimView dict
    shape) into the juror prompt. Same claim, same prompt — the
    judgment is priced against exactly what was claimed."""
    challenge = claim.get("challenge") or {}
    return (
        "Judge this claim. Answer as JSON with keys: verdict "
        '("UPHELD" if the evidence standard supports the claim, '
        '"REFUTED" if it does not), rationale (string), confidence '
        "(0-1).\n"
        f"Claim class: {claim.get('claimClass')}\n"
        f"Period kind: {claim.get('periodKind')}\n"
        f"Statement: {claim.get('statement')}\n"
        f"Claimed value: {json.dumps(claim.get('claimedValue'), sort_keys=True)}\n"
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
        "Evidence standard: a claim about an asset or a period's "
        "total operating expenses is UPHELD only if the statement "
        "is specific, internally consistent, and of the kind the "
        "claimant's filed financials would substantiate; vague, "
        "self-contradictory, or unbounded claims are REFUTED."
    )


def _messages(claim: dict) -> list:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": render_claim_as_prompt(claim)},
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


async def _run(claim: dict, client, model: str = MODEL) -> dict:
    completion = await client.chat.completions.create(
        model=model,
        messages=_messages(claim),
    )
    verified = await client.verify_response(completion.id)
    content = completion.choices[0].message.content or ""
    verdict = _parse_verdict(content)
    return {
        "status": "ok",
        **verdict,
        "model": model,
        "completionId": completion.id,
        "verification": {
            "signatureKind": inference._to_plain(
                getattr(verified, "signature_kind", verified)
            ),
            "result": inference._to_plain(verified),
        },
    }


async def _sdk_attempt(claim: dict, api_key: str, model: str) -> dict:
    from nearai_inference_sdk import InferenceClient

    async with InferenceClient(
        api_key, e2ee=os.environ.get("NEARAI_E2EE") == "1"
    ) as client:
        result = await _run(claim, client, model)
    result["transport"] = "sdk"
    return result


async def _rest_attempt(claim: dict, api_key: str, model: str) -> dict:
    payload = await inference._rest_completion(
        api_key, model, _messages(claim)
    )
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


async def _run_with_real_client(claim: dict, api_key: str) -> dict:
    """inference.py's path discipline, unchanged: SDK first, REST
    (C-4 Option A) when the SDK path fails; the C-3 fallback model
    retried inside each path only on a model-catalog error."""
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
                result = await attempt(claim, api_key, model)
                if model != MODEL:
                    result["requestedModel"] = MODEL
                    result["modelFallback"] = True
                return result
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
    """Judge one claim (the ClaimView dict shape). `client` is
    injectable for structural tests, exactly as in
    inference.analyze_property. Without one, the real SDK client
    is built from NEARAI_API_KEY; without a key the honest answer
    is "unavailable" — never a fabricated verdict."""
    try:
        if client is not None:
            return asyncio.run(_run(claim, client))
        api_key = os.environ.get("NEARAI_API_KEY")
        if not api_key:
            return {
                "status": "unavailable",
                "reason": "NEARAI_API_KEY is not set",
                "model": MODEL,
            }
        return asyncio.run(_run_with_real_client(claim, api_key))
    except Exception as exc:
        return {
            "status": "error",
            "reason": f"{type(exc).__name__}: {exc}",
            "model": MODEL,
        }
