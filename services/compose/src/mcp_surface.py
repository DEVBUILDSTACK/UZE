"""MCP surface for UZE Research (hardening build, 2026-11-13).

POST /api/v1/mcp — a minimal MCP (JSON-RPC 2.0) surface
exposing UZE_Research_Query, delegating
to research._execute so the MCP door shares the API door's
provider functions, x402 gate, run contract, and event log
(door="mcp"). A second tool, UZE_Underwrite, exposes the
persisted multi-year underwrite (underwrite_reports) through
the same x402 gate. Supported methods: initialize, ping,
tools/list, tools/call. Notifications (no id) are accepted
and answered with an empty 202.

Honest scope: this is the manifest + tool-call surface the
explainer section 7 specifies — tool entry with input and
output schemas, the Tier 1 gate, permitted rails (Base and
Solana; the agentic surface only), and the pricing RULE
(quoted per request; no static price). It is not a general
MCP host: no resources, no prompts, no sampling. Payment
rides the same PAYMENT-SIGNATURE header convention as the
API door; an unpaid tools/call returns the x402
payment-required payload as its result content.
"""

from __future__ import annotations

import json
import re
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

import metering
import research
from db import get_session

router = APIRouter(prefix="/api/v1", tags=["mcp"])

TOOL_NAME = "UZE_Research_Query"
_SNIPPET_CAP = 300

TOOL = {
    "name": TOOL_NAME,
    "description": (
        "UZE Research — white-labeled web and financial data "
        "search. Tier 1: an x402 payment is quoted per request "
        "and the call runs on the payment signature."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "vertical": {
                "type": "string",
                "enum": ["financial", "general", "sec_filings"],
                "default": "general",
            },
            "num_results": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
                "default": 5,
            },
        },
        "required": ["query"],
    },
    "outputSchema": {
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                        "snippet": {"type": "string"},
                        "source_date": {"type": ["string", "null"]},
                    },
                    "required": ["title", "url", "snippet", "source_date"],
                },
            }
        },
        "required": ["results"],
    },
    "_meta": {
        "tier_gate": "Tier 1",
        "surface": "agentic",
        "permitted_rails": ["Base", "Solana"],
        "pricing_rule": (
            "quoted per request in the x402 payment-required "
            "response; no static price is posted"
        ),
    },
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _base_lane_email(request: Request) -> str | None:
    """Base-builder identity for the underwrite tool (NoGate
    alignment, James's Tier-1 taxonomy, 2026-11-13): an
    X-IDENTITY header carrying an email address — the raw
    address, or the subject of a payload — is the caller's
    identity at this band. No attestation is requested or
    required here; the gate's credential is the x402 payment
    signature, exactly as for UZE_Research_Query."""
    header = request.headers.get("x-identity")
    if not header:
        return None
    raw = header.strip()
    if _EMAIL_RE.match(raw):
        return raw
    decoded = metering._decode_header(raw)
    if isinstance(decoded, dict):
        subject = decoded.get("subject")
        if isinstance(subject, str) and _EMAIL_RE.match(subject.strip()):
            return subject.strip()
    return None


UNDERWRITE_TOOL_NAME = "UZE_Underwrite"

UNDERWRITE_TOOL = {
    "name": UNDERWRITE_TOOL_NAME,
    "description": (
        "UZE Underwrite — multi-year T-12 analysis through "
        "the seven-bucket chart of accounts, per-unit comp "
        "benchmarking, findings and a value-creation plan; "
        "every call persists a report and returns its "
        "receipt; an NOI Assuratie is issued when the "
        "subject declares a micro-region in the reference "
        "table. Base builder band (NoGate): identity is "
        "your email address (sender_email, or an X-IDENTITY "
        "header carrying it) and the credential is the "
        "x402 payment signature — no attestation, no "
        "spend cap at this band."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "years": {
                "type": "array",
                "items": {"type": "object"},
                "minItems": 1,
            },
            "context": {"type": "object"},
            "subject_profile": {"type": "object"},
            "comps": {"type": "array"},
            "comp_threshold_pct": {"type": "number"},
            "sender_email": {"type": "string"},
            "prior_report_id": {"type": "string"},
            "contribute_comps": {"type": "boolean", "default": False},
        },
        "required": ["years"],
    },
    "outputSchema": {
        "type": "object",
        "properties": {
            "receipt": {"type": "object"},
            "summary": {"type": "object"},
        },
        "required": ["receipt", "summary"],
    },
    "_meta": {
        "tier_gate": "Tier 1",
        "surface": "agentic",
        "permitted_rails": ["Base", "Solana"],
        "pricing_rule": (
            "quoted per request in the x402 payment-required "
            "response; no static price is posted"
        ),
    },
}


def _rpc_result(req_id: Any, result: dict[str, Any]) -> JSONResponse:
    return JSONResponse(
        content={"jsonrpc": "2.0", "id": req_id, "result": result}
    )


def _rpc_error(req_id: Any, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        content={
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }
    )


def _map_results(body: dict[str, Any]) -> list[dict[str, Any]]:
    """The tool's declared output shape, exactly: title, url,
    snippet, source_date — nothing else rides along."""
    mapped = []
    for r in body.get("results", []):
        mapped.append(
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "snippet": (r.get("text") or "")[:_SNIPPET_CAP],
                "source_date": r.get("published_date"),
            }
        )
    return mapped


