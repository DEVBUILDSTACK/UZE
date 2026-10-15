# Secrets / Credentials Triage — UZE Deploy Pipeline

**Purpose:** single checklist of every credential the deploy pipeline needs,
where each comes from, who provides it, and its status.

**Security rule (hard):** this document records secret *names*, sources, and
status — **never secret values**. Values live only in GitHub Actions secrets
(repo Settings → Secrets and variables → Actions) and GCP Secret Manager.
No value is ever committed, pasted into docs, or stored in chat.

**How the pipeline uses them:** every push to `main` triggers the `Deploy`
workflow (`.github/workflows/deploy.yml`). Its `preflight` job fails fast when
any secret below is missing — that is the "failed in 3 seconds" notification.
When all are present, the workflow builds the API Docker image, pushes it to
GCP Artifact Registry, deploys to Cloud Run, and deploys `apps/uze-web` to
Vercel production.

---

## A. GitHub Actions secrets (repo Settings → Secrets and variables → Actions)

| Secret | Used by | Service / where to get it | Status |
|---|---|---|---|
| `GCP_SA_KEY` | Cloud Run deploy | **Google Cloud Console** → IAM & Admin → Service Accounts → create account (roles: Cloud Run Admin, Artifact Registry Writer, Secret Manager Secret Accessor) → Keys → Add key → JSON | ⬜ missing |
| `GCP_PROJECT_ID` | Cloud Run deploy | **Google Cloud Console** → project dashboard (e.g. `uze-prod-…`) | ⬜ missing |
| `GCP_REGION` | Cloud Run deploy | Your choice, e.g. `us-central1` | ⬜ missing |
| `ARTIFACT_REGISTRY_REPO` | Docker image push | **Google Cloud Console** → Artifact Registry → create Docker repository (e.g. `uze-images`) | ⬜ missing |
| `VERCEL_TOKEN` | Web frontend deploy | **Vercel dashboard** → Settings → Tokens → Create | ⬜ missing |
| `VERCEL_ORG_ID` | Web frontend deploy | **Vercel dashboard** → Settings → General (Team/Org ID) | ⬜ missing |
| `VERCEL_PROJECT_ID` | Web frontend deploy | **Vercel dashboard** → uze-web project → Settings → General (Project ID) | ⬜ missing |

## B. GCP Secret Manager secrets (runtime — read by Cloud Run, never in GitHub)

Referenced in `deploy.yml` as `uze-database-url`, `uze-direct-url`,
`uze-redis-url`, `uze-secret-key` (`--set-secrets`).

| Secret | Used by | Service / where to get it | Status |
|---|---|---|---|
| `uze-database-url` | API → Postgres | **Neon Console** → project → connection string (pooled) | ⬜ missing |
| `uze-direct-url` | API → Postgres (migrations) | **Neon Console** → project → connection string (direct) | ⬜ missing |
| `uze-redis-url` | API → Redis (OTP, cache) | **Upstash/Redis provider** → database → connection string | ⬜ missing |
| `uze-secret-key` | API → JWT signing | Generate: `openssl rand -hex 32` (any machine) | ⬜ missing |

## C. Application env (non-secret config, for reference)

`RESEND_API_KEY` (OTP email), `EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY`
(RAG) — wired at deploy time, tracked separately in `docs/DEPLOY.md`.

---

## Triage log

| Date | Event |
|---|---|
| 2026-10-14 | Triage doc created. All secrets missing — Deploy `preflight` failing on every push (by design). Secrets watch cron (`uze-deploy-secrets-watch`) active: auto re-runs Deploy when all 7 GitHub secrets land. |

**Owner of this doc:** whoever holds the GCP/Vercel/Neon accounts. Update the
Status column as each secret is added (⬜ missing → ✅ live). Values stay in
their vaults — this file only tracks *that* they exist.
