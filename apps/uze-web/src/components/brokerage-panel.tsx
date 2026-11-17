"use client";

import { useCallback, useEffect, useState } from "react";

/** Brokerage MCP panel — the TradeLayer door (dynamic mock-up,
 *  2026-11-16; spec: docs/MCP-UTILITY-SPEC-v0.1.md).
 *
 *  Speaks JSON-RPC to the real MCP surface
 *  (POST /api/v1/mcp-brokerage) — the same calls an external LLM
 *  client makes. If the API build carrying the surface is not
 *  deployed yet, the panel says so plainly and shows nothing
 *  faked: no local demo data stands in for the server. */

const COMPOSE_API =
  process.env.NEXT_PUBLIC_COMPOSE_API_URL ??
  "https://uze-compose-api.onrender.com";
const MCP_URL = `${COMPOSE_API}/api/v1/mcp-brokerage`;

let rpcId = 0;

async function rpc(method: string, params?: unknown) {
  const res = await fetch(MCP_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: ++rpcId,
      method,
      ...(params ? { params } : {}),
    }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const body = await res.json();
  if (body.error) throw new Error(body.error.message as string);
  return body.result;
}

async function callTool(name: string, args: Record<string, unknown> = {}) {
  const result = await rpc("tools/call", { name, arguments: args });
  return {
    structured: result.structuredContent as Record<string, any>,
    isError: Boolean(result.isError),
  };
}

const money = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD" });

interface Account {
  account_id: string;
  label: string;
  custody: string;
  dedicated_mcp_account: boolean;
  agent_access: string;
  cash_usd: number;
  total_value_usd: number;
  positions: {
    symbol: string;
    name: string;
    quantity: number;
    avg_cost: number;
    mark: number;
    market_value: number;
  }[];
}

