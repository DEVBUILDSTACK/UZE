"""UZE Research — the white-labeled research channel
(owner directive, 2026-11-13).

The provider transport is stubbed at research._provider_post
(the live upstream was verified separately against the real
API the same day); everything else runs for real: the x402
v2 gate, the normalization, the white-label discipline, and
the EventLog audit rows on both doors (API + email gateway).

Pins:
  - unconfigured provider -> 503 RESEARCH_NOT_CONFIGURED;
    unconfigured pricing -> 503 PRICING_NOT_CONFIGURED
    (nothing invented, either way);
  - validation precedes payment (empty query -> 422
    MISSING_FIELD naming the field and the accepted shape);
  - no signature -> 402 quoting Base + Solana; a bad
    signature -> 402; the mock-profile signature -> 200
    with a PAYMENT-RESPONSE receipt;
  - no provider name, request id, or cost field ever
    appears in a response payload (white-label rule);
  - the financial endpoint forces the financial category;
  - the email door runs the same search and logs door=email.
"""

from __future__ import annotations

import base64
import json

import db
import models
import research
import x402

ENV = {
    "X402_SKU_AMOUNT_ATOMIC": "5000000",
    "X402_PAYTO_BASE": "0x1111111111111111111111111111111111111111",
    "X402_PAYTO_SOLANA": "SoLanaPayTo1111111111111111111111111111",
    "EXA_API_KEY": "test-key-not-a-real-credential",
}

RAW_SEARCH = {
    "requestId": "req-abc-123",
    "results": [
        {
            "id": "https://cdn.sample.test/a",
            "title": "Hotel earnings beat",
            "url": "https://cdn.sample.test/a",
            "publishedDate": "2026-11-01T00:00:00.000Z",
            "author": "Wire",
            "score": 0.91,
            "text": "Revenue grew.",
        },
        {
            "id": "https://cdn.sample.test/b",
            "title": "Second result",
            "url": "https://cdn.sample.test/b",
            "publishedDate": None,
            "score": 0.5,
        },
    ],
    "costDollars": {"total": 0.007},
}


def _configure(monkeypatch):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)


def _stub_provider(monkeypatch, captured: dict | None = None):
    def fake_post(path, payload):
        if captured is not None:
            captured["path"] = path
            captured["payload"] = payload
        return RAW_SEARCH

    monkeypatch.setattr(research, "_provider_post", fake_post)


def _pay_header(payer="agent@uze.test"):
    return x402.build_mock_signature_header(
        payer=payer,
        network=x402.BASE_NETWORK,
        amount=ENV["X402_SKU_AMOUNT_ATOMIC"],
        pay_to=ENV["X402_PAYTO_BASE"],
    )


def _research_events():
    session = db.session()
    try:
        rows = (
            session.query(models.EventLog)
            .filter(models.EventLog.event_type == "research.metered_call")
            .all()
        )
        return [r.payload for r in rows]
    finally:
        session.close()


def test_unconfigured_provider_is_a_labelled_503(client, monkeypatch):
    _configure(monkeypatch)
    monkeypatch.delenv("EXA_API_KEY")
    r = client.post("/api/v1/research/search", json={"query": "hotels"})
    assert r.status_code == 503
    assert r.json()["error"] == "RESEARCH_NOT_CONFIGURED"


def test_unconfigured_pricing_is_a_labelled_503(client, monkeypatch):
    _configure(monkeypatch)
    for k in ("X402_SKU_AMOUNT_ATOMIC", "X402_PAYTO_BASE", "X402_PAYTO_SOLANA"):
        monkeypatch.delenv(k)
    r = client.post("/api/v1/research/search", json={"query": "hotels"})
    assert r.status_code == 503
    assert r.json()["error"] == "PRICING_NOT_CONFIGURED"


def test_validation_precedes_payment(client, monkeypatch):
    _configure(monkeypatch)
    r = client.post("/api/v1/research/search", json={"query": "  "})
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "MISSING_FIELD"
    assert body["field"] == "query"
    assert "accepted_shape" in body


def test_no_signature_quotes_base_and_solana(client, monkeypatch):
    _configure(monkeypatch)
    _stub_provider(monkeypatch)
    r = client.post("/api/v1/research/search", json={"query": "hotels"})
    assert r.status_code == 402
    required = json.loads(base64.b64decode(r.headers["PAYMENT-REQUIRED"]))
    networks = {a["network"] for a in required["accepts"]}
    assert networks == {x402.BASE_NETWORK, x402.SOLANA_NETWORK}


