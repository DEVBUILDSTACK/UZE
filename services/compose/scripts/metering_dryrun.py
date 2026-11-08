"""Metering dry run — Sprint 1.5 Day 5's end-to-end evidence.

Walks the filed x402/x401 mock flow through the real API (TestClient
over the real migrated schema), printing every step:

  Run 1 — the demo fixture spec (tier ANY):
    attempt -> 402 + payment requirements -> mock authorization ->
    retry -> 200, mock transfer read back from the EventLog.

  Run 2 — a tier C spec (identity-gated):
    attempt -> 402 -> authorization -> 401 identity challenge ->
    identity presented -> 200 with the verified credential shape.

  Plus the /identity/verify stub shapes (incomplete -> 401,
  complete -> verified credential).

The inference outcome printed is whatever this environment honestly
produces (no NEARAI_API_KEY -> "unavailable"). The script asserts
only the protocol invariants.

    PYTHONPATH=src ~/workspace/tools/composevenv/bin/python \
        scripts/metering_dryrun.py

Uses the throwaway demonstration database, reset and migrated
exactly as the test suite does.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMPOSE_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(COMPOSE_DIR, "src"))
sys.path.insert(0, os.path.join(COMPOSE_DIR, "src", "generated"))

os.environ.setdefault(
    "COMPOSE_DATABASE_URL",
    "postgresql+psycopg://postgres@127.0.0.1:55433/uzemarkets-compose",
)


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
    env = dict(os.environ)
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=COMPOSE_DIR, env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr[-400:]


def main() -> int:
    reset_db()
    with open(os.path.join(HERE, "fixtures", "sprint15_demo.json")) as fh:
        fixture = json.load(fh)

    import db
    import metering
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
    agent = "recon.uzemarkets-talent.testnet"

    def post_spec(tier: str) -> dict:
        body = copy.deepcopy(fixture["spec"])
        body.pop("posterLabel", None)
        body["tier"] = tier
        r = client.post("/api/v1/specs", json=body)
        assert r.status_code == 201, r.text
        return r.json()

    # --- Run 1: tier ANY — the x402 flow alone. ---
    spec = post_spec("ANY")
    r = client.post("/api/v1/metered/analyze", json={"specId": spec["id"]})
    assert r.status_code == 402, r.text
    req = r.json()["accepts"][0]
    print(f"[run 1] attempt -> 402; requirements: scheme={req['scheme']} "
          f"network={req['network']} amount={req['maxAmountRequired']} "
          f"asset={req['asset'][:8]}… payTo={req['payTo'][:8]}…")

    r = metering.call_metered_analyze(client, spec["id"], agent)
    assert r.status_code == 200, r.text
    body = r.json()
    print(f"[run 1] authorized retry -> 200; payment={body['payment']['status']} "
          f"(mock, event #{body['payment']['eventLogId']}), "
          f"inference={body['inference']['status']}")

    with db.session() as s:
        ev = (s.query(models.EventLog)
              .filter_by(event_type="metering.mock_transfer",
                         aggregate_id=spec["id"]).one())
    assert ev.payload["mock"] is True
    print(f"[run 1] EventLog metering.mock_transfer verified: "
          f"amount={ev.payload['amountBaseUnits']} payer={ev.payload['payer']} "
          f"mock={ev.payload['mock']}")

    # --- Run 2: tier C — x402 then the x401 identity gate. ---
    spec_c = post_spec("C")
    r = client.post(
        "/api/v1/metered/analyze", json={"specId": spec_c["id"]},
        headers={"X-PAYMENT": metering.build_mock_authorization(agent)},
    )
    assert r.status_code == 401, r.text
    print(f"[run 2] paid attempt on tier C spec -> 401; "
          f"required={r.json()['required']}")

    r = metering.call_metered_analyze(client, spec_c["id"], agent)
    assert r.status_code == 200, r.text
    cred = r.json()["identity"]["credential"]
    print(f"[run 2] identity presented -> 200; credential: "
          f"type={cred['type']} issuer={cred['issuer']} "
          f"subject={cred['subject'][:24]}…")

    # --- The /identity/verify stub shapes. ---
    r = client.post("/api/v1/identity/verify",
                    json={"subject": "syndicate.acme.testnet"})
    assert r.status_code == 401
    r = client.post("/api/v1/identity/verify", json={
        "subject": "syndicate.acme.testnet",
        "credentialType": "near-account-attestation",
        "attestation": "mock-attested",
    })
    assert r.status_code == 200 and r.json()["verified"] is True
    print("[verify] incomplete payload -> 401; complete -> verified "
          "credential shape (mock)")

    print("METERING DRY RUN COMPLETE — outcomes as printed above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
