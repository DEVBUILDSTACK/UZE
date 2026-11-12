<!--
  Assurative V2 forensic audit — discovery only; no application code
  was written against the audited repo for this report.
  Audited: DEVBUILDSTACK/assurative-v2 @ 80c0958 (2025-10-16),
  local clone ~/workspace/uze-gira/repo-scan/assurative-v2.
  Cross-referenced: DEVBUILDSTACK/UZE services/api + services/compose
  (the Sprint 1.5 build). Filed 2026-11-08, SoSem.
-->

# Assurative V2 — Gap Analysis for the UZEmarkets HIADR Marketplace

## Executive summary

Assurative V2 as built is a **single-product finance backend** (LP
positions, yields, cohorts, remittances) with a **flat, Privy-keyed
User table** and a separate password/JWT **Admin** table. The trust
layer the HIADR architecture names — **Entity hierarchy, Affiliates,
attestation, provenance/attribution — does not exist in it today**:
zero tables, zero routes, zero code references to entity, affiliate,
attestation, provenance, or referral anywhere in its API source.
That is the central finding. The good news is structural: its API is
the same stack family as the UZEmarkets build (Python / FastAPI /
SQLAlchemy 2.0 / Alembic / Postgres), its IDs are UUIDs, and the
UZEmarkets side already carries the seams (poster kinds incl.
AGENT, an append-only audit log, the x401 stub) the trust layer
needs to plug into.

The architecture principle this audit applies (Scope Tenet 01):
**Assurative V2 is the trust layer** (entities, affiliates, auth,
provenance, attribution); **UZEmarkets is the transaction layer**
(intents, spatial underwriting, TEE/REE auctions); UZEmarkets sits
on top, consuming Assurative identity and provenance while keeping
its own transaction state machine — in its **own database**.
Combination happens only through a defined shared entity, and
cross-database references are plain strings, never foreign keys
(the filed R4 rule).

---

## A. Schema topology (SQLAlchemy / Alembic)

### What exists — DEVBUILDSTACK/assurative-v2, apps/api

Stack: FastAPI 0.115 · SQLAlchemy 2.0.40 + SQLModel 0.0.24 (async)
· Alembic (5 revisions) · Google Cloud SQL Postgres. All tables
inherit a base with a **UUID primary key** (uuid4). Seventeen
tables, all finance-domain:

| Area | Tables |
|---|---|
| Identity | `user`, `admin` |
| Product | `lp`, `lp_type`, `lp_period`, `lp_type_remittance_link`, `lp_type_yield_schedule_link`, `tier`, `cohort_schedule`, `installment`, `autorenewal`, `bal_rate`, `month_fv_yield`-family metrics |
| Payouts | `beneficiary`, `remittance` |
| Ops | `job_history` |

**The identity model is flat.** `user` carries: `privy_user_id`
(unique, indexed — the identity anchor), `primary_email` (unique),
`username`, `social_type` (google/apple), `smart_wallet_address`
(Privy smart wallet, EVM), `safe_address` (Gnosis Safe). Its only
relationships are to its own financial objects (installments,
yields). There is **no role or type field on the user**; `admin` is
a wholly separate table (email + bcrypt password) with its own
auth. `beneficiary` is a named payee record (name + description)
attached to cohort schedules — the closest existing thing to a
payee, but it has no link to a user, no share/fee fields, and no
attribution semantics.

**Entity / Affiliate / Attestation / Provenance tables: none.**
A full-source search for `entity`, `affiliate`, `attestation`,
`provenance`, and `referral` in apps/api returns zero hits.

### What exists — DEVBUILDSTACK/UZE (the marketplace side)

- `services/api` (the ticketing-era core): routers for auth,
  users, profiles, **affiliates**, listings, tickets, events,
  auctions, nfts, analytics, rag, health (unversioned `/{name}`
  prefixes). The affiliates router is an **envelope-only stub**
  (its own docstring: "Affiliate entity table is team build work;
  envelope shape is stable" — list returns `[]`, payout is 501
  pending an approval flow). Listings carry an `ownerId`; ticket
  transfer is its only post-creation writer (Sprint 0 code-verified
  record). Role-gated dependencies exist (`require_role`).
