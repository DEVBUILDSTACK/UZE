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
