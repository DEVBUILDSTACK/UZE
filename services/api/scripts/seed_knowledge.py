#!/usr/bin/env python3
"""Seed the RAG knowledge base from services/api/knowledge/*.json packs.

Each pack: {"source": ..., "title": ..., "chunks": [...]}.
Posts each pack to POST {API_URL}/rag/ingest with a bearer JWT.

Usage:
  API_URL=https://api.uze.fi JWT=<service-token> \
    python scripts/seed_knowledge.py [--pack shadow-accounts-strk20]

Env:
  API_URL   Base URL of the UZE API (no trailing slash).
  JWT       Bearer token for an authenticated (service) user.
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def ingest(api_url: str, jwt: str, source: str, chunks: list[str]) -> dict:
    req = urllib.request.Request(
        f"{api_url.rstrip('/')}/rag/ingest",
        data=json.dumps({"source": source, "chunks": chunks}).encode(),
        headers={
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", help="Only seed this pack (filename stem)")
    args = ap.parse_args()

    api_url = os.environ.get("API_URL", "").strip()
    jwt = os.environ.get("JWT", "").strip()
    if not api_url or not jwt:
        print("API_URL and JWT env vars are required.", file=sys.stderr)
        return 2

    packs = sorted(KNOWLEDGE_DIR.glob("*.json"))
    if args.pack:
        packs = [p for p in packs if p.stem == args.pack]
        if not packs:
            print(f"No pack named {args.pack!r}.", file=sys.stderr)
            return 2

    for pack_path in packs:
        pack = json.loads(pack_path.read_text())
        source = pack.get("source", pack_path.stem)
        chunks = pack.get("chunks", [])
        if not chunks:
            print(f"Skipping {pack_path.name}: no chunks.")
            continue
        result = ingest(api_url, jwt, source, chunks)
        stored = result.get("data", {}).get("stored", "?")
        print(f"{pack_path.name}: stored {stored} chunks (source={source})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