- `services/compose` (Sprint 1.5): the intent's actor model is
  NEAR-account strings (`posterAccount`, `bidderAccount`) plus
  **PosterKind {HUMAN, AGENT, INTERNAL_AGENT, PARTNER}** — the only
  human/agent distinction anywhere in either codebase. The
  append-only `EventLog` (actor + payload on every state change)
  is the provenance *substrate*, but it records marketplace events,
  not rights or revenue attribution. Attribution edges (Numbers
  Protocol) are filed Sprint 2 work, not built.

### The gap — mapping Assurative Entity → Intent.poster_account

1. **The Entity/Affiliate hierarchy must be created** in the trust
   layer: an `entity` table (UUID, the top of the hierarchy) and an
   `affiliate` table (UUID, FK to entity, FK-or-ref to user), with
   the syndicate = Entity and its human partners = Affiliates as
   the first tenants. Nothing to migrate *from* — this is greenfield
   inside Assurative's database, additive by construction.
2. **An identity-binding record is required.** Assurative users are
   keyed by Privy DID with EVM wallet addresses; UZEmarkets actors
   are NEAR accounts (`uzemarkets-talent.testnet`,
   `recon.uzemarkets-talent.testnet`, poster accounts). A NEAR
   account is neither a Privy DID nor an EVM address, so
   poster_account strings cannot be resolved to Entities by
   matching. The trust layer needs an external-accounts binding
   (entity_id ↔ chain/account pairs: privy DID, EVM wallets, NEAR
   accounts) so resolution happens once, at the binding, not by
   string-matching per intent.
3. **On the UZEmarkets side, the additive step is references, not
   keys** (shipped with this audit's companion directive,
   2026-11-08): Intent gains `entityId` / `affiliateId` as nullable
   **string** columns (UUID values carried as strings — a UUID
   column type with a cross-database FK would violate both the
   distinct-databases tenet and the R4 plain-string rule), plus
   `executionEnvironment` (NEAR_INTENTS | ARCIUM_AUCTION) and
   `agentAttestation` (HUMAN | AGENT_X401). Resolution of those
   references against the trust layer is the post-audit migration
   spec's work.

## B. The x401 & agent attestation flow

### How Assurative V2 verifies identity today

Two disjoint mechanisms, both **human-session only**:

- **Users — Privy.** `PrivyAuthMiddleware` extracts the Bearer
  token on a hardcoded list of protected paths, verifies it
  server-side through the Privy API client
  (`users.verify_access_token`), reads the `user_id` claim (the
  Privy DID), loads the User row, and stashes
  `{user_id, privy_id, email, wallet_address}` on request state.
- **Admins — self-issued JWT.** Email/password (bcrypt) login
  issues an HS256 JWT (sub = email, settings secret);
  `AccessTokenAuthMiddleware` verifies it against the Admin table
  on its own protected-path list.

There is **no agent credential, no agent session, and no
machine-to-machine auth** anywhere in the repo. The nearest thing
to an agent identity in the ecosystem is on the UZEmarkets side:
the NEAR account + Chain Signatures (an agent *is* its NEAR
account; the MPC signer produces its Solana signatures), and
PosterKind.AGENT marking agent-posted bids.

### Where x401 fits, and the gap

x401 exists today only as the compose stub (Day 5,
`services/compose/src/metering.py`): tier C+ engagements challenge
for an identity payload and return a verified-credential shape,
everything flagged mock. To make x401 real, the trust layer must
supply what the stub assumes:

1. **An agent credential model**: an agent identity bound to an
   Entity (agent acts *on behalf of* an Entity — the DEMO-SCRIPT's
   x401 line states exactly this), with scope (which intents,
   which tracks, spend ceilings) and revocation. Natural home:
   Assurative DB, beside the entity/affiliate tables of §A.
