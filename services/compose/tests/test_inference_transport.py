"""C-3 / C-4 rulings (DeepSeek, 2026-11-08): model fallback and
the Option A REST transport, tested at the network boundary.

The attempts (`_sdk_attempt` / `_rest_attempt`) and the REST/verify
helpers are the seams — the same posture as test_inference.py's
FakeClient. No test fabricates a live attestation: fakes stand at
the boundary, and the properties under test are the orchestration
decisions (which path runs, which model is retried, what the
receipt records, and when the C-4 transportNote may be claimed).
"""

from __future__ import annotations

import asyncio
import json

import inference


class _ModelNotFound(Exception):
    pass


class _ConnError(Exception):
    pass


def _ok_result(model):
    return {
        "status": "ok",
        "model": model,
        "completionId": "chatcmpl-x",
        "analysis": {},
        "verification": {"signatureKind": "gateway"},
    }


def _attempts(monkeypatch, sdk_behavior, rest_behavior, calls):
    async def fake_sdk(spec, api_key, model):
        calls.append(("sdk", model))
        outcome = sdk_behavior(model)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def fake_rest(spec, api_key, model):
        calls.append(("rest", model))
        outcome = rest_behavior(model)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(inference, "_sdk_attempt", fake_sdk)
    monkeypatch.setattr(inference, "_rest_attempt", fake_rest)


def _run_live(monkeypatch, spec=None):
    monkeypatch.setenv("NEARAI_API_KEY", "test-key-not-real")
    return inference.analyze_property(spec or {"microRegionId": "x"})


def test_model_error_detection():
    assert inference._is_model_error(
        _ModelNotFound("model glm-5.3-flash not found")
    )
    assert inference._is_model_error(
        RuntimeError(
            "REST completion failed: HTTP 404: "
            '{"error": {"code": "model_not_found"}}'
        )
    )
    assert not inference._is_model_error(
        _ConnError("APIConnectionError: Connection error.")
    )
    assert not inference._is_model_error(
        RuntimeError("REST completion failed: HTTP 500: boom")
    )


def test_parse_rest_completion():
    payload = {
        "id": "chatcmpl-rest-1",
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {"operatingBudget": {"payroll": 5}}
                    )
                }
            }
        ],
    }
    completion_id, analysis = inference._parse_rest_completion(payload)
    assert completion_id == "chatcmpl-rest-1"
    assert analysis["operatingBudget"]["payroll"] == 5

    _, narrative = inference._parse_rest_completion(
        {"id": "c2", "choices": [{"message": {"content": "plain"}}]}
    )
    assert narrative == {"narrative": "plain"}


def test_sdk_connection_failure_falls_to_rest(monkeypatch):
    calls: list = []
    _attempts(
        monkeypatch,
        lambda model: _ConnError("APIConnectionError: Connection error."),
        lambda model: _ok_result(model),
        calls,
    )
    result = _run_live(monkeypatch)
    assert result["status"] == "ok"
    # Connection failure is not a model error: no model retry on
    # the SDK path — straight to REST with the primary model.
    assert calls == [("sdk", inference.MODEL), ("rest", inference.MODEL)]


def test_model_error_retries_fallback_on_sdk(monkeypatch):
    calls: list = []

    def sdk(model):
        if model == inference.MODEL:
            return _ModelNotFound(f"model {model} not found")
        return _ok_result(model)

    _attempts(monkeypatch, sdk, lambda model: _ok_result(model), calls)
    result = _run_live(monkeypatch)
    assert result["status"] == "ok"
    assert result["model"] == inference.FALLBACK_MODEL
    assert result["requestedModel"] == inference.MODEL
    assert result["modelFallback"] is True
    assert calls == [
        ("sdk", inference.MODEL),
        ("sdk", inference.FALLBACK_MODEL),
    ]


def test_all_paths_fail_reports_every_attempt(monkeypatch):
    calls: list = []
    _attempts(
        monkeypatch,
        lambda model: _ConnError("sdk down"),
        lambda model: _ConnError("rest down"),
        calls,
    )
    result = _run_live(monkeypatch)
    assert result["status"] == "error"
    assert "sdk down" in result["reason"]
    assert "rest down" in result["reason"]


class _FakeVerified:
    signature_kind = "provider_tee"


def _rest_payload():
    return {
        "id": "chatcmpl-rest-9",
        "choices": [
            {
                "message": {
                    "content": json.dumps({"confidence": 0.7})
                }
            }
        ],
    }


def test_rest_attempt_attaches_note_only_when_verified(monkeypatch):
    async def fake_completion(api_key, model, messages):
        return _rest_payload()

    async def fake_verify(api_key, completion_id):
        assert completion_id == "chatcmpl-rest-9"
        return _FakeVerified()

    monkeypatch.setattr(inference, "_rest_completion", fake_completion)
    monkeypatch.setattr(inference, "_verify_with_sdk", fake_verify)
    result = asyncio.run(
        inference._rest_attempt({}, "k", inference.MODEL)
    )
    assert result["status"] == "ok"
    assert result["transport"] == "rest-proxy-route"
    assert result["verification"]["signatureKind"] == "provider_tee"
    assert result["transportNote"] == inference.TRANSPORT_NOTE


def test_rest_attempt_never_claims_note_when_verify_fails(monkeypatch):
    async def fake_completion(api_key, model, messages):
        return _rest_payload()

    async def fake_verify(api_key, completion_id):
        raise RuntimeError("attestation fetch failed")

    monkeypatch.setattr(inference, "_rest_completion", fake_completion)
    monkeypatch.setattr(inference, "_verify_with_sdk", fake_verify)
    result = asyncio.run(
        inference._rest_attempt({}, "k", inference.MODEL)
    )
    assert result["status"] == "ok"
    assert result["verification"]["status"] == "error"
    assert "transportNote" not in result
