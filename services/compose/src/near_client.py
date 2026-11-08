"""NEAR contract client for the composition layer (Sprint 1.5, Day 2).

Thin sync wrapper over py-near's async Account, in the shape Day 2's
plan files: connect to testnet, call post_intent / submit_bid on the
deployed contract, read get_matches.

Credentials: the NEAR CLI keychain file
(~/.near-credentials/testnet/<account>.json) — the same key the CLI
deployed with. The private key is read from that file at call time and
never logged, stored in the database, or committed.

Chain calls are GATED: compose calls the chain only when
COMPOSE_NEAR_CHAIN=1. Endpoints record the outcome on the response
(chain.status: submitted | disabled | unavailable) and never fake a
chain result — an unavailable chain leaves chainIntentRef/chainBidRef
null, which is the honest state (Kitchen Standard: evidence from the
running system, or a stated absence of it).
"""

from __future__ import annotations

import asyncio
import json
import os

CONTRACT_ID = os.environ.get("NEAR_CONTRACT_ID", "uzemarkets-talent.testnet")
ACCOUNT_ID = os.environ.get("NEAR_ACCOUNT_ID", "uzemarkets-talent.testnet")
RPC_ADDR = os.environ.get("NEAR_RPC_ADDR", "https://rpc.testnet.near.org")


def chain_enabled() -> bool:
    return os.environ.get("COMPOSE_NEAR_CHAIN") == "1"


def _load_private_key(account_id: str) -> str:
    path = os.path.expanduser(
        f"~/.near-credentials/testnet/{account_id}.json"
    )
    with open(path) as fh:
        creds = json.load(fh)
    return creds["private_key"]


class _ProxiedProvider:
    """py-near's JsonProvider with an env-proxy-aware HTTP session.

    This VM's egress goes through an HTTP proxy (https_proxy is set
    globally; curl and requests honor it automatically). py-near
    builds its aiohttp session without trust_env, so it connects
    directly and the intercepted TLS handshake fails with
    SSL WRONG_VERSION_NUMBER. Rebuilding the session with
    trust_env=True is the whole fix — signing, serialization, and
    RPC semantics stay py-near's."""

    @staticmethod
    def build(rpc_addr: str):
        import aiohttp
        from py_near.providers import JsonProvider

        class Proxied(JsonProvider):
            async def startup(self):
                self._timeout = aiohttp.ClientTimeout(total=self.timeout)
                self._connector = aiohttp.TCPConnector(
                    limit=1000, limit_per_host=200
                )
                self._client = aiohttp.ClientSession(
                    connector=self._connector,
                    timeout=self._timeout,
                    trust_env=True,
                )

        return Proxied(rpc_addr)


async def _call(method: str, args: dict, view: bool):
    from py_near.account import Account

    account = Account(
        ACCOUNT_ID, _load_private_key(ACCOUNT_ID), rpc_addr=RPC_ADDR
    )
    account._provider = _ProxiedProvider.build(RPC_ADDR)
    await account.startup()
    if view:
        result = await account.view_function(CONTRACT_ID, method, args)
        return result.result
    result = await account.function_call(
        CONTRACT_ID, method, args, gas=100_000_000_000_000, amount=0
    )
    # py-near's TransactionResult carries the call's return value as a
    # base64 SuccessValue in .status, not as a .result attribute.
    import base64

    value = None
    if isinstance(result.status, dict) and result.status.get("SuccessValue"):
        value = json.loads(base64.b64decode(result.status["SuccessValue"]))
    return {"txHash": result.transaction.hash, "result": value}


def _run(method: str, args: dict, view: bool = False) -> dict:
    """One chain outcome, stated plainly:
    {"status": "submitted", ...} | {"status": "disabled"} |
    {"status": "unavailable", "error": <what failed>}."""
    if not chain_enabled():
        return {"status": "disabled"}
    try:
        out = asyncio.run(_call(method, args, view))
        return {"status": "submitted", **(out if isinstance(out, dict) else {"result": out})}
    except Exception as exc:  # chain is external; report, never raise
        return {"status": "unavailable", "error": f"{type(exc).__name__}: {exc}"}


def post_intent(intent_payload: dict) -> dict:
    return _run("post_intent", {"intent_json": json.dumps(intent_payload)})


def submit_bid(intent_ref: str, bid_payload: dict) -> dict:
    return _run(
        "submit_bid",
        {"intent_id": intent_ref, "bid_json": json.dumps(bid_payload)},
    )


def get_matches(intent_ref: str) -> dict:
    return _run("get_matches", {"intent_id": intent_ref}, view=True)


def settle(intent_ref: str, bid_ref: str) -> dict:
    return _run("settle", {"intent_id": intent_ref, "bid_id": bid_ref})
