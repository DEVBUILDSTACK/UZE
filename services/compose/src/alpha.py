"""Alpha signup list — UZEguidance priced-market levels (owner directive, 2026-11-12).

The owner removed every posted price and replaced fixed pricing with
autonomous UZEguidance priced markets: the market bids the levels for
three participation levels —

  1. UZEBuilder
  2. UZEaffiliate
  3. UZEaffiliate actively onramped uzing TradeLayer or SigLayer

— and UZEmarkets honors the market levels PROSPECTIVELY, only for
KYB entities and KYC partner agents, and only for signups completed
inside the honored window:

  opens  2026-11-15 00:00 America/Los_Angeles
  closes 2027-01-12 22:59 America/Los_Angeles (10:59 PM PST)

The signup whitelists ONE self-custodial wallet per signup on one of:
Solana, NEAR (native), Robinhood (EVM), Ink (EVM), LightLink (EVM).
The whitelist is for the 2027 B2B and B2C event offerings, secondary
UZEticket tech offerings, and music-festival Frontier NFT collectibles
paired as payment tech innovation from the L2Launch Launchpad.

STORAGE (honest scope): v1 persists to an append-only JSONL file
(env ALPHA_SIGNUPS_PATH, default ./data/alpha-signups.jsonl) so the
list survives restarts. The DB table lands with the post-demo
migration batch the owner already deferred (same call as D6); the
record shape below is the migration shape. KYB/KYC at signup is an
ATTESTATION — status stays "attested" until ops verification; nothing
here performs KYB/KYC itself.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/alpha", tags=["alpha"])

LA = ZoneInfo("America/Los_Angeles")
WINDOW_OPEN = datetime(2026, 11, 15, 0, 0, 0, tzinfo=LA)
WINDOW_CLOSE = datetime(2027, 1, 12, 23, 0, 0, tzinfo=LA)  # last valid: 22:59:59

LEVELS = {"builder", "affiliate", "affiliate_onramped"}
ONRAMP_LANES = {"tradelayer", "siglayer"}
CHAINS = {"solana", "near", "robinhood", "ink", "lightlink"}

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SOLANA = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
_EVM = re.compile(r"^0x[0-9a-fA-F]{40}$")
_NEAR_IMPLICIT = re.compile(r"^[0-9a-f]{64}$")
_NEAR_NAMED = re.compile(
    r"^(([a-z0-9]+[-_])*[a-z0-9]+\.)*([a-z0-9]+[-_])*[a-z0-9]+$"
)


def valid_wallet(chain: str, address: str) -> bool:
    a = (address or "").strip()
    if chain == "solana":
        return bool(_SOLANA.match(a))
    if chain in ("robinhood", "ink", "lightlink"):
        return bool(_EVM.match(a))
    if chain == "near":
        if _NEAR_IMPLICIT.match(a):
            return True
        return 2 <= len(a) <= 64 and bool(_NEAR_NAMED.match(a))
    return False


def _store_path() -> Path:
    return Path(os.environ.get("ALPHA_SIGNUPS_PATH", "./data/alpha-signups.jsonl"))


_lock = threading.Lock()
_signups: list[dict[str, Any]] | None = None


def _load() -> list[dict[str, Any]]:
    global _signups
    if _signups is None:
        _signups = []
        p = _store_path()
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    _signups.append(json.loads(line))
    return _signups


def _signup_id(email: str, wallet: str) -> str:
    h = hashlib.sha256((email + "|" + wallet.lower()).encode()).hexdigest()[:12]
    return "uze-alpha-" + h


class AlphaSignupIn(BaseModel):
    level: str
    name: str
    email: str
    entity_name: str | None = None
    kyb_attested: bool = False
    kyc_attested: bool = False
    chain: str
    wallet_address: str
    onramp_lane: str | None = None


def _window(now_utc: datetime) -> tuple[bool, str]:
    now_la = now_utc.astimezone(LA)
    if now_la < WINDOW_OPEN:
        return False, "pre_window"
    if now_la >= WINDOW_CLOSE:
        return False, "post_window"
    return True, "in_window"


@router.post("/signups")
def create_signup(body: AlphaSignupIn):
    level = (body.level or "").strip().lower()
    if level not in LEVELS:
        raise HTTPException(status_code=422, detail="unknown level")
    chain = (body.chain or "").strip().lower()
    if chain not in CHAINS:
        raise HTTPException(status_code=422, detail="unknown chain")
    email = (body.email or "").strip().lower()
    if not _EMAIL.match(email):
        raise HTTPException(status_code=422, detail="a valid email is required")
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="a name is required")
    wallet = (body.wallet_address or "").strip()
    if not valid_wallet(chain, wallet):
        raise HTTPException(
            status_code=422,
            detail=f"wallet address does not match the {chain} format",
        )
    lane = (body.onramp_lane or "").strip().lower() or None
    if level == "affiliate_onramped":
        if lane not in ONRAMP_LANES:
            raise HTTPException(
                status_code=422,
                detail="the onramped affiliate level requires an onramp lane: tradelayer or siglayer",
            )
    elif lane is not None:
        raise HTTPException(
            status_code=422,
            detail="onramp_lane applies only to the affiliate_onramped level",
        )

    now = datetime.now(timezone.utc)
    in_window, window_state = _window(now)
    verified_track = bool(body.kyb_attested or body.kyc_attested)
    record = {
        "id": _signup_id(email, wallet),
        "level": level,
        "name": name,
        "email": email,
        "entity_name": (body.entity_name or "").strip() or None,
        "kyb_attested": bool(body.kyb_attested),
        "kyc_attested": bool(body.kyc_attested),
        "chain": chain,
        "wallet_address": wallet,
        "onramp_lane": lane,
        "created_at": now.isoformat(),
        "window_state": window_state,
        "in_honored_window": in_window,
        # Market levels are honored prospectively ONLY for KYB entities /
        # KYC partner agents whose signup lands inside the window.
        "honored": bool(in_window and verified_track),
        "verification_status": "attested" if verified_track else "none",
    }

    with _lock:
        rows = _load()
        for r in rows:
            if r["wallet_address"].lower() == wallet.lower():
                if r["email"] == email:
                    return {**r, "duplicate": True}
                raise HTTPException(
                    status_code=409,
                    detail="this wallet is already whitelisted under another email",
                )
        p = _store_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
        rows.append(record)
    return record


@router.get("/signups/count")
def signup_count():
    rows = _load()
    by_level: dict[str, int] = {}
    by_chain: dict[str, int] = {}
    for r in rows:
        by_level[r["level"]] = by_level.get(r["level"], 0) + 1
        by_chain[r["chain"]] = by_chain.get(r["chain"], 0) + 1
    return {
        "count": len(rows),
        "by_level": by_level,
        "by_chain": by_chain,
        "window": {
            "opens": WINDOW_OPEN.isoformat(),
            "closes_last_valid": "2027-01-12T22:59:59-08:00",
        },
    }
