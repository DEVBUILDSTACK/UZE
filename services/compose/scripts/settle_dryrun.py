"""Live settle dry run — Sprint 1.5 Day 3's end-to-end evidence.

Runs the filed flow twice through the real API (TestClient over the
real migrated schema), chain gate OPEN:

  Run 1 — the demo fixture (Aloft Brickell; agent bid $4,200 wins).
  Run 2 — a dry-run-sized spec (human bid wins at an amount the
          payer's devnet USDC balance actually covers).

Each run: POST spec -> POST bids x2 -> GET bids -> POST settle, then
the database state is read back and printed. Outcomes are whatever
the chain says they are: SETTLED with a Solana receipt when funded,
SELECTED + settlement "signed" (MPC signature obtained over the real
transfer message, broadcast held for funds) when not. The script
asserts only the invariants that must hold either way.

    COMPOSE_NEAR_CHAIN=1 PYTHONPATH=src:tests \
        ~/workspace/tools/composevenv/bin/python scripts/settle_dryrun.py

Uses the throwaway demonstration database (uzemarkets-compose on
the local pgserver PostgreSQL), reset and migrated exactly as the
test suite does.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMPOSE_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(COMPOSE_DIR, "src"))
sys.path.insert(0, os.path.join(COMPOSE_DIR, "src", "generated"))

os.environ.setdefault("COMPOSE_NEAR_CHAIN", "1")
os.environ.setdefault(
    "COMPOSE_DATABASE_URL",
    "postgresql+psycopg://postgres@127.0.0.1:55433/uzemarkets-compose",
)

import chain_sig  # noqa: E402
import settlement  # noqa: E402


def reset_db() -> None:
    import sqlalchemy
    from sqlalchemy import text

    admin = sqlalchemy.create_engine(
        "postgresql+psycopg://postgres@127.0.0.1:55433/postgres",
        isolation_level="AUTOCOMMIT",
    )
    with admin.connect() as c:
        c.execute(text('DROP DATABASE IF EXISTS "uzemarkets-compose"'))
        c.execute(text('CREATE DATABASE "uzemarkets-compose"'))
    admin.dispose()
    env = dict(os.environ, COMPOSE_DATABASE_URL=os.environ["COMPOSE_DATABASE_URL"])
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=COMPOSE_DIR, env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr[-400:]


def payer_usdc_balance() -> int:
    import aiohttp

    async def go():
        payer, _ = chain_sig.derive_address(settlement.OPERATOR_ACCOUNT)
        ata = settlement.ata_address(payer)
        async with aiohttp.ClientSession(trust_env=True) as s:
            try:
                bal = await settlement._rpc(s, "getTokenAccountBalance", [ata])
                return int(bal["value"]["amount"])
            except RuntimeError:
                return 0

    return asyncio.run(go())


def run_flow(client, fixture, spec_body, bids, winner_idx, label) -> dict:
    resp = client.post("/api/v1/specs", json=spec_body)
    assert resp.status_code == 201, resp.text
    spec = resp.json()
    print(f"[{label}] spec {spec['id'][:8]}… chain={spec['chain']}")
    posted = []
    for bid in bids:
        body = {k: v for k, v in bid.items() if k != "bidderLabel"}
        body["intentId"] = spec["id"]
        r = client.post("/api/v1/bids", json=body)
        assert r.status_code == 201, r.text
        posted.append(r.json())
    listed = client.get(f"/api/v1/specs/{spec['id']}/bids").json()
    assert len(listed) == 2
    r = client.post(
        "/api/v1/settle",
        json={"intentId": spec["id"], "bidId": posted[winner_idx]["id"]},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    st = body["settlement"]
    print(f"[{label}] settle -> spec {body['spec']['status']}, "
          f"match {body['match']['state']}, settlement {st['status']}"
          + (f", solanaTx {st.get('solanaTx')}" if st.get("solanaTx") else "")
          + (f" ({st.get('reason')})" if st.get("reason") else ""))
    assert body["match"]["bidId"] == posted[winner_idx]["id"]
    if st["status"] == "settled":
        assert body["spec"]["status"] == "SETTLED"
        assert body["match"]["settlementRef"] == st["solanaTx"]
    elif st["status"] == "signed":
        assert body["spec"]["status"] == "SELECTED"
    return body


def main() -> int:
    reset_db()
    with open(os.path.join(HERE, "fixtures", "sprint15_demo.json")) as fh:
        fixture = json.load(fh)

    import db
    import models
    from app import create_app
    from fastapi.testclient import TestClient

    session = db.session()
    for row in fixture["microRegions"]:
        session.add(models.MicroRegion(id=row["id"], label=row["label"],
                                       metro=row["metro"], region=row["region"]))
    session.commit()
    session.close()

    client = TestClient(create_app())
    balance = payer_usdc_balance()
    print(f"payer devnet USDC balance: {balance} base units "
          f"({balance / 1e6} USDC)")

    run_flow(client, fixture, fixture["spec"], fixture["bids"], 1,
             "run 1: demo fixture, agent wins")

    # Run 2 sized to the payer's real balance (whole USDC, min 1).
    sized = max(1, int(balance // 1_000_000))
    spec2 = dict(fixture["spec"])
    spec2["budgetMinUsdc"] = 1
    spec2["budgetMaxUsdc"] = sized + 2
    bids2 = [
        {"bidderAccount": "treasury.uzemarkets-talent.testnet",
         "bidderKind": "human", "amountUsdc": sized, "etaHours": 1440,
         "onSiteDays": 25, "remoteDays": 35, "payload": {"dryRun": True}},
        {"bidderAccount": "recon.uzemarkets-talent.testnet",
         "bidderKind": "agent", "amountUsdc": sized + 2, "etaHours": 48,
         "onSiteDays": 0, "remoteDays": 2, "payload": {"dryRun": True}},
    ]
    run_flow(client, fixture, spec2, bids2, 0,
             f"run 2: balance-sized ({sized} USDC), human wins")
    print("DRY RUNS COMPLETE — outcomes as printed above are the chain's own.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
