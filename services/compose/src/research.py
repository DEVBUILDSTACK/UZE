"""UZE Research — the white-labeled research channel
(owner directive, 2026-11-13: the connected search provider
is wired into the product, deployed, working, and tested
before the hackathon submission — not only a document).

One capability, every door (door parity):
  - API: POST /api/v1/research/search, /contents,
    /financial — x402-gated like every priced Tier-1 tool
    call (see below).
  - Email gateway: a subject carrying the "research"
    keyword routes here from email_gateway.py and runs the
    SAME provider functions with the SAME event logging;
    the gateway's demo scope is unmetered for all its flows
    today (its module docstring says so), and the log row
    records that profile rather than pretending a charge.
  - MCP: the manifest surface is specified in the D5
    explainer section 7; no MCP server exists in this
    codebase yet, so nothing is claimed for that door here.

Provider discipline (naming rule, 2026-11-13): the upstream
provider is an internal implementation detail, registered
in partners/software-stack-implementations. Responses carry
UZE service naming only — the provider's name, its request
ids, and its cost fields never appear in a response payload,
so a provider swap is invisible to affiliates. The provider
identity appears only in the internal EventLog audit row.

Metering (Tier 1, x402): no PAYMENT-SIGNATURE -> 402 with a
PAYMENT-REQUIRED header quoting the configured amount on
Base + Solana; a validated mock-profile signature runs the
call and logs an EventLog row flagged mock:true (validation
is the codebase's labelled mock profile — no funds move;
live facilitator settlement waits on CDP credentials, as
x402.py records). Every metered tool call, search included,
is billable to the calling agent.

Configuration honesty: the provider key comes from
EXA_API_KEY (EXA_API_BASE overrides the endpoint). Absent
key -> 503 RESEARCH_NOT_CONFIGURED. Absent pricing config
-> 503 PRICING_NOT_CONFIGURED. Nothing is invented in
either case, and no key value ever appears in a response
or a log row.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
import x402
from db import get_session

router = APIRouter(prefix="/api/v1/research", tags=["research"])

SERVICE_NAME = "UZE Research"
_DEFAULT_BASE = "https://api.exa.ai"
_MAX_RESULTS = 10
_MAX_URLS = 10
_TEXT_CAP = 20_000

FINANCIAL_CATEGORY = "financial report"


class ResearchNotConfigured(Exception):
    pass


class ResearchUpstreamError(Exception):
    def __init__(self, status: int):
        super().__init__(f"upstream answered HTTP {status}")
        self.status = status


def _provider_key() -> str | None:
    key = os.environ.get("EXA_API_KEY", "").strip()
    return key or None


def _provider_base() -> str:
    return os.environ.get("EXA_API_BASE", _DEFAULT_BASE).rstrip("/")


def _provider_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """One upstream call. trust_env=False follows the
    codebase convention (trust.py, inference.py): this
    deployment's proxy environment breaks httpx env parsing,
    and the provider endpoint is reached directly."""
    key = _provider_key()
    if key is None:
        raise ResearchNotConfigured()
    with httpx.Client(trust_env=False, timeout=30.0) as client:
        resp = client.post(
            f"{_provider_base()}{path}",
            json=payload,
            headers={"x-api-key": key, "Content-Type": "application/json"},
        )
    if resp.status_code != 200:
        raise ResearchUpstreamError(resp.status_code)
    return resp.json()


def _normalize_result(raw: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "title": raw.get("title"),
        "url": raw.get("url"),
        "published_date": raw.get("publishedDate"),
        "author": raw.get("author"),
        "score": raw.get("score"),
    }
    text = raw.get("text")
    if isinstance(text, str) and text:
        out["text"] = text[:_TEXT_CAP]
    return out


def search_web(
    query: str,
    num_results: int = 5,
    category: str | None = None,
    include_text: bool = False,
) -> dict[str, Any]:
    """The provider search call, normalized to the UZE
    Research shape. Raises ResearchNotConfigured /
    ResearchUpstreamError; callers shape the HTTP answer."""
    payload: dict[str, Any] = {
        "query": query,
        "numResults": max(1, min(num_results, _MAX_RESULTS)),
        "type": "auto",
    }
    if category:
        payload["category"] = category
    if include_text:
        payload["contents"] = {"text": True}
    raw = _provider_post("/search", payload)
    return {
        "service": SERVICE_NAME,
        "kind": "financial_search" if category == FINANCIAL_CATEGORY else "search",
        "query": query,
        "results": [_normalize_result(r) for r in raw.get("results", [])],
        "_upstream_request_id": raw.get("requestId"),
    }


def get_contents(urls: list[str]) -> dict[str, Any]:
    raw = _provider_post("/contents", {"urls": urls[:_MAX_URLS], "text": True})
    return {
        "service": SERVICE_NAME,
        "kind": "contents",
        "results": [_normalize_result(r) for r in raw.get("results", [])],
        "_upstream_request_id": raw.get("requestId"),
    }


def _public(result: dict[str, Any]) -> dict[str, Any]:
    """Strip internal fields (underscore-prefixed) so nothing
    provider-shaped reaches an affiliate-facing payload."""
    return {k: v for k, v in result.items() if not k.startswith("_")}


def _log_call(
    session: Session,
    *,
    kind: str,
    door: str,
    actor: str,
    result: dict[str, Any],
    payment: dict[str, Any],
) -> None:
    session.add(
        models.EventLog(
            aggregate_type="research",
            aggregate_id=kind,
            event_type="research.metered_call",
            actor=actor,
            payload={
                "provider": "exa",  # internal audit only
                "upstream_request_id": result.get("_upstream_request_id"),
                "door": door,
                "result_count": len(result.get("results", [])),
                "payment": payment,
            },
        )
    )
    session.commit()


def run_via_gateway(session: Session, *, query: str, sender: str) -> dict[str, Any]:
    """The email door's entry point: same provider function,
    same event log; the gateway demo profile is unmetered
    and the log row says so."""
    result = search_web(query)
    _log_call(
        session,
        kind=result["kind"],
        door="email",
        actor=sender,
        result=result,
        payment={"profile": "gateway-demo-unmetered", "mock": True},
    )
    return _public(result)


# ---------------------------------------------------------------- API door


class SearchIn(BaseModel):
    query: str = ""
    num_results: int = 5
    category: str | None = None
    include_text: bool = False


class FinancialIn(BaseModel):
    query: str = ""
    num_results: int = 5


class ContentsIn(BaseModel):
    urls: list[str] = []


def _gate(request: Request, resource_url: str, description: str):
    """The x402 gate, shared by the three endpoints.
    Returns (config, auth, error_response): exactly one of
    auth / error_response is set."""
    config = x402.pricing_config()
    if config is None:
        return None, None, JSONResponse(
            status_code=503,
            content={
                "error": "PRICING_NOT_CONFIGURED",
                "mock": True,
                "note": (
                    "amounts are quoted per request from "
                    "UZEguidance market pricing; no static "
                    "price is posted and none is invented here"
                ),
            },
        )
    if _provider_key() is None:
        return None, None, JSONResponse(
            status_code=503,
            content={
                "error": "RESEARCH_NOT_CONFIGURED",
                "note": (
                    "the research channel's provider credential "
                    "is not configured on this deployment"
                ),
            },
        )
    required = x402.build_payment_required(resource_url, description, config)
    header_value = request.headers.get("payment-signature")
    if not header_value:
        return None, None, JSONResponse(
            status_code=402,
            content=required,
            headers={"PAYMENT-REQUIRED": x402.encode_header(required)},
        )
    ok, reason, auth = x402.validate_payment_signature(header_value, config)
    if not ok:
        content = dict(required)
        content["error"] = f"invalid PAYMENT-SIGNATURE: {reason}"
        return None, None, JSONResponse(
            status_code=402,
            content=content,
            headers={"PAYMENT-REQUIRED": x402.encode_header(required)},
        )
    return config, auth, None


def _receipt(auth: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": True,
        "mock": True,
        "network": auth["network"],
        "transaction": "mock:" + auth["signature"].removeprefix("mock:")[:16],
        "payer": auth["payer"],
    }


def _run(request: Request, session: Session, kind: str, description: str, fn):
    _config, auth, error = _gate(request, f"/api/v1/research/{kind}", description)
    if error is not None:
        return error
    try:
        result = fn()
    except ResearchNotConfigured:
        return JSONResponse(
            status_code=503, content={"error": "RESEARCH_NOT_CONFIGURED"}
        )
    except ResearchUpstreamError:
        return JSONResponse(
            status_code=502,
            content={
                "error": "RESEARCH_UPSTREAM_ERROR",
                "note": "the research channel's provider did not answer",
            },
        )
    receipt = _receipt(auth)
    _log_call(
        session,
        kind=result["kind"],
        door="api",
        actor=auth["payer"],
        result=result,
        payment={
            "profile": "x402-mock",
            "mock": True,
            "network": auth["network"],
            "asset": auth["asset"],
            "amountAtomic": auth["amount"],
        },
    )
    body = _public(result)
    body["payment"] = receipt
    return JSONResponse(
        content=body,
        headers={"PAYMENT-RESPONSE": x402.encode_header(receipt)},
    )


def _missing(field: str, shape: dict[str, Any]) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "MISSING_FIELD",
            "field": field,
            "accepted_shape": shape,
        },
    )


@router.post("/search")
def research_search(
    body: SearchIn,
    request: Request,
    session: Session = Depends(get_session),
):
    if not body.query.strip():
        return _missing("query", {"query": "non-empty string"})
    return _run(
        request,
        session,
        "search",
        "UZE Research — web search",
        lambda: search_web(
            body.query.strip(),
            body.num_results,
            body.category,
            body.include_text,
        ),
    )


@router.post("/financial")
def research_financial(
    body: FinancialIn,
    request: Request,
    session: Session = Depends(get_session),
):
    if not body.query.strip():
        return _missing("query", {"query": "non-empty string"})
    return _run(
        request,
        session,
        "financial",
        "UZE Research — financial data search",
        lambda: search_web(
            body.query.strip(),
            body.num_results,
            category=FINANCIAL_CATEGORY,
            include_text=True,
        ),
    )


@router.post("/contents")
def research_contents(
    body: ContentsIn,
    request: Request,
    session: Session = Depends(get_session),
):
    urls = [u for u in body.urls if isinstance(u, str) and u.strip()]
    if not urls:
        return _missing("urls", {"urls": ["https://example.com/page"]})
    return _run(
        request,
        session,
        "contents",
        "UZE Research — page contents",
        lambda: get_contents(urls),
    )
