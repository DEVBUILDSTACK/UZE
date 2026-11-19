# UZE Dev Library — the reading room

**Talent Vertical, Phase 1 (reading room foundation).** Governing document: `docs/talent/BUILD-SCOPE-AND-PHASED-SPRINT-v1.0.md`.

A permissioned, human-browsable library of developer mocks — what has been built across DEVBUILDSTACK, explained for the blockchain developers we recruit (Lightning · NFT & wallets · NEAR AI · cross-chain EVM/Solana/Robinhood Chain · Lighter) and for the team after they join. **Descriptions and mocks only — source code never lives here.** GitHub is the source gate (per-repo collaborator access); this room is gated by an email allowlist, checked server-side before anything is served.

## How it works

- **The door** (`lib/gate.mjs`) — allowlist = the Developer List. A developer whose reading-room grant is active requests a one-time 6-digit code (15 minutes), verifies, and gets an HMAC session cookie carrying their session epoch. Any access-affecting change bumps the epoch and kills live sessions — the re-prompt behavior.
- **The catalog** — manifest-driven (`data/mocks.json`), newest first, filterable by **topic, date, full DEVBUILDSTACK repo name, and track**. Per-mock clearance lists restrict individual mocks; the track rule keeps INTERNAL_ONLY material out of external flows.
- **Proposals** — any signed-in developer can comment/suggest on a mock before holding any GitHub access. Accepted suggestions drive refinements on either side.
- **Naming sync** — the manifest is the single source for names. Renames keep the old slug as an alias (redirect, never a dead end) and append to the mock's version changelog.
- **The Developer List** (`lib/lifecycle.mjs`) — name, email, up to five realms of expertise, contact on **email and WhatsApp only**, stages prospect → contacted → recruiting → reading-room → source-access → revoked. Revocation is **reset to zero** (room, source, sessions) with the **chronicle preserved permanently** (`data/chronicle.json`, append-only).
- **Comms desk** — every send (invitations, codes, change notices, revocation notices) is written to `data/comms-log.json` from **desk@uzemarkets.com** with status `queued` until live dispatch is verified (G8). Nothing sends silently.

## Run

```
npm start        # PORT env, default 8734
npm test         # the Phase 1 exit-gate rehearsal (temp data dir; the real chronicle is never touched)
```

Env: `LIBRARY_SECRET` (session signing), `LIBRARY_MASTER_TOKEN` (master-control API), `LIBRARY_DATA` (data dir override). Master control is SoSem's surface: `/api/admin/*` with the `x-master-token` header.

## Data

`data/` holds the JSON store for the standalone deployment. The platform-side home is the PostgreSQL `talent` schema — migration `d1ce7a1e5001` in `services/compose/alembic/versions/` (verified by from-empty replay, 2026-11-18). The two stores carry the same contracts; the app store is the deployable unit for dev.uzemarkets.com, the schema is the core integration.

## Placement desk — merged program M1 (Scope 1 Phase 3, 2026-11-18)

- **Role × Realm taxonomy** (`lib/taxonomy.mjs`) — 11 Roles × 6 Realms; each developer holds up to five pairs ranked PRIMARY → QUINARY (I1: no duplicates, first pair is PRIMARY), enforced in the lifecycle ops, in the app DB (`developer_expertise` table with the same checks), and in the core `talent` schema (`talent_expertise`, migration `d1ce7a1e5001`). The realm list remains as the pairs' derived mirror. Admin filters: `GET /api/admin/developers?role=…&realm=…` (both = the exact pair).
- **Dual track** — `track` is INTERNAL_ONLY (Track A, never placed), EXTERNAL_PLACED (Track B), or EITHER; transitions are desk ops, logged (`track-set`).
- **Engagements** (`lib/engagements.mjs`) — Track B records with service AUG/OUTSTAFF/PLACE/PROJECT × deployment REMOTE/HYBRID/MIXED/ONSITE and a commercial model: OUTSTAFFING (UZE pays the talent, bills the client) or PLACEMENT (fee ≥ 1 month of salary; the client pays the individual) — never blended, enforced at open. Engagements run on invoice through M3 (amendment C2); no settlement machinery here. Core-side: `talent.client` + `talent.engagement` (migration `b7e3f1a9c204`).
- **Desk-mediated staffing (amendment S1)** — the desk makes the staffing call; the only hard rules are Track A is never placed and a revoked record cannot be staffed. State is **derived** from facts (OPEN → STAFFED → SIGNED → ACTIVE → CLOSED / CANCELLED), never written; every transition emits a chronicle Event.
- **Blind by construction** — the only client-facing projection (`GET /api/admin/engagements/:id/client-view`) shows skills only (pairs + realms) until the engagement has **both** a signature and a deposit recorded; only then does it carry the talent's name + email. Enforced in the API projection, not just the UI.
- Rehearsal: `test.mjs` covers taxonomy rejection paths, the pair filter, the blind/reveal boundary, and the full engagement lifecycle — 67 passed / 0 failed in JSON mode; DB mode 68 passed with one pre-existing phase-2 failure (see below).

## Data layer — Vercel DB (addendum, 2026-11-18)

With `DATABASE_URL` set, the app runs on the talent data layer (Vercel Postgres in production): `lib/store-pg.mjs` hydrates the working set from the DB at boot and writes every save through to the typed tables in `db/schema.sql` (`developer`, `developer_status`, `repo_permission`, `mock`, `chronicle_entry`, `comms_send`, `comment`). The DB is the durable record; the JSON documents remain the app's interface and working set.

- `node db/seed.mjs` — idempotent seed: the five known professionals (`db/professionals.mjs`, from the verified GitHub scan of 2026-11-18) into `developer` + `developer_status`, and their 59 grants into `repo_permission`. Records access as found; changes nothing.
- `node db/sync-sheet.mjs [--dry-run]` — regenerates the Google Sheet (Permissions Ledger + Developer Status tabs) from the DB. The sheet is an output of the DB, never hand-edited.
- Verified 2026-11-18 against a local Postgres: seed counts {developer 5, developer_status 5, repo_permission 59}; the rehearsal suite passes 21/21 in both JSON mode and DB mode; DB-mode boot serves exactly the five seeded professionals.
- Provisioning remainder: create the Postgres store on the dev-library Vercel project and set `DATABASE_URL` — rides with the dev.uzemarkets.com deployment (separate gate).
- M1 update (2026-11-18): the typed tables now also include `developer_expertise` and `engagement`, written through and hydrated the same way. Known DB-mode rehearsal note: the phase-2 assertion "the delivered code signs in" fails in DB mode on the pre-M1 code as well (verified against the base tree) — in DB mode the second server hydrates phase 1's still-queued OTP mails, and its stub-mail code extraction can pick a phase-1 code; a harness interaction, not an app regression. It passes in JSON mode.