2. **A verification path that is not a Privy user session**: the
   agent presents its credential (the stub's shape: subject +
   credential type + attestation); the verifier checks it against
   the trust layer and returns the credential + the Entity it acts
   for. The NEAR account is the agent's durable identifier; Chain
   Signatures already proves control of it cryptographically —
   x401 verification should bind to that proof rather than invent
   a second key system.
3. **A session distinction**: human sessions (Privy) vs agent
   attestations (x401) must be distinguishable at the API boundary.
   The wire marker ships today (`agentAttestation` on the Intent);
   compose's dependency-based checks (not Assurative's path-list
   middleware) are where the distinction gets enforced per-route.

## C. API & repo structure

### Assurative V2 — directory tree (apps/api, the FastAPI core)

```
apps/api/
├── alembic/versions/            # 5 revisions
├── src/assurative/
│   ├── api.py                   # app factory; middleware + path lists
│   ├── __main__.py
│   ├── config.py                # pydantic-settings
│   ├── auth/privy_auth.py       # Privy server-side verification
│   ├── core/                    # db_conn (Cloud SQL), db_init, logging
│   ├── middlewares/             # privy, access-token, logging, exceptions
│   ├── models/                  # 17 SQLModel tables (see §A)
│   ├── routers/                 # one module per resource
│   └── scheduler/               # APScheduler jobs (emails, recovery)
├── apps/web, apps/dashboard     # Next.js front ends
└── packages/                    # ui, transactional, configs
```

Router prefixes (factory: `APIRouter(prefix=f"/{name}")`, **no
version segment**): `/users`, `/lps`, `/lp-types`, `/lp-config`,
`/beneficiary`, `/tiers`, `/autorenewals`, `/remittances`,
`/admin`, `/cohort-schedule`, `/installments`, `/yield`,
`/bal-rate`, plus `/health`.

### UZEmarkets — where the code lives

`services/compose` already sits **beside** `services/api` in
DEVBUILDSTACK/UZE and owns the versioned surface: `/api/v1/specs`,
`/api/v1/bids`, `/api/v1/settle`, `/api/v1/metered/analyze`,
`/api/v1/identity/verify` (the x401 stub), `/api/v1/micro-regions`
(+ `/{id}`, `/{id}/pulse`), `/api/v1/talent/{account}`. There is
**no prefix collision** with Assurative's unversioned routes, and
no shared process: different services, different databases.

### The gap — placement

**Do not inject the UZEmarkets routers into the assurative-v2
app.** Its protected-path middleware lists, Cloud SQL lifecycle,
and scheduler are product-specific, and merging processes would
break the distinct-databases tenet and Assurative's existing auth
flows (the exact failure mode this audit was commissioned to
prevent). The correct boundary, per the tenet: compose stays a
separate service consuming trust-layer **data** (entity/affiliate
resolution, x401 verification) over an API, carrying string
references in its own schema. What the trust layer owes that
boundary — an entity-resolution endpoint and the x401 verify
endpoint — is the substance of the post-audit migration spec.

## Recommended sequence (for the post-audit migration spec)

1. Trust layer, additive: `entity`, `affiliate`,
   `entity_external_account` (the binding of §A.2), `agent_credential`
   (§B.1) in Assurative's DB; resolution + x401-verify endpoints
   behind its existing middleware patterns.
2. UZEmarkets: backfill `entityId` on intents from the binding
   (poster_account → entity), keep the string-ref design; the x401
   stub's verifier swaps its local check for the trust-layer call,
   shape unchanged.
3. Attribution/provenance: build on the EventLog substrate +
   the filed Sprint 2 attribution edges; do not retrofit
   Assurative's remittance machinery (it models LP payouts, not
   fractional rights).

*End of audit. Companion work shipped the same day under James's
codification directive: the Intent trust-layer references
(§A.3), the SUBMISSION.md architecture section, and the
DEMO-SCRIPT Entity/Affiliate/x401 narration.*
