"""Gateway trace opt-in (owner tap, 2026-11-13).

Pins: the endpoint is a labelled mock that records intent
only; the always-on tier is fixed by the endpoint, not the
caller; optional tiers validate against the four-tier
consent model verified from the NEAR AI Gateway data
policy; and opting out records no optional tiers.
"""

from __future__ import annotations

import json


def test_opt_in_records_intent_as_mock(client, tmp_path, monkeypatch):
    monkeypatch.setenv(
        "GATEWAY_TRACE_OPTIN_PATH", str(tmp_path / "optins.jsonl"))
    r = client.post("/api/v1/gateway/traces/opt-in", json={
        "account": "affiliate@example.com",
        "opt_in": True,
        "tiers": ["benchmark_generation"],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["mock"] is True and body["status"] == "mock_recorded"
    assert body["always_on"] == ["debugging_evaluation"]
    assert body["optional_tiers"] == ["benchmark_generation"]
    assert "no traces" in body["note"]
    rows = (tmp_path / "optins.jsonl").read_text().strip().splitlines()
    assert len(rows) == 1
    assert json.loads(rows[0])["record"]["opt_in"] is True


def test_opt_out_records_no_optional_tiers(client, tmp_path, monkeypatch):
    monkeypatch.setenv(
        "GATEWAY_TRACE_OPTIN_PATH", str(tmp_path / "optins.jsonl"))
    r = client.post("/api/v1/gateway/traces/opt-in", json={
        "account": "affiliate@example.com",
        "opt_in": False,
        "tiers": ["model_training"],
    })
    assert r.status_code == 200
    assert r.json()["optional_tiers"] == []


def test_opt_in_names_problems(client):
    r = client.post("/api/v1/gateway/traces/opt-in", json={
        "account": "", "tiers": ["everything_forever"],
    })
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "INSUFFICIENT_DATA"
    assert set(body["missing_fields"]) == {"account", "opt_in", "tiers"}
