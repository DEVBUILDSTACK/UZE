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
  - MCP: mcp_surface.py exposes UZE_Research_Query over a
    minimal JSON-RPC surface, delegating to the same
    execution core (_execute) with door="mcp".

Run contract (explainer section 7, built for this channel
2026-11-13): every accepted run gets a run ID
(UZE-RES-<ulid>) carried in the response and the event log.
A provider failure AFTER payment validation logs the run as
failed with a machine-readable error_code (provider_error /
provider_timeout) and a credit note, and RETIRES the paid
signature: replaying it answers payment_invalid naming the
failed run, and a retry pays a fresh quote under a new run
ID. Replaying the signature of a COMPLETED run returns that
run's result — the same run, never a second charge.

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

import hashlib
import os
import secrets
import time
from typing import Any, Callable

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

CREDIT_NOTE = (
    "the validated payment is credited toward the payer's "
    "next run; under the mock validation profile no funds "
    "moved, and the failed run's signature is retired"
)

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _ulid() -> str:
    """A minimal ULID: 48-bit millisecond timestamp + 80-bit
    randomness, Crockford base32 — time-ordered and unique
    across doors, per the run-ID contract."""
    value = (int(time.time() * 1000) << 80) | secrets.randbits(80)
    chars = []
    for _ in range(26):
        chars.append(_CROCKFORD[value & 0x1F])
        value >>= 5
    return "".join(reversed(chars))


def new_run_id() -> str:
    return f"UZE-RES-{_ulid()}"


class ResearchNotConfigured(Exception):
    pass


