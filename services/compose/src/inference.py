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

Transport + model rulings (DeepSeek, 2026-11-08, filed at
docs/hackathon/nov-2026/08-BUILD-CLARIFICATIONS-2026-11-08.md):

C-3 — Model fallback: if the configured model is not in the NEAR
AI Cloud catalog, retry with FALLBACK_MODEL (the UZD_NearHack-
verified Qwen model). The requirement is a verifiable enclave +
cryptographically attested response, not a specific model. A
fallback run records requestedModel + modelFallback on the result.

C-4 — Option A transport: the SDK's verified chat path pins TLS
over a direct transport, which cannot traverse this VM's egress
proxy (diagnosed 2026-11-07: a live SDK call from here fails with
APIConnectionError before any request is sent, while its plain
attestation fetches do traverse the proxy). When the SDK path
fails, completion runs over the OpenAI-compatible REST endpoint
through the proxy route, and the SDK's verify_response runs
alongside it against the REST completion id. The result records
transport "rest-proxy-route" and — only when verification actually
succeeded — the transportNote sentence the demo states verbatim.
If verification fails on the REST path, the result says so in its
verification field and carries NO transportNote: the claim is
never made unverified.

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
FALLBACK_MODEL = os.environ.get(
    "NEARAI_FALLBACK_MODEL", "Qwen/Qwen3.8-27B-abliterated"
)
REST_BASE_URL = os.environ.get(
    "NEARAI_REST_BASE_URL", "https://cloud-api.near.ai/v1"
)
TRANSPORT_NOTE = (
    "The HTTP transport traversed a proxy, but the attestation "
    "receipt and response signature were verified locally."
)
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


def parse_analysis_content(content: str) -> dict:
    try:
        parsed = json.loads(content or "")
        if isinstance(parsed, dict):
            return parsed
    except (ValueError, TypeError):
        pass
    return {"narrative": content}


def parse_analysis(completion) -> dict:
    content = completion.choices[0].message.content or ""
    return parse_analysis_content(content)


def _parse_rest_completion(payload: dict) -> tuple[Any, dict]:
    """(completion_id, analysis) from a REST chat-completion
    payload — the same capture set the SDK path produces."""
    completion_id = payload.get("id")
    content = ""
    choices = payload.get("choices") or []
    if choices:
        content = (choices[0].get("message") or {}).get("content") or ""
    return completion_id, parse_analysis_content(content)


def _is_model_error(exc: BaseException) -> bool:
    """True when a failure says the requested model is not in the
    catalog (C-3's fallback trigger) — as opposed to a transport,
    auth, or server failure, where retrying with another model
    would fail identically."""
    text = str(exc).lower()
    if "model" not in text:
        return False
    return any(
        marker in text
        for marker in (
            "not found",
            "not_found",
            "does not exist",
            "no such model",
            "unknown model",
        )
    )


async def _run(spec: dict, client, model: str = MODEL) -> dict:
    completion = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": render_spec_as_prompt(spec)},
        ],
    )
    verified = await client.verify_response(completion.id)
    return {
        "status": "ok",
        "model": model,
        "completionId": completion.id,
        "analysis": parse_analysis(completion),
        "verification": {
            "signatureKind": _to_plain(
                getattr(verified, "signature_kind", verified)
            ),
            "result": _to_plain(verified),
        },
    }


async def _sdk_attempt(spec: dict, api_key: str, model: str) -> dict:
    from nearai_inference_sdk import InferenceClient

    async with InferenceClient(
        api_key, e2ee=os.environ.get("NEARAI_E2EE") == "1"
    ) as client:
        result = await _run(spec, client, model)
    result["transport"] = "sdk"
    return result


async def _verify_with_sdk(api_key: str, completion_id: str):
    """Attestation verification alongside the REST path (C-4): the
    SDK's plain attestation fetches traverse this VM's proxy even
    though its pinned-TLS chat path does not."""
    from nearai_inference_sdk import InferenceClient

    async with InferenceClient(api_key, e2ee=False) as client:
        return await client.verify_response(completion_id)


async def _rest_completion(
    api_key: str, model: str, messages: list
) -> dict:
    """One chat completion over the OpenAI-compatible REST endpoint.
    httpx is given the proxy explicitly (trust_env=False): this
    VM's no_proxy entries crash httpx's env parsing, and the
    explicit proxy= route is the one verified to reach
    cloud-api.near.ai."""
    import httpx

    proxy = (
        os.environ.get("https_proxy")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("http_proxy")
        or os.environ.get("HTTP_PROXY")
    )
    kwargs: dict[str, Any] = {"timeout": 120.0, "trust_env": False}
    if proxy:
        kwargs["proxy"] = proxy
    async with httpx.AsyncClient(**kwargs) as http:
        resp = await http.post(
            f"{REST_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages},
        )
    if resp.status_code >= 400:
        raise RuntimeError(
            f"REST completion failed: HTTP {resp.status_code}: "
            f"{resp.text[:300]}"
        )
    return resp.json()


async def _rest_attempt(spec: dict, api_key: str, model: str) -> dict:
    payload = await _rest_completion(
        api_key,
        model,
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": render_spec_as_prompt(spec)},
        ],
    )
    completion_id, analysis = _parse_rest_completion(payload)
    result: dict[str, Any] = {
        "status": "ok",
        "model": model,
        "completionId": completion_id,
        "analysis": analysis,
        "transport": "rest-proxy-route",
    }
    try:
        verified = await _verify_with_sdk(api_key, completion_id)
        result["verification"] = {
            "signatureKind": _to_plain(
                getattr(verified, "signature_kind", verified)
            ),
            "result": _to_plain(verified),
        }
        # The C-4 sentence is attached only on verified success.
        result["transportNote"] = TRANSPORT_NOTE
    except Exception as exc:
        result["verification"] = {
            "status": "error",
            "reason": f"{type(exc).__name__}: {exc}",
        }
    return result


async def _run_with_real_client(spec: dict, api_key: str) -> dict:
    """SDK path first; REST path (C-4 Option A) when the SDK path
    fails; the C-3 fallback model is retried inside each path when
    — and only when — the failure is a model-catalog error. Every
    path failing raises with all attempts' reasons, which
    analyze_property reports honestly as status "error"."""
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
                result = await attempt(spec, api_key, model)
                if model != MODEL:
                    result["requestedModel"] = MODEL
                    result["modelFallback"] = True
                return result
            except Exception as exc:
                errors.append(
                    f"{label}/{model}: {type(exc).__name__}: {exc}"
                )
                if not _is_model_error(exc):
                    break
    raise RuntimeError(
        "all inference paths failed — " + " | ".join(errors)
    )


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