def test_bad_signature_is_refused(client, monkeypatch):
    _configure(monkeypatch)
    _stub_provider(monkeypatch)
    r = client.post(
        "/api/v1/research/search",
        json={"query": "hotels"},
        headers={"PAYMENT-SIGNATURE": base64.b64encode(b"{}").decode()},
    )
    assert r.status_code == 402
    assert "invalid PAYMENT-SIGNATURE" in r.json()["error"]


def test_paid_search_is_white_labeled_and_logged(client, monkeypatch):
    _configure(monkeypatch)
    _stub_provider(monkeypatch)
    before = len(_research_events())
    r = client.post(
        "/api/v1/research/search",
        json={"query": "hotel REIT earnings", "include_text": True},
        headers={"PAYMENT-SIGNATURE": _pay_header("paidsearch@uze.test")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "UZE Research"
    assert body["kind"] == "search"
    first = body["results"][0]
    assert first["title"] == "Hotel earnings beat"
    assert first["published_date"] == "2026-11-01T00:00:00.000Z"
    assert first["text"] == "Revenue grew."
    # White-label rule: no provider name, request id, or cost
    # field anywhere in the affiliate-facing payload.
    raw = r.text.lower()
    assert "exa.ai" not in raw
    assert '"provider"' not in raw
    assert "req-abc-123" not in raw
    assert "costdollars" not in raw
    assert "PAYMENT-RESPONSE" in r.headers
    events = _research_events()
    assert len(events) == before + 1
    latest = events[-1]
    assert latest["door"] == "api"
    assert latest["provider"] == "exa"  # internal audit only
    assert latest["payment"]["profile"] == "x402-mock"
    assert latest["result_count"] == 2


def test_financial_forces_the_financial_category(client, monkeypatch):
    _configure(monkeypatch)
    captured: dict = {}
    _stub_provider(monkeypatch, captured)
    r = client.post(
        "/api/v1/research/financial",
        json={"query": "ASHFORD HOSPITALITY earnings"},
        headers={"PAYMENT-SIGNATURE": _pay_header("financial@uze.test")},
    )
    assert r.status_code == 200
    assert captured["payload"]["category"] == "financial report"
    assert r.json()["kind"] == "financial_search"


def test_contents_requires_urls(client, monkeypatch):
    _configure(monkeypatch)
    _stub_provider(monkeypatch)
    r = client.post("/api/v1/research/contents", json={"urls": []})
    assert r.status_code == 422
    assert r.json()["field"] == "urls"
    r = client.post(
        "/api/v1/research/contents",
        json={"urls": ["https://cdn.sample.test/a"]},
        headers={"PAYMENT-SIGNATURE": _pay_header("contents@uze.test")},
    )
    assert r.status_code == 200
    assert r.json()["kind"] == "contents"


def test_email_gateway_research_door(client, monkeypatch):
    _configure(monkeypatch)
    _stub_provider(monkeypatch)
    before = len(_research_events())
    r = client.post(
        "/api/v1/ingest/email",
        json={
            "subject": "Research: hotel REIT earnings",
            "sender": "agent@uze.test",
            "attachment_base64": "",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["routedTo"] == "UZE Research"
    assert body["query"] == "hotel REIT earnings"
    assert len(body["results"]) == 2
    assert "exa.ai" not in r.text.lower()
    assert '"provider"' not in r.text.lower()
    events = _research_events()
    assert len(events) == before + 1
    assert events[-1]["door"] == "email"
    assert events[-1]["payment"]["profile"] == "gateway-demo-unmetered"


def test_email_gateway_research_needs_a_question(client, monkeypatch):
    _configure(monkeypatch)
    _stub_provider(monkeypatch)
    r = client.post(
        "/api/v1/ingest/email",
        json={
            "subject": "Research:",
            "sender": "agent@uze.test",
            "attachment_base64": "",
        },
    )
    assert r.status_code == 422
    assert "Research:" in r.json()["error"]


# ------------------------------------------------------- run contract (B/C)


def _stub_raising(monkeypatch, exc):
    def fake_post(path, payload):
        raise exc

    monkeypatch.setattr(research, "_provider_post", fake_post)


def _events_of(event_type):
    session = db.session()
    try:
        rows = (
            session.query(models.EventLog)
            .filter(models.EventLog.event_type == event_type)
            .all()
        )
        return [r.payload for r in rows]
    finally:
        session.close()


def _pay_header_for(payer):
    return x402.build_mock_signature_header(
        payer=payer,
        network=x402.BASE_NETWORK,
        amount=ENV["X402_SKU_AMOUNT_ATOMIC"],
        pay_to=ENV["X402_PAYTO_BASE"],
    )


def test_failure_after_payment_logs_failed_and_retires_signature(
    client, monkeypatch
):
    _configure(monkeypatch)
    _stub_raising(monkeypatch, research.ResearchUpstreamError(503))
    header = _pay_header_for("failcase@uze.test")
    r = client.post(
        "/api/v1/research/search",
        json={"query": "hotels"},
        headers={"PAYMENT-SIGNATURE": header},
    )
    assert r.status_code == 502
    body = r.json()
    assert body["error_code"] == "provider_error"
    assert body["run_id"].startswith("UZE-RES-")
    assert "credit" in body["credit_note"]
    failed = [
        p
        for p in _events_of("research.run_failed")
        if p["run_id"] == body["run_id"]
    ]
    assert len(failed) == 1
    assert failed[0]["status"] == "failed"
    assert failed[0]["error_code"] == "provider_error"
    assert failed[0]["credit_note"] == body["credit_note"]

    # The paid signature is retired: replaying it is refused
    # as payment_invalid naming the failed run.
    r2 = client.post(
        "/api/v1/research/search",
        json={"query": "hotels"},
        headers={"PAYMENT-SIGNATURE": header},
    )
    assert r2.status_code == 402
    assert r2.json()["error_code"] == "payment_invalid"
    assert r2.json()["run_id"] == body["run_id"]

    # A fresh payment runs under a NEW run id.
    _stub_provider(monkeypatch)
    r3 = client.post(
        "/api/v1/research/search",
        json={"query": "hotels"},
        headers={"PAYMENT-SIGNATURE": _pay_header_for("failcase2@uze.test")},
    )
    assert r3.status_code == 200
    assert r3.json()["run_id"] != body["run_id"]


def test_provider_timeout_maps_to_provider_timeout(client, monkeypatch):
    _configure(monkeypatch)
    _stub_raising(monkeypatch, research.ResearchTimeout())
    r = client.post(
        "/api/v1/research/search",
        json={"query": "hotels"},
        headers={"PAYMENT-SIGNATURE": _pay_header_for("timeout@uze.test")},
    )
    assert r.status_code == 502
    assert r.json()["error_code"] == "provider_timeout"


def test_completed_signature_replays_the_same_run(client, monkeypatch):
    _configure(monkeypatch)
    calls = {"n": 0}

    def counting_post(path, payload):
        calls["n"] += 1
        return RAW_SEARCH

    monkeypatch.setattr(research, "_provider_post", counting_post)
    header = _pay_header_for("replay@uze.test")
    r1 = client.post(
        "/api/v1/research/search",
        json={"query": "hotels"},
        headers={"PAYMENT-SIGNATURE": header},
    )
    assert r1.status_code == 200
    r2 = client.post(
        "/api/v1/research/search",
        json={"query": "hotels"},
        headers={"PAYMENT-SIGNATURE": header},
    )
    assert r2.status_code == 200
    assert r2.json()["run_id"] == r1.json()["run_id"]
    assert r2.json()["idempotent_replay"] is True
    assert calls["n"] == 1  # never a second provider call / charge


_YEARS = [{
    "line_items": {
        "Rental Revenue": 1_000_000,
        "Payroll - Property Manager": -60_000,
        "Property Taxes": -90_000,
        "Insurance": -25_000,
    }
}]


def test_composition_by_run_id(client, monkeypatch):
    _configure(monkeypatch)
    _stub_provider(monkeypatch)
    payer = "compose@uze.test"
    header = _pay_header_for(payer)
    r = client.post(
        "/api/v1/research/financial",
        json={"query": "hotel REIT SEC filings"},
        headers={"PAYMENT-SIGNATURE": header},
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]

    # The owner references the run on an underwrite: sources
    # are cited, and the settlement log links the runs.
    u = client.post(
        "/api/v1/underwrite/UZ-W-001",
        json={"years": _YEARS, "context_run_id": run_id},
        headers={"PAYMENT-SIGNATURE": header},
    )
    assert u.status_code == 200
    ctx = u.json()["result"]["research_context"]
    assert ctx["run_id"] == run_id
    assert len(ctx["sources"]) == 2
    settlements = _events_of("x402.mock_settlement")
    assert settlements[-1]["composed_from"] == run_id

    # A different identity may not reference the run.
    u2 = client.post(
        "/api/v1/underwrite/UZ-W-001",
        json={"years": _YEARS, "context_run_id": run_id},
        headers={"PAYMENT-SIGNATURE": _pay_header_for("intruder@uze.test")},
    )
    assert u2.status_code == 422
    assert u2.json()["error"] == "COMPOSITION_IDENTITY_MISMATCH"

    # An unknown run is named as such.
    u3 = client.post(
        "/api/v1/underwrite/UZ-W-001",
        json={"years": _YEARS, "context_run_id": "UZE-RES-DOESNOTEXIST"},
        headers={"PAYMENT-SIGNATURE": header},
    )
    assert u3.status_code == 422
    assert u3.json()["error"] == "RUN_NOT_FOUND"