class ResearchTimeout(Exception):
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
    try:
        with httpx.Client(trust_env=False, timeout=30.0) as client:
            resp = client.post(
                f"{_provider_base()}{path}",
                json=payload,
                headers={
                    "x-api-key": key,
                    "Content-Type": "application/json",
                },
            )
    except httpx.TimeoutException as exc:
        raise ResearchTimeout() from exc
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
    ResearchTimeout / ResearchUpstreamError; callers shape
    the HTTP answer."""
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


# ------------------------------------------------------------- run records


def _signature_hash(header_value: str) -> str:
    return hashlib.sha256(header_value.encode()).hexdigest()


def find_run(session: Session, run_id: str) -> tuple[dict[str, Any], str] | None:
    """(payload, actor) for a research run ID, or None. Used
    by cross-service composition: a run may be referenced by
    the identity that owns it, and by no one else."""
    row = (
        session.query(models.EventLog)
        .filter(models.EventLog.aggregate_type == "research")
        .filter(models.EventLog.payload["run_id"].as_string() == run_id)
        .order_by(models.EventLog.id.desc())
        .first()
    )
    if row is None:
        return None
    return row.payload, row.actor


def _prior_by_signature(
    session: Session, signature_hash: str
) -> dict[str, Any] | None:
    row = (
        session.query(models.EventLog)
        .filter(models.EventLog.aggregate_type == "research")
        .filter(
            models.EventLog.payload["signature_hash"].as_string()
            == signature_hash
        )
        .order_by(models.EventLog.id.desc())
        .first()
    )
    return row.payload if row is not None else None


def _log(
    session: Session,
    *,
    event_type: str,
    kind: str,
    door: str,
    actor: str,
    run_id: str,
    payment: dict[str, Any],
    extra: dict[str, Any],
) -> None:
    payload: dict[str, Any] = {
        "provider": "exa",  # internal audit only
        "door": door,
        "kind": kind,
        "run_id": run_id,
        "payment": payment,
    }
    payload.update(extra)
    session.add(
        models.EventLog(
            aggregate_type="research",
            aggregate_id=kind,
            event_type=event_type,
            actor=actor,
            payload=payload,
        )
    )
    session.commit()


def _receipt(auth: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": True,
        "mock": True,
        "network": auth["network"],
        "transaction": "mock:" + auth["signature"].removeprefix("mock:")[:16],
        "payer": auth["payer"],
    }


def _execute(
    session: Session,
    *,
    door: str,
    auth: dict[str, Any],
    signature_hash: str,
    kind_hint: str,
    fn: Callable[[], dict[str, Any]],
) -> tuple[int, dict[str, Any], dict[str, Any] | None]:
    """The paid execution core shared by the API and MCP
    doors. Returns (http_status, body, receipt_or_None).

    Idempotency: a signature that already completed returns
    its original run's result; a signature consumed by a
    failed run is refused (payment_invalid) so a retry pays
    a fresh quote under a new run ID."""
    prior = _prior_by_signature(session, signature_hash)
    if prior is not None:
        if prior.get("status") == "completed":
            body = dict(prior["result"])
            body["run_id"] = prior["run_id"]
            body["idempotent_replay"] = True
            body["payment"] = prior["payment_receipt"]
            return 200, body, prior["payment_receipt"]
        return 402, {
            "error": "PAYMENT_SIGNATURE_CONSUMED",
            "error_code": "payment_invalid",
            "run_id": prior["run_id"],
            "note": (
                "this payment signature was consumed by a "
                "failed run and cannot be reused; pay a fresh "
                "quote to retry — the failed run carries a "
                "credit note"
            ),
        }, None

    run_id = new_run_id()
    receipt = _receipt(auth)
    payment_log = {
        "profile": "x402-mock",
        "mock": True,
        "network": auth["network"],
        "asset": auth["asset"],
        "amountAtomic": auth["amount"],
    }
    try:
        result = fn()
    except (ResearchTimeout, ResearchUpstreamError) as exc:
        error_code = (
            "provider_timeout"
            if isinstance(exc, ResearchTimeout)
            else "provider_error"
        )
        _log(
            session,
            event_type="research.run_failed",
            kind=kind_hint,
            door=door,
            actor=auth["payer"],
            run_id=run_id,
            payment=payment_log,
            extra={
                "status": "failed",
                "signature_hash": signature_hash,
                "error_code": error_code,
                "credit_note": CREDIT_NOTE,
            },
        )
        return 502, {
            "error": "RESEARCH_UPSTREAM_ERROR",
            "error_code": error_code,
            "run_id": run_id,
            "credit_note": CREDIT_NOTE,
        }, None
    body = _public(result)
    _log(
        session,
        event_type="research.metered_call",
        kind=result["kind"],
        door=door,
        actor=auth["payer"],
        run_id=run_id,
        payment=payment_log,
        extra={
            "status": "completed",
            "signature_hash": signature_hash,
            "upstream_request_id": result.get("_upstream_request_id"),
            "result_count": len(result.get("results", [])),
            "result": body,
            "payment_receipt": receipt,
        },
    )
    body["run_id"] = run_id
    body["payment"] = receipt
    return 200, body, receipt


def run_via_gateway(session: Session, *, query: str, sender: str) -> dict[str, Any]:
    """The email door's entry point: same provider function,
    same event log, its own run ID; the gateway demo profile
    is unmetered and the log row says so."""
    run_id = new_run_id()
    result = search_web(query)
    body = _public(result)
    _log(
        session,
        event_type="research.metered_call",
        kind=result["kind"],
        door="email",
        actor=sender,
        run_id=run_id,
        payment={"profile": "gateway-demo-unmetered", "mock": True},
        extra={
            "status": "completed",
            "signature_hash": None,
            "upstream_request_id": result.get("_upstream_request_id"),
            "result_count": len(result.get("results", [])),
            "result": body,
        },
    )
    body["run_id"] = run_id
    return body


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
    """The x402 gate, shared by the API endpoints and the
    MCP surface. Returns (auth, error_response): exactly one
    of the two is set."""
    config = x402.pricing_config()
    if config is None:
        return None, JSONResponse(
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
        return None, JSONResponse(
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
        return None, JSONResponse(
            status_code=402,
            content=required,
            headers={"PAYMENT-REQUIRED": x402.encode_header(required)},
        )
    ok, reason, auth = x402.validate_payment_signature(header_value, config)
    if not ok:
        content = dict(required)
        content["error"] = f"invalid PAYMENT-SIGNATURE: {reason}"
        return None, JSONResponse(
            status_code=402,
            content=content,
            headers={"PAYMENT-REQUIRED": x402.encode_header(required)},
        )
    return auth, None


def _run(request: Request, session: Session, kind: str, description: str, fn):
    auth, error = _gate(request, f"/api/v1/research/{kind}", description)
    if error is not None:
        return error
    status, body, receipt = _execute(
        session,
        door="api",
        auth=auth,
        signature_hash=_signature_hash(request.headers["payment-signature"]),
        kind_hint=kind,
        fn=fn,
    )
    headers = {}
    if receipt is not None:
        headers["PAYMENT-RESPONSE"] = x402.encode_header(receipt)
    return JSONResponse(status_code=status, content=body, headers=headers)


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
