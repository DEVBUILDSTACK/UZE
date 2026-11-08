"""NEAR AI inference (Day 4 interface, built Day 3): structural
tests against a fake InferenceClient, plus the bid-attach seam.

The fake implements the SDK's real protocol (async context manager,
chat.completions.create, verify_response) — the flow under test is
the same code the live key will run tomorrow. No test fabricates a
live attestation: the "ok" result here is a structural proof, and
analyze_property without a key must say "unavailable".
"""

from __future__ import annotations

import json

import inference
from test_intents import _post_spec


class _FakeMessage:
    content = json.dumps(
        {"operatingBudget": {"payroll": 1200000}, "confidence": 0.8}
    )


class _FakeChoice:
    message = _FakeMessage()


class _FakeCompletion:
    id = "chatcmpl-fake-1"
    choices = [_FakeChoice()]


class _FakeVerified:
    signature_kind = "gateway"


class _FakeCompletions:
    async def create(self, **kwargs):
        self.kwargs = kwargs
        return _FakeCompletion()


class _FakeChat:
    completions = _FakeCompletions()


class FakeClient:
    chat = _FakeChat()

    async def verify_response(self, completion_id):
        assert completion_id == "chatcmpl-fake-1"
        return _FakeVerified()


def test_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("NEARAI_API_KEY", raising=False)
    result = inference.analyze_property({"microRegionId": "miami-brickell"})
    assert result["status"] == "unavailable"
    assert "NEARAI_API_KEY" in result["reason"]


def test_structural_flow_with_fake_client(demo_fixture):
    result = inference.analyze_property(
        demo_fixture["spec"], client=FakeClient()
    )
    assert result["status"] == "ok"
    assert result["completionId"] == "chatcmpl-fake-1"
    assert result["analysis"]["operatingBudget"]["payroll"] == 1200000
    assert result["verification"]["signatureKind"] == "gateway"


def test_prompt_renders_the_spec(demo_fixture):
    prompt = inference.render_spec_as_prompt(demo_fixture["spec"])
    assert "340 doors" in prompt
    assert "miami-brickell" in prompt
    assert "Aloft" in prompt


def test_agent_bid_carries_inference_state(
    market_client, demo_fixture, monkeypatch
):
    monkeypatch.delenv("NEARAI_API_KEY", raising=False)
    spec = _post_spec(market_client, demo_fixture)
    body = {
        k: v for k, v in demo_fixture["bids"][1].items() if k != "bidderLabel"
    }
    body["intentId"] = spec["id"]
    resp = market_client.post("/api/v1/bids", json=body)
    assert resp.status_code == 201, resp.text
    attached = resp.json()["payload"]["inference"]
    # No key in the test environment: the honest state, attached.
    assert attached["status"] == "unavailable"

    human = {
        k: v for k, v in demo_fixture["bids"][0].items() if k != "bidderLabel"
    }
    human["intentId"] = spec["id"]
    resp = market_client.post("/api/v1/bids", json=human)
    assert "inference" not in resp.json()["payload"]
