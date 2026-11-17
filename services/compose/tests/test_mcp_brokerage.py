"""Brokerage-model MCP utility (MCP Utility build, 2026-11-16).

Pins the contract in docs/MCP-UTILITY-SPEC-v0.1.md as built by
mcp_brokerage.py: connect-your-LLM over one MCP link; read access
to all accounts; TradFi trading confined to the dedicated MCP
account behind a REVIEW-then-confirm step; crypto refused with the
custody-differentiation payload; pairings board labelled roadmap.
Everything is demo data and every check here can fail against the
intended behaviour.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import create_app

client = TestClient(create_app(), raise_server_exceptions=False)

URL = "/api/v1/mcp-brokerage"


def _rpc(method, params=None, req_id=1):
    body = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        body["params"] = params
    return client.post(URL, json=body)


def _call(name, arguments=None):
    r = _rpc(
        "tools/call",
        {"name": name, "arguments": arguments or {}},
    )
    assert r.status_code == 200
    return r.json()["result"]


def _structured(name, arguments=None):
    result = _call(name, arguments)
    return result["structuredContent"], result["isError"]


def test_initialize_and_tools_list():
    r = _rpc("initialize")
    assert r.status_code == 200
    info = r.json()["result"]["serverInfo"]
    assert info["name"] == "UZEmarkets Brokerage MCP"

    r = _rpc("tools/list")
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert names == [
        "Brokerage_List_Accounts",
        "Brokerage_Get_Positions",
        "Brokerage_Get_Transactions",
        "Brokerage_Get_Quote",
        "Brokerage_Place_Order",
        "UZE_Self_Custody_Route",
        "UZE_Pairings_Board",
    ]


def test_unknown_tool_is_an_rpc_error():
    r = _rpc("tools/call", {"name": "Nope", "arguments": {}})
    assert r.json()["error"]["code"] == -32602


def test_connect_payload_carries_the_rules():
    r = client.get(URL + "/connect")
    assert r.status_code == 200
    body = r.json()
    assert body["demo"] is True
    assert "Claude" in body["supported_clients"]
    assert "dedicated" in body["dedicated_account_rule"].lower()
    assert "loss of the entire amount invested" in body["disclosure"]
    assert "more than 5 consecutive years" in body["disclosure"]
    assert "more than 5 consecutive years" in body["self_custody_eligibility"]


def test_connect_payload_carries_the_trading_segmentation():
    body = client.get(URL + "/connect").json()
    # Trading segmentation only: TradeLayer | SigLayer. The product
    # MCPs (Underwrite | Assign | Auction) are a separate grouping
    # and must not appear in this surface's payload (James's
    # correction, 2026-11-16: nothing to do with each other).
    assert body["trading_segmentation"] == "TradeLayer | SigLayer"
    surfaces = {s["name"]: s["status"] for s in body["trading_surfaces"]}
    assert set(surfaces) == {"TradeLayer", "SigLayer"}
    assert "Brokerage MCP" in surfaces["TradeLayer"]
    assert "after TradeLayer" in surfaces["SigLayer"]
    assert "mcp_family" not in body
    assert "family_listing" not in body
    sequence = " ".join(body["launch_sequence"])
    assert sequence.index("TradeLayer") < sequence.rindex("SigLayer")


def test_list_accounts_flags_the_dedicated_account():
    structured, is_error = _structured("Brokerage_List_Accounts")
    assert is_error is False
    accounts = {a["account_id"]: a for a in structured["accounts"]}
    assert accounts["acct_mcp"]["dedicated_mcp_account"] is True
    assert accounts["acct_mcp"]["agent_access"] == "read_and_trade"
    assert accounts["acct_primary"]["dedicated_mcp_account"] is False
    assert accounts["acct_primary"]["agent_access"] == "read_only"


def test_positions_and_transactions_read():
    structured, _ = _structured(
        "Brokerage_Get_Positions", {"account_id": "acct_mcp"}
    )
    assert structured["cash_usd"] == 5000.00
    symbols = {p["symbol"] for p in structured["positions"]}
    assert symbols == {"VOO", "NVDA"}

    structured, _ = _structured(
        "Brokerage_Get_Transactions", {"account_id": "acct_primary"}
    )
    assert len(structured["transactions"]) == 2


def test_unknown_account_refused():
    structured, is_error = _structured(
        "Brokerage_Get_Positions", {"account_id": "acct_nope"}
    )
    assert is_error is True
    assert structured["code"] == "UNKNOWN_ACCOUNT"


def test_quote_tradfi_and_crypto_differentiation():
    structured, is_error = _structured(
        "Brokerage_Get_Quote", {"symbol": "AAPL"}
    )
    assert is_error is False
    assert structured["price"] == 247.85
    assert "not live market data" in structured["as_of"]

    structured, is_error = _structured(
        "Brokerage_Get_Quote", {"symbol": "BTC"}
    )
    assert is_error is True
    assert structured["code"] == "CRYPTO_NOT_SERVED_HERE"
    route = structured["uze_crypto_route"]
    assert route["custody"] == "permissionless_self_custody"
    assert "Buyer beware" in route["risk"]


def test_order_review_then_confirm_executes_in_dedicated_account():
    # No confirm -> REVIEW preview, book unchanged.
    structured, is_error = _structured(
        "Brokerage_Place_Order",
        {
            "account_id": "acct_mcp",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 2,
        },
    )
    assert is_error is False
    assert structured["status"] == "REVIEW"
    assert structured["preview"]["estimated_total_usd"] == 495.70

    positions, _ = _structured(
        "Brokerage_Get_Positions", {"account_id": "acct_mcp"}
    )
    assert positions["cash_usd"] == 5000.00

    # Confirm -> FILLED, cash and positions move.
    structured, is_error = _structured(
        "Brokerage_Place_Order",
        {
            "account_id": "acct_mcp",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 2,
            "confirm": True,
        },
    )
    assert is_error is False
    assert structured["status"] == "FILLED"
    assert structured["cash_after_usd"] == 4504.30

    positions, _ = _structured(
        "Brokerage_Get_Positions", {"account_id": "acct_mcp"}
    )
    aapl = next(
        p for p in positions["positions"] if p["symbol"] == "AAPL"
    )
    assert aapl["quantity"] == 2


def test_order_refused_outside_dedicated_account():
    structured, is_error = _structured(
        "Brokerage_Place_Order",
        {
            "account_id": "acct_primary",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 1,
            "confirm": True,
        },
    )
    assert is_error is True
    assert structured["code"] == "NOT_DEDICATED_ACCOUNT"


def test_crypto_order_refused_with_differentiation():
    structured, is_error = _structured(
        "Brokerage_Place_Order",
        {
            "account_id": "acct_mcp",
            "symbol": "SOL",
            "side": "buy",
            "quantity": 1,
            "confirm": True,
        },
    )
    assert is_error is True
    assert structured["code"] == "CRYPTO_NOT_SERVED_HERE"


def test_insufficient_cash_and_position_refused():
    structured, is_error = _structured(
        "Brokerage_Place_Order",
        {
            "account_id": "acct_mcp",
            "symbol": "SPY",
            "side": "buy",
            "quantity": 100,
            "confirm": True,
        },
    )
    assert is_error is True
    assert structured["code"] == "INSUFFICIENT_CASH"

    structured, is_error = _structured(
        "Brokerage_Place_Order",
        {
            "account_id": "acct_mcp",
            "symbol": "MSFT",
            "side": "sell",
            "quantity": 1,
            "confirm": True,
        },
    )
    assert is_error is True
    assert structured["code"] == "INSUFFICIENT_POSITION"


def test_self_custody_route_and_pairings_board():
    structured, is_error = _structured("UZE_Self_Custody_Route")
    assert is_error is False
    assert structured["product"] == "UZE TradFi Complex & Agentic DeFi"
    assert structured["custody"] == "permissionless_self_custody"
    assert set(structured["venues"]) == {"TradeLayer", "SigLayer"}
    # Eligibility (James, 2026-11-16): the extension is only for
    # experienced DeFi traders — more than 5 consecutive years
    # trading permissionless, non-custodial DeFi markets.
    assert "more than 5 consecutive years" in structured["eligibility"]
    assert "permissionless, non-custodial" in structured["eligibility"]

    structured, is_error = _structured("UZE_Pairings_Board")
    assert is_error is False
    assert structured["priority_chains"] == ["Robinhood", "Solana", "Ink"]
    routes = {p["route"] for p in structured["pairings"]}
    assert any("xStocks" in p["pair"] for p in structured["pairings"])
    assert any("Ink" in r for r in routes)
    assert all(
        p["status"].startswith("roadmap") for p in structured["pairings"]
    )
