#!/bin/sh
# prestart.sh — wait for Postgres, run Prisma migrations, exec the server.
# Keeps Cloud Run revisions self-migrating. Never destructive: migrations
# only move forward (no drop/seed here — seed scripts are separate and manual).
set -e

echo "Waiting for Postgres..."
python - <<'EOF'
import os, socket, time, urllib.parse
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
host, port = url.hostname, url.port or 5432
for i in range(60):
    try:
        socket.create_connection((host, port), timeout=2).close()
        print(f"Postgres reachable at {host}:{port}")
        break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit("Postgres not reachable after 120s")
EOF

echo "Running Prisma migrations..."
prisma db push --accept-data-loss=false

echo "Starting API..."
exec uv run uvicorn src.api:create_app --factory \
  --host 0.0.0.0 --port "${PORT:-8000}"
