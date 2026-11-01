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

echo "Ensuring pgvector extension..."
python - <<'EOF'
import os, urllib.parse, psycopg2
url = os.environ["DIRECT_URL"] or os.environ["DATABASE_URL"]
p = urllib.parse.urlparse(url)
conn = psycopg2.connect(host=p.hostname, port=p.port or 5432,
                        user=p.username, password=p.password,
                        dbname=p.path.lstrip("/"), sslmode="require")
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
print("pgvector ready")
EOF

echo "Running Prisma migrations..."
prisma db push --accept-data-loss=false

echo "Starting API..."
exec uvicorn src.api:create_app --factory \
  --host 0.0.0.0 --port "${PORT:-8000}"
