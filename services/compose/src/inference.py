"""NEAR AI inference for the composition layer (Sprint 1.5, Day 4
interface — built Day 3 evening per DeepSeek's pre-flight directive:
write the code against the SDK now, swap the real key in when it
lands).

Filed interface (02-SPRINT-1.5-PLAN.md Day 4): analyze_property(spec)
runs an attested chat completion — system prompt "You are a CRE
operating cost analyst." — captures completion.id, the attestation
receipt, and the verification result, and the result attaches to the
agent's bid payload.

One correction to the filed snippet, logged for DeepSeek: the
installed nearai-inference-sdk 0.2.1 has no `NearAIClient`. Its real
surface is `InferenceClient` (async context manager;
client.chat.completions.create; client.verify_response(id) ->
result with .signature_kind) — the same surface the UZD_NearHack
client was built and verified against on 2026-11-07. This module
follows the real surface and keeps the filed function name, prompts,
and capture set.

Outcome states: "ok" (completion + verification captured) |
"unavailable" (no NEARAI_API_KEY configured) | "error" (the call was
attempted and failed — reason carried). analyze_property never
raises: a bid must not fail because inference is down.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

MODEL = os.environ.get("NEARAI_MODEL", "glm-5.3-flash")
SYSTEM_PROMPT = "You are a CRE operating cost analyst."


def render_spec_as_prompt(spec: dict) -> str:
    """Deterministic rendering of a spec (the SpecView dict shape)
    into the analyst prompt. Same input, same prompt — the analysis
    is priced against exactly what the marketplace posted."""
    asset = spec.get("assetContext", {})
    deliverable = spec.get("deliverable", {})
    return (
        "Analyze this commercial real estate specification and "
        "produce the deliverable as JSON with keys: operatingBudget "
        "(object of annual cost lines), pmSpec (object), assumptions "
        "(list of strings), confidence (0-1).\n"
        f"Micro-region: {spec.get('microRegionId')}\n"
        f"Domain: {spec.get('domain')} / work product: "
        f"{spec.get('workProduct')}\n"
        f"Property: {asset.get('propertyType')}, "
        f"{asset.get('doorCount')} doors, brand: "
        f"{asset.get('brandAffiliation')}, stage: "
        f"{asset.get('acquisitionStage')}\n"
        f"Deliverable: {json.dumps(deliverable)}\n"
        f"Budget window (USDC): {spec.get('budgetMinUsdc')}-"
        f"{spec.get('budgetMaxUsdc')}; on-site days: "
        f"{spec.get('onSiteDays')}, remote days: "
        f"{spec.get('remoteDays')}"
    )


def _to_plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def parse_analysis(completion) -> dict:
    content = completion.choices[0].message.content or ""
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except (ValueError, TypeError):
        pass
    return {"narrative": content}


async def _run(spec: dict, client) -> dict:
    completion = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": render_spec_as_prompt(spec)},
        ],
    )
    verified = await client.verify_response(completion.id)
    return {
        "status": "ok",
        "model": MODEL,
        "completionId": completion.id,
        "analysis": parse_analysis(completion),
        "verification": {
            "signatureKind": _to_plain(
                getattr(verified, "signature_kind", verified)
            ),
            "result": _to_plain(verified),
        },
    }


async def _run_with_real_client(spec: dict, api_key: str) -> dict:
    from nearai_inference_sdk import InferenceClient

    # VM transport note (diagnosed 2026-11-07, Day 4 opening item):
    # the SDK's verified chat path pins TLS over a direct transport,
    # which cannot traverse this VM's egress proxy — a live call
    # from here fails with APIConnectionError before any request is
    # sent (its plain attestation fetches do traverse the proxy).
    # analyze_property reports that honestly as status "error". The
    # Day 4 options are a direct-egress runtime for the inference
    # call, or completion over the OpenAI-compatible REST endpoint
    # (proxy-reachable) with SDK attestation verification alongside.
    async with InferenceClient(
        api_key, e2ee=os.environ.get("NEARAI_E2EE") == "1"
    ) as client:
        return await _run(spec, client)


def analyze_property(spec: dict, client=None) -> dict:
    """The filed Day 4 entry point. `client` is injectable for
    structural tests (any object with the InferenceClient protocol:
    async context manager + chat.completions.create +
    verify_response). Without one, the real SDK client is built from
    NEARAI_API_KEY; without a key, the honest answer is
    "unavailable" — never a fabricated analysis."""
    try:
        if client is not None:
            return asyncio.run(_run(spec, client))
        api_key = os.environ.get("NEARAI_API_KEY")
        if not api_key:
            return {
                "status": "unavailable",
                "reason": "NEARAI_API_KEY is not set",
                "model": MODEL,
            }
        return asyncio.run(_run_with_real_client(spec, api_key))
    except Exception as exc:
        return {
            "status": "error",
            "reason": f"{type(exc).__name__}: {exc}",
            "model": MODEL,
        }