export default function BrokeragePanel() {
  const [status, setStatus] = useState<"loading" | "online" | "offline">(
    "loading",
  );
  const [connect, setConnect] = useState<Record<string, any> | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [pairings, setPairings] = useState<Record<string, any>[]>([]);
  const [custodyRoute, setCustodyRoute] = useState<Record<
    string,
    any
  > | null>(null);
  const [txAccount, setTxAccount] = useState<string>("acct_mcp");
  const [transactions, setTransactions] = useState<Record<string, any>[]>(
    [],
  );

  const [orderAccount, setOrderAccount] = useState("acct_mcp");
  const [symbol, setSymbol] = useState("AAPL");
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [quantity, setQuantity] = useState("2");
  const [orderResult, setOrderResult] = useState<{
    structured: Record<string, any>;
    isError: boolean;
  } | null>(null);
  const [busy, setBusy] = useState(false);

  const loadAccounts = useCallback(async () => {
    const { structured } = await callTool("Brokerage_List_Accounts");
    setAccounts(structured.accounts as Account[]);
  }, []);

  const loadTransactions = useCallback(async (accountId: string) => {
    const { structured } = await callTool("Brokerage_Get_Transactions", {
      account_id: accountId,
    });
    setTransactions(structured.transactions as Record<string, any>[]);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${MCP_URL}/connect`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setConnect(await res.json());
        await loadAccounts();
        const p = await callTool("UZE_Pairings_Board");
        setPairings(p.structured.pairings as Record<string, any>[]);
        const c = await callTool("UZE_Self_Custody_Route");
        setCustodyRoute(c.structured);
        await loadTransactions("acct_mcp");
        setStatus("online");
      } catch {
        setStatus("offline");
      }
    })();
  }, [loadAccounts, loadTransactions]);

  async function placeOrder(confirm: boolean) {
    setBusy(true);
    try {
      const result = await callTool("Brokerage_Place_Order", {
        account_id: orderAccount,
        symbol: symbol.trim().toUpperCase(),
        side,
        quantity: Number(quantity),
        confirm,
      });
      setOrderResult(result);
      if (!result.isError && result.structured.status === "FILLED") {
        await loadAccounts();
        await loadTransactions(txAccount);
      }
    } catch {
      setStatus("offline");
    } finally {
      setBusy(false);
    }
  }

  if (status === "loading") {
    return <p className="note">Connecting to the Brokerage MCP…</p>;
  }

  if (status === "offline") {
    return (
      <p className="note">
        The Brokerage MCP API isn&apos;t answering yet — this panel
        lights up when the API build carrying{" "}
        <code>POST /api/v1/mcp-brokerage</code> is deployed. Nothing
        here is faked in the meantime.
      </p>
    );
  }

  const s = orderResult?.structured;
  const isCryptoRefusal = s?.code === "CRYPTO_NOT_SERVED_HERE";

  return (
    <div>
      <h2>Connect your AI</h2>
      <p>
        One MCP link — paste it into your LLM client and the agent can
        read your accounts and trade TradFi in the dedicated account.
      </p>
      <dl>
        <dt>MCP link</dt>
        <dd>
          <code>{MCP_URL}</code>
        </dd>
        <dt>Works with</dt>
        <dd>
          <span className="chips">
            {(connect?.supported_clients as string[] | undefined)?.map(
              (c) => (
                <span key={c} className="chip">
                  {c}
                </span>
              ),
            )}
          </span>
        </dd>
        <dt>The rule</dt>
        <dd>{connect?.dedicated_account_rule as string}</dd>
        <dt>Review</dt>
        <dd>{connect?.review_rule as string}</dd>
      </dl>

      <h2>Trading — TradeLayer | SigLayer</h2>
      <div className="cards">
        {(connect?.trading_surfaces as Record<string, any>[] | undefined)?.map(
          (t) => (
            <div key={t.name as string} className="card">
              <h3>{t.name as string}</h3>
              <p className="meta">{t.status as string}</p>
              <p>{t.surface as string}</p>
            </div>
          ),
        )}
      </div>
      <p className="note">
        {(connect?.launch_sequence as string[] | undefined)?.join(" ")}
      </p>

      <h2>Accounts — what the agent sees</h2>
      <div className="cards">
        {accounts.map((a) => (
          <div key={a.account_id} className="card">
            <h3>
              {a.label}
              {a.dedicated_mcp_account ? " — dedicated MCP account" : ""}
            </h3>
            <p className="meta">
              Agent access: {a.agent_access} · Cash {money(a.cash_usd)} ·
              Total {money(a.total_value_usd)}
            </p>
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Qty</th>
                  <th>Mark</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {a.positions.map((p) => (
                  <tr key={p.symbol}>
                    <td>{p.symbol}</td>
                    <td>{p.quantity}</td>
                    <td>{money(p.mark)}</td>
                    <td>{money(p.market_value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>

      <h2>Place an order — as the agent</h2>
      <form
        className="gen-form"
        onSubmit={(e) => {
          e.preventDefault();
          void placeOrder(false);
        }}
      >
        <label>
          Account{" "}
          <select
            value={orderAccount}
            onChange={(e) => {
              setOrderAccount(e.target.value);
              setOrderResult(null);
            }}
          >
            {accounts.map((a) => (
              <option key={a.account_id} value={a.account_id}>
                {a.label}
                {a.dedicated_mcp_account ? " (agent may trade)" : " (read-only)"}
              </option>
            ))}
          </select>
        </label>{" "}
        <label>
          Symbol{" "}
          <input
            type="text"
            value={symbol}
            onChange={(e) => {
              setSymbol(e.target.value);
              setOrderResult(null);
            }}
            size={8}
          />
        </label>{" "}
        <label>
          Side{" "}
          <select
            value={side}
            onChange={(e) => {
              setSide(e.target.value as "buy" | "sell");
              setOrderResult(null);
            }}
          >
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
          </select>
        </label>{" "}
        <label>
          Qty{" "}
          <input
            type="text"
            value={quantity}
            onChange={(e) => {
              setQuantity(e.target.value);
              setOrderResult(null);
            }}
            size={5}
          />
        </label>{" "}
        <button type="submit" disabled={busy}>
          Review order
        </button>
      </form>
      <p className="note">
        Try it: buy AAPL in the MCP account (review, then confirm);
        try the Individual Brokerage account (refused — read-only);
        try BTC (refused — crypto lives on the self-custody route).
      </p>

      {orderResult && s && !isCryptoRefusal && (
        <div className="card">
          <h3>
            {s.status === "REVIEW"
              ? "Review — not placed yet"
              : s.status === "FILLED"
                ? "Filled (simulated)"
                : `Refused — ${s.code as string}`}
          </h3>
          {s.status === "REVIEW" && (
            <>
              <p>
                {(s.preview.side as string).toUpperCase()}{" "}
                {s.preview.quantity as number} × {s.preview.symbol as string}{" "}
                @ {money(s.preview.mark_price as number)} ={" "}
                {money(s.preview.estimated_total_usd as number)} in{" "}
                {s.preview.account_label as string}
              </p>
              <button
                type="button"
                disabled={busy}
                onClick={() => void placeOrder(true)}
              >
                Confirm order
              </button>
            </>
          )}
          {s.status === "FILLED" && (
            <p>
              Order {s.order.order_id as string} filled. Cash after:{" "}
              {money(s.cash_after_usd as number)}. Simulated against the
              demo book — no real money moved.
            </p>
          )}
          {s.status === "REFUSED" && (
            <p>{(s.message as string) ?? (s.code as string)}</p>
          )}
        </div>
      )}

      {orderResult && isCryptoRefusal && s && (
        <div className="card">
          <h3>Crypto doesn&apos;t live here</h3>
          <p>{s.message as string}</p>
          <p>
            <strong>UZE route:</strong>{" "}
            {(s.uze_crypto_route.venues as string[]).join(" + ")} —{" "}
            {s.uze_crypto_route.chain as string}.{" "}
            {s.uze_crypto_route.extension as string}{" "}
            <strong>{s.uze_crypto_route.eligibility as string}</strong>{" "}
            {s.uze_crypto_route.risk as string}
          </p>
        </div>
      )}

      <h2>Order history</h2>
      <p>
        Account{" "}
        <select
          value={txAccount}
          onChange={(e) => {
            setTxAccount(e.target.value);
            void loadTransactions(e.target.value);
          }}
        >
          {accounts.map((a) => (
            <option key={a.account_id} value={a.account_id}>
              {a.label}
            </option>
          ))}
        </select>
      </p>
      <table>
        <thead>
          <tr>
            <th>When</th>
            <th>Order</th>
            <th>Side</th>
            <th>Qty</th>
            <th>Price</th>
            <th>By</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((t) => (
            <tr key={t.order_id as string}>
              <td>{t.at as string}</td>
              <td>{t.symbol as string}</td>
              <td>{t.side as string}</td>
              <td>{t.quantity as number}</td>
              <td>{money(t.price as number)}</td>
              <td>{t.placed_by as string}</td>
              <td>{t.status as string}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Two doors, two custody models</h2>
      <div className="cards">
        <div className="card">
          <h3>This door — brokerage model</h3>
          <p>
            All available assets at the brokerage — long equities,
            options, and crypto — inside a brokerage account, held in
            brokerage custody. The agent reads everything and trades
            only in the dedicated MCP account, behind a review step.
            (This demo simulates equities.)
          </p>
        </div>
        <div className="card">
          <h3>UZE door — permissionless self-custody</h3>
          <p>
            {custodyRoute?.differentiation as string}{" "}
            {custodyRoute?.extension as string}{" "}
            <strong>{custodyRoute?.eligibility as string}</strong>{" "}
            {custodyRoute?.risk as string}
          </p>
        </div>
      </div>

      <h2>Pairings board — roadmap</h2>
      <table>
        <thead>
          <tr>
            <th>Pair</th>
            <th>Route</th>
            <th>Kind</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {pairings.map((p) => (
            <tr key={p.pair as string}>
              <td>{p.pair as string}</td>
              <td>{p.route as string}</td>
              <td>{p.kind as string}</td>
              <td>{p.status as string}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="note">
        Priority chains: Robinhood, Solana, Ink. The other previously
        specified chains (NEAR, Base, LightLink) follow. No pairing is
        live in this build.
      </p>

      <h2>Disclosure</h2>
      <p className="note">{connect?.disclosure as string}</p>
    </div>
  );
}
