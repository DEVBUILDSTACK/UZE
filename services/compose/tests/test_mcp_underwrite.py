"""MCP surface — the UZE_Underwrite tool (2026-11-13).

Pins the second tool beside UZE_Research_Query: the
tools/list manifest order, argument validation (-32602)
before the gate, the x402 gate answered in-band exactly as
the research tool answers it (an unconfigured price is the
labelled PRICING_NOT_CONFIGURED payload, never an invented
one), and — with the gate satisfied the same way
tests/test_mcp_surface.py satisfies it (configured pricing
plus a mock PAYMENT-SIGNATURE) — the persisted report
receipt and the summary shape.

Fixtures are synthetic and modeled on
tests/test_comp_benchmark.py (SUBJECT / COMPS / YEARS).
"""

from __future__ import annotations

import json

from test_research import _configure, _pay_header_for

SUBJECT = {
    "property_type": "Garden Style",
    "year_built": 2005,
    "property_class": "B",
    "unit_count": 100,
    "micro_region": "baltimore-washington",
}

SUBJECT_ITEMS = {
    "Market Rent Potential": 1_200_000,
    "Parking": 10_000,
    "Vacancy Loss": -60_000,
    "Repairs & Maintenance": 150_000,
    "Property Taxes": 90_000,
    "Insurance": 30_000,
}


def _comp(name, units, items, *, year=2004, ptype="GARDEN_STYLE",
          pclass="B", region="baltimore-washington"):
    return {
        "name": name,
        "profile": {
            "property_type": ptype,
            "year_built": year,
            "property_class": pclass,
            "unit_count": units,
            "micro_region": region,
        },
        "line_items": items,
    }


COMPS = [
    _comp("Comp One", 80, {
        "Market Rent Potential": 1_040_000, "Parking": 16_000,
        "Vacancy Loss": -40_000, "R&M": 96_000,
    }),
    _comp("Comp Two", 120, {
        "Market Rent Potential": 1_560_000, "Parking": 24_000,
        "Vacancy Loss": -60_000, "Repairs and Maintenance": 144_000,
    }),
]

YEARS = [
    {"period": "2024", "line_items": {
        "Rental Income": 900_000, "Repairs & Maintenance": 120_000,
    }},
    {"period": "2025", "line_items": SUBJECT_ITEMS},
]

ARGS = {
    "years": YEARS,
    "subject_profile": SUBJECT,
    "comps": COMPS,
    "sender_email": "owner@example.com",
}


def _rpc(client, method, params=None, req_id=1, headers=None):
    body = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        body["params"] = params
    return client.post("/api/v1/mcp", json=body, headers=headers or {})


def _call(client, arguments, headers=None):
    return _rpc(
        client,
        "tools/call",
        {"name": "UZE_Underwrite", "arguments": arguments},
        headers=headers,
    )


def test_tools_list_names_both_tools_in_order(client):
    r = _rpc(client, "tools/list")
    assert r.status_code == 200
    tools = r.json()["result"]["tools"]
    assert [t["name"] for t in tools] == [
        "UZE_Research_Query",
        "UZE_Underwrite",
    ]
    tool = tools[1]
    assert tool["inputSchema"]["required"] == ["years"]
    assert tool["inputSchema"]["properties"]["years"]["minItems"] == 1
    assert tool["inputSchema"]["properties"]["contribute_comps"][
        "default"
    ] is False
    assert set(tool["outputSchema"]["required"]) == {"receipt", "summary"}
    meta = tool["_meta"]
    assert meta["tier_gate"] == "Tier 1"
    assert meta["surface"] == "agentic"
    assert meta["permitted_rails"] == ["Base", "Solana"]
    assert "no static price" in meta["pricing_rule"]


def test_tools_call_unconfigured_pricing_is_labelled_in_band(
    client, monkeypatch
):
    # The default environment: no pricing configured. The
    # gate's labelled answer rides the tool result content
    # (isError False), exactly as the research tool's does.
    for key in (
        "X402_SKU_AMOUNT_ATOMIC",
        "X402_PAYTO_BASE",
        "X402_PAYTO_SOLANA",
    ):
        monkeypatch.delenv(key, raising=False)
    r = _call(client, ARGS)
    result = r.json()["result"]
    assert result["isError"] is False
    assert result["_meta"]["http_status"] == 503
    assert result["_meta"]["payment_required"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["error"] == "PRICING_NOT_CONFIGURED"


def test_tools_call_missing_years_is_a_rpc_validation_error(client):
    r = _call(client, {"subject_profile": SUBJECT})
    assert r.json()["error"]["code"] == -32602
    assert "years" in r.json()["error"]["message"]
    r = _call(client, {"years": []})
    assert r.json()["error"]["code"] == -32602


def test_tools_call_paid_returns_receipt_and_summary(client, monkeypatch):
    _configure(monkeypatch)
    r = _call(
        client,
        ARGS,
        headers={"PAYMENT-SIGNATURE": _pay_header_for("underwrite@uze.test")},
    )
    result = r.json()["result"]
    assert result["isError"] is False
    structured = result["structuredContent"]
    # The content text carries the same structured payload.
    assert json.loads(result["content"][0]["text"]) == structured
    receipt = structured["receipt"]
    assert receipt["report_id"].startswith("uwr_")
    summary = structured["summary"]
    # Period NOIs computed independently of the code under
    # test: 2024 = 900,000 - 120,000; 2025 = (1,200,000 +
    # 10,000 - 60,000) - 150,000 - 90,000 - 30,000.
    assert summary["periods"] == [
        {"period": "2024", "noi": 780_000},
        {"period": "2025", "noi": 880_000},
    ]
    # Findings rank by absolute annualized dollars: the
    # R&M divergence ($300/unit x 100 units) leads.
    assert summary["top_findings"][0]["line"] == "Repairs & Maintenance"
    assert summary["top_findings"][0]["annualized_impact_usd"] == 30_000
    assert summary["delta_status"] is None