@router.post("/mcp")
async def mcp_endpoint(
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        rpc = await request.json()
    except Exception:
        return _rpc_error(None, -32700, "request body is not valid JSON")
    req_id = rpc.get("id")
    method = rpc.get("method")
    if req_id is None:
        # A notification: accepted, no response body.
        return Response(status_code=202)
    if method == "initialize":
        return _rpc_result(
            req_id,
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "UZE Research", "version": "1.0.0"},
            },
        )
    if method == "ping":
        return _rpc_result(req_id, {})
    if method == "tools/list":
        return _rpc_result(req_id, {"tools": [TOOL, UNDERWRITE_TOOL]})
    if method != "tools/call":
        return _rpc_error(req_id, -32601, f"method not supported: {method}")

    params = rpc.get("params") or {}
    if params.get("name") == UNDERWRITE_TOOL_NAME:
        # UZE_Underwrite branch: validation precedes the
        # gate, exactly as the research branch validates
        # its query before gating.
        u_args = params.get("arguments") or {}
        u_years = u_args.get("years")
        if not isinstance(u_years, list) or not u_years:
            return _rpc_error(
                req_id,
                -32602,
                "missing required field: years (non-empty array)",
            )
        # The shared gate's only credential is the payment
        # signature — there is no attestation step in it, at
        # either tool. That IS the base-builder rule (NoGate
        # alignment, 2026-11-13); the caller's email identity
        # is resolved below, never gated on.
        auth, error = research._gate(
            request, "/api/v1/mcp", "UZE Underwrite — MCP"
        )
        if error is not None:
            # Same in-band shape as the research branch:
            # the gate's answer becomes the tool result
            # content so the calling agent sees the quote.
            payload = json.loads(error.body)
            return _rpc_result(
                req_id,
                {
                    "content": [
                        {"type": "text", "text": json.dumps(payload)}
                    ],
                    "isError": False,
                    "_meta": {
                        "http_status": error.status_code,
                        "payment_required": error.status_code == 402,
                    },
                },
            )
        import underwrite_reports

        u_payload = {
            "years": u_years,
            "context": u_args.get("context"),
            "subject_profile": u_args.get("subject_profile"),
            "comps": u_args.get("comps"),
            "comp_threshold_pct": u_args.get("comp_threshold_pct"),
            "sender_email": u_args.get("sender_email")
            or _base_lane_email(request),
            "prior_report_id": u_args.get("prior_report_id"),
            "contribute_comps": bool(u_args.get("contribute_comps", False)),
        }
        result = underwrite_reports.run_multiyear_ingest(
            session, u_payload, door=underwrite_reports.DOOR_MCP
        )
        receipt = result["receipt"]
        findings = (result.get("comp_benchmark") or {}).get(
            "findings", []
        )
        top_findings = [
            {
                "line": f.get("line"),
                "classification": f.get("classification"),
                "annualized_impact_usd": f.get("annualized_impact_usd"),
            }
            for f in sorted(
                findings,
                key=lambda f: abs(f.get("annualized_impact_usd") or 0),
                reverse=True,
            )[:3]
        ]
        summary = {
            "periods": [
                {"period": p["period"], "noi": p["noi"]}
                for p in result["periods"]
            ],
            "top_findings": top_findings,
            "claim_id": receipt["claim_id"],
            "delta_status": (result.get("delta") or {}).get("status"),
        }
        structured = {"receipt": receipt, "summary": summary}
        return _rpc_result(
            req_id,
            {
                "content": [
                    {"type": "text", "text": json.dumps(structured)}
                ],
                "structuredContent": structured,
                "isError": False,
            },
        )
    if params.get("name") != TOOL_NAME:
        return _rpc_error(
            req_id, -32602, f"unknown tool: {params.get('name')}"
        )
    args = params.get("arguments") or {}
    query = str(args.get("query") or "").strip()
    if not query:
        return _rpc_error(
            req_id,
            -32602,
            "missing required field: query (non-empty string)",
        )
    vertical = args.get("vertical") or "general"
    if vertical not in ("financial", "general", "sec_filings"):
        return _rpc_error(
            req_id,
            -32602,
            "invalid field: vertical must be financial, general, "
            "or sec_filings",
        )
    num_results = args.get("num_results") or 5

    auth, error = research._gate(request, "/api/v1/mcp", "UZE Research — MCP")
    if error is not None:
        # The gate's answer (402 payment-required, or a
        # labelled 503) becomes the tool result content so
        # the calling agent sees the quote in-band.
        payload = json.loads(error.body)
        return _rpc_result(
            req_id,
            {
                "content": [
                    {"type": "text", "text": json.dumps(payload)}
                ],
                "isError": False,
                "_meta": {
                    "http_status": error.status_code,
                    "payment_required": error.status_code == 402,
                },
            },
        )

    # The financial-report category is where SEC filings
    # surface (verified live, 2026-11-13), so both financial
    # verticals ride it; general search is uncategorized.
    category = (
        research.FINANCIAL_CATEGORY if vertical != "general" else None
    )
    status, body, _receipt = research._execute(
        session,
        door="mcp",
        auth=auth,
        signature_hash=research._signature_hash(
            request.headers["payment-signature"]
        ),
        kind_hint="search",
        fn=lambda: research.search_web(
            query, num_results, category=category, include_text=True
        ),
    )
    if status != 200:
        return _rpc_result(
            req_id,
            {
                "content": [{"type": "text", "text": json.dumps(body)}],
                "isError": True,
                "_meta": {"http_status": status},
            },
        )
    structured = {"run_id": body["run_id"], "results": _map_results(body)}
    return _rpc_result(
        req_id,
        {
            "content": [
                {"type": "text", "text": json.dumps(structured)}
            ],
            "structuredContent": structured,
            "isError": False,
        },
    )
