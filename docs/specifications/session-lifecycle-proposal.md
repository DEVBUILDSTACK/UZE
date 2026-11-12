# Session Lifecycle — PROPOSAL

**Status: 🔴 PROPOSAL — not built, not scheduled.** Filed
2026-11-12 on the owner's tap as a design record. The
underwriting engine is stateless today and stays stateless
until the gating infrastructure below exists and the owner
ratifies a build. Nothing in this document describes running
code.

## Why this exists

Analysts work in sittings: a rent roll arrives at 10:00, the
T-12 at 10:29, the instruction to "run the pro forma" later
still. A stateless engine forces the analyst to re-supply
every document on every call. A *session* layer would hold
parsed documents against a client identity for a bounded
window. This proposal designs that layer — and its retention
policy — before any of it is built.

## The gating dependencies (all open)

1. A receiving mailbox (underwriting@uzemarkets.com does not
   exist; the published intake is uzemarket@uzemarkets.com,
   and the custom-domain mail setup is owner-side work).
2. A publicly deployed compose API (the Render step on the
   owner's log) — sessions behind an unreachable API are
   fiction.
3. The owner's explicit build tap on this proposal,
   including the retention policy below.

## Schema sketch (ClientSession)

| Field | Notes |
|---|---|
| `id` | UUID, primary key |
| `sender_email` | Indexed; the session lookup key |
| `created_at` / `expires_at` | The lifecycle window (tiers below) |
| `status` | ACTIVE · PROCESSED · EXPIRED |
| `document_count` | Documents appended to the session |
| `session_hash` | Salted commitment hash (see Privacy) |
| `billing_tier` | FULL · WEEKLY · MONTHLY · QUARTERLY · ANNUALLY |
| `cloud_container_id` | Nullable; only if container isolation is ever built |

Parsed documents link to the session by `session_id`; the
engine assembles its working set from the session's parsed
JSON at execution time. The model holds no memory between
executions — the database is the memory, the prompt is
assembled per run and discarded.

## TTL tiers

| Tier | Window | `expires_at` |
|---|---|---|
| Stateless | none | no session is created |
| WEEKLY | 7 days | created_at + 7d |
| MONTHLY | 30 days | created_at + 30d |
| QUARTERLY | 90 days | created_at + 90d |
| ANNUALLY | 365 days | created_at + 365d |
| FULL (fixed) | to a contracted end date | the date itself |

Expiry is enforced by a purge job (which itself requires the
owner's scope tap before it may run on a schedule): on
expiry the session's parsed JSON and any stored raw files
are deleted and the deletion is logged.

## Privacy & retention policy (the operative part)

- **Raw files:** purged immediately after parsing by
  default; retained only inside an ACTIVE session whose tier
  explicitly includes raw retention, and never beyond
  `expires_at`.
- **Parsed JSON:** retained for the session window only;
  purged at expiry. No indefinite retention tier exists.
- **PII minimization:** the session stores the sender's email
  (the lookup key) and property financials the sender
  supplied — nothing else is collected, and nothing is shared
  with third parties or external AI services.
- **The on-chain anchor, stated correctly:** an optional
  `anchor_session(session_hash, expires_at)` contract call
  would write the commitment hash and the expiry to NEAR.
  That proves **the authorized lifecycle window existed** —
  when the session was authorized to begin and when it was
  authorized to end. It does **not** prove deletion: deletion
  happens off-chain and can only be **attested** (by the
  purge job's signed log), never proven by the anchor. Any
  sales language claiming "cryptographic proof of deletion"
  is false and must not be used.
- **Salted commitment hash, never a bare email hash:** an
  email address is low-entropy; a bare SHA-256 of it on a
  public chain is reversible by dictionary attack and would
  deanonymize the client list. The anchor value must be a
  keyed commitment — HMAC-SHA-256 over (email + session id +
  created_at) under a server-held secret — so the chain
  record is verifiable by UZEmarkets and meaningless to
  anyone else.

## Endpoints (proposed)

- `POST /api/v1/ingest/stateless` — parse, answer, retain
  nothing. (This is effectively today's behavior.)
- `POST /api/v1/ingest/session` — append a document to the
  sender's ACTIVE session, creating one if none exists.
- `POST /api/v1/sessions/rent` — set/extend a session's tier
  and `expires_at`.

## What this proposal is not

Not a commitment to build, not a retention promise to any
client, and not a description of the current system. The
current system is stateless; client files supplied in chat
or by upload are processed in the working environment and
are not written into any repository or long-term store.
