"""MCP surface for UZE Research (hardening build, 2026-11-13).

Pins the manifest contract from the explainer section 7 as
built by mcp_surface.py: one tool (UZE_Research_Query) with
the declared input/output schemas, the Tier 1 gate,
permitted rails Base + Solana (agentic surface only), and a
pricing RULE instead of a static price. tools/call rides
the same x402 gate and execution core as the API door, and
its structured output carries exactly the declared keys —
no provider metadata, pagination tokens, or internal IDs.
"""

from __future__ import annotations

import json

import research
import x402
from test_research import ENV, RAW_SEARCH, _configure, _pay_header_for


def _rpc(client, method, params=None, req_id=1, headers=None):
    body = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        body["params"] = params
    return client.post("/api/v1/mcp", json=body, headers=headers or {})


def test_initialize_and_tools_list_manifest(client, monkeypatch):
    _configure(monkeypatch)
    r = _rpc(client, "initialize")
    assert r.status_code == 200
    assert r.json()["result"]["serverInfo"]["name"] == "UZE Research"

    r = _rpc(client, "tools/list")
    tools = r.json()["result"]["tools"]
    # Two tools since the 2026-11-13 night sprint added
    # UZE_Underwrite beside UZE_Research_Query (its own manifest
    # is pinned in test_mcp_underwrite.py).
    assert len(tools) == 2
    tool = tools[0]
    assert tool["name"] == "UZE_Research_Query"
    assert tool["inputSchema"]["required"] == ["query"]
    assert tool["inputSchema"]["properties"]["vertical"]["enum"] == [
        "financial",
        "general",
        "sec_filings",
    ]
    out_props = tool["outputSchema"]["properties"]["results"]["items"]
    assert set(out_props["properties"]) == {
        "title",
        "url",
        "snippet",
        "source_date",
    }
    meta = tool["_meta"]
    assert meta["tier_gate"] == "Tier 1"
    assert meta["permitted_rails"] == ["Base", "Solana"]
    assert "no static price" in meta["pricing_rule"]


def test_tools_call_without_payment_returns_the_quote(client, monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(
        research, "_provider_post", lambda path, payload: RAW_SEARCH
    )
    r = _rpc(
        client,
        "tools/call",
        {"name": "UZE_Research_Query", "arguments": {"query": "hotels"}},
    )
    result = r.json()["result"]
    assert result["_meta"]["payment_required"] is True
    quote = json.loads(result["content"][0]["text"])
    networks = {a["network"] for a in quote["accepts"]}
    assert networks == {x402.BASE_NETWORK, x402.SOLANA_NETWORK}


def test_tools_call_paid_output_matches_the_schema(client, monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(
        research, "_provider_post", lambda path, payload: RAW_SEARCH
    )
    r = _rpc(
        client,
        "tools/call",
        {
            "name": "UZE_Research_Query",
            "arguments": {"query": "hotel REIT earnings", "vertical": "sec_filings"},
        },
        headers={"PAYMENT-SIGNATURE": _pay_header_for("mcp@uze.test")},
    )
    result = r.json()["result"]
    assert result["isError"] is False
    structured = result["structuredContent"]
    assert structured["run_id"].startswith("UZE-RES-")
    assert len(structured["results"]) == 2
    for item in structured["results"]:
        assert set(item) == {"title", "url", "snippet", "source_date"}
    assert structured["results"][0]["snippet"] == "Revenue grew."
    assert structured["results"][0]["source_date"] == "2026-11-01T00:00:00.000Z"
    raw = r.text.lower()
    assert "exa.ai" not in raw
    assert "req-abc-123" not in raw
    assert "costdollars" not in raw


def test_tools_call_validation(client, monkeypatch):
    _configure(monkeypatch)
    r = _rpc(client, "tools/call", {"name": "Nope", "arguments": {}})
    assert r.json()["error"]["code"] == -32602
    r = _rpc(
        client,
        "tools/call",
        {"name": "UZE_Research_Query", "arguments": {}},
    )
    assert r.json()["error"]["code"] == -32602
    assert "query" in r.json()["error"]["message"]
    r = _rpc(client, "resources/list")
    assert r.json()["error"]["code"] == -32601
