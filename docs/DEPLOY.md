# UZE Deploy Guide

Docker image structure and deploy targets for the UZE monorepo.
Approach lifted from the Fundio Docker model (see `repo-scan/ANALYSIS.md` §7),
fixed for production: healthchecks, non-root users, no baked secrets, PORT-aware.

## Architecture

```
apps/uze-web (Next.js standalone) ──HTTPS──▶ services/api (FastAPI :8000)
        │                                            │
   Vercel (prod web)                          Cloud Run (prod api)
        │                                     Artifact Registry
        └──────────────▶ Neon Postgres ◀──────────────┘
                        (DATABASE_URL pooled / DIRECT_URL migrations)
                              +
                        Redis (REDIS_URL — cache/queues/rate limits)
```

Local dev mirrors this with `docker-compose.yml` (local Postgres + Redis containers).

## One-time setup (James)

1. **Neon** (neon.tech, signed in as dev.build@decensat.org): create project `uze`,
   copy the **pooled** connection string → `DATABASE_URL`, and the **direct**
   string → `DIRECT_URL`.
2. **Redis**: Upstash or GCP Memorystore → `REDIS_URL`.
3. **GCP**: project + Artifact Registry repo (`uze-images`) + Cloud Run API enabled.
   Create a deploy service account; store its JSON as GitHub secret `GCP_SA_KEY`.
4. **Secret Manager**: store `DATABASE_URL`, `DIRECT_URL`, `REDIS_URL`, `SECRET_KEY`
   as secrets (`uze-database-url`, etc. — names must match `deploy.yml`).
5. **Vercel**: import `apps/uze-web` as a project; set `NEXT_PUBLIC_API_BASE_URL`
   to the Cloud Run API URL; store `VERCEL_TOKEN`/`VERCEL_ORG_ID`/`VERCEL_PROJECT_ID`
   as GitHub secrets.
6. Copy `.env.example` → `.env` locally and fill in.

## Local dev

```bash
docker compose up --build
# web → http://localhost:3000, api → http://localhost:8000, docs → /docs
```

## Deploy

Push to `main`:
- `api-cloudrun` job builds `services/api/Dockerfile`, pushes to Artifact Registry,
  deploys to Cloud Run (prestart.sh waits for Neon → `prisma db push` → serves).
- `web-vercel` job deploys `apps/uze-web` to Vercel production.

## Conventions (from the repo scan — do not regress)

- One canonical env name per concept (`.env.example` is the source of truth).
- Secrets never baked as Docker `ARG`s — runtime env via Secret Manager only.
- Browser code never hardcodes `localhost` — always `NEXT_PUBLIC_API_BASE_URL`.
- Prisma is the migration authority for the API's tables. Next.js/Drizzle owns
  only its own tables, if any — never two ORMs migrating the same tables.
- Health: `/health` (liveness) and `/health/deep` (postgres + redis) on the API;
  `/api/health` on web.
