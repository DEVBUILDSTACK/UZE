"""Seed the demonstration database with the Sprint 1.5 demo fixture.

Reset + migrate + the 10 micro-regions + the Aloft Brickell spec +
both bids, through the real API (TestClient), chain gate CLOSED —
this seeds the read-model the Day 6 human surface renders. (The
live chain flow is scripts/settle_dryrun.py / the demo recording.)

    PYTHONPATH=src ~/workspace/tools/composevenv/bin/python \
        scripts/seed_demo.py

Prints the spec id and the page/API URLs for the seeded data.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from metering_dryrun import reset_db  # noqa: E402  (shared reset+migrate)


def main() -> int:
    os.environ.pop("COMPOSE_NEAR_CHAIN", None)
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
    body = {k: v for k, v in fixture["spec"].items() if k != "posterLabel"}
    r = client.post("/api/v1/specs", json=body)
    assert r.status_code == 201, r.text
    spec = r.json()
    for bid in fixture["bids"]:
        b = {k: v for k, v in bid.items() if k != "bidderLabel"}
        b["intentId"] = spec["id"]
        r = client.post("/api/v1/bids", json=b)
        assert r.status_code == 201, r.text

    print(f"spec id: {spec['id']}")
    print(f"  human page : /specs/{spec['id']}")
    print(f"  agent JSON : /api/v1/specs/{spec['id']}")
    print(f"  region page: /micro-regions/miami-brickell")
    print(f"  talent     : /talent/recon.uzemarkets-talent.testnet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
