# AUDIT — Dev Library / Talent Composite Scope: Completion Record for Review and Attestation

**Addressed to:** DeepSeek (reviewer)
**Prepared by:** SoSem (SYS_Administrator, DEVBUILDSTACK; build lead)
**Date:** 2026-11-18
**Subject:** Phase-by-phase completion audit of the Talent Vertical composite scope (Directive v3.1), with evidence drawn from the repository record and live checks performed at audit time. Prepared for attestation by James (Project Lead, 456iP) — see the attestation block at the end. This document is unsigned.

---

## Discrepancies flagged first (docs vs. record vs. live state)

1. **Scope headers were never re-stamped after the tap.** `CONSOLIDATED-SCOPE-v3.1.md` still carries the header "Status: FOR JAMES'S TAP — no build begins before the tap," and `BUILD-SCOPE-AND-PHASED-SPRINT-v1.0.md` still reads "FOR JAMES'S TAP." The record shows James tapped the build on 2026-11-18 (the tap is recorded in the commit messages of `83cb964` and, for the amended scope, `d36b333`), and Phase 1 is built and deployed. The headers are stale; the taps are real and are cited below. The documents were not rewritten, per the convention that filed records are corrected by addition, not by silent edit.
2. **Yagnik Moradiya grant count: addendum says 41, seed source encodes 40.** Addendum §5 states access on "41 of 41 repos (7 admin, 2 maintain, 5 write, 27 read)." The seed source `apps/dev-library/db/professionals.mjs` carries **40** grant rows for Yagnik. The repo_permission total reconciles at **59** only under the 40 figure (40 + 9 Rohan + 10 Shradhesh + 0 + 0 = 59), which matches the recorded seed verification `{developer 5, developer_status 5, repo_permission 59}` in commit `d36b333`. One repo counted in the addendum's prose is not rowed in the seed source. This audit does not resolve which figure is correct; it flags the one-row difference for the reviewer and for James.
3. **The addendum's database name is superseded by the deploy record.** Addendum §2 names "Vercel Postgres" as the data layer. The deployment record (commit `78f63d6`) establishes that Vercel Postgres was sunset and the create-store API returns `not_found`; the attach path is now a Marketplace Postgres (Neon). The addendum's architecture (one data layer, sheet generated from the DB) is unchanged; only the provider name in its §2 is overtaken.
4. **Untracked asset in the working tree.** `apps/dev-library/assets/hero.jpg` exists in the working tree but is untracked and is **not** part of the repository of record at HEAD `9a0d6a1`. It belongs to in-progress email-design work and is excluded from every claim in this audit.

---

## 1. Scope of record

- **Directive v3.1** — the reading room consolidates into a four-layer talent platform: **DISCOVERY** (reading room) → **ASSESSMENT** (DAL) → **PLACEMENT** (TR marketplace) → **SETTLEMENT** (escrow), dual-track (Track A internal technical only, never placed; Track B external placement), Role × Realm taxonomy (11 Roles × 6 Realms, up to 5 pairs per talent), entity model with 21 invariants (status derived, never written; revoke cascade atomic; ladder promotion requires a human `promotedBy`; every transition emits an Event). Filed as received at `docs/talent/CONSOLIDATED-ENGINEERING-DOCUMENT-as-received-2026-11-18.md`.
- **Phase 0 extension** — `docs/talent/CONSOLIDATED-SCOPE-v3.1.md` (field-level extension, sprint decomposition, gap analysis G1–G8, migration plan), with the directive's 16 Mermaid exhibits extracted verbatim and hash-verified 16/16 into `docs/talent/exhibits/`. Commit `bd226ae`.
- **Phased sprint plan (the scope of record for execution)** — `docs/talent/BUILD-SCOPE-AND-PHASED-SPRINT-v1.0.md`, commit `164fd2b`: P0 extension → P1 reading room → P2 assessment → P3 dual-track + taxonomy → P4 NEAR marketplace → P5 hardening → P6 open-repo gate (James's tap only; closed until HR placement + payment are proven live via P4).
- **Vercel-DB addendum** — `docs/talent/ADDENDUM-VERCEL-DB-AND-PERMISSIONS-LEDGER-2026-11-18.md`, commit `3b77b81`: the database is the phased sprint's data layer; tables `repo_permission` + `developer_status` added; the Google Sheet "DEVBUILDSTACK — Developer Permissions Ledger" is generated from the DB by sync, never hand-edited; the five known professionals are seeded with their verified 2026-11-18 status; no permission is changed by the seeding.
- **James's build tap** — 2026-11-18: the build tap on the phased scope, and the tap on the amended (addendum) scope, both recorded in the commit messages cited in §2.

## 2. Phase-by-phase status

| Phase | Status | Evidence |
|---|---|---|
| **P0 — Extension** | **FILED** | `bd226ae` (directive as received, 16 exhibits hash-verified 16/16, consolidated scope v3.1); `164fd2b` (build scope + phased sprint v1.0) |
| **P1 — Reading room** | **BUILT · DEPLOYED LIVE · GATE VERIFIED** | App commit `83cb964`; Vercel-readiness + deploy workflow `5fdc787`; deploy fixes `ae60a35`, `78f63d6`; live checks at audit time below |
| **Data layer (addendum)** | **BUILT · VERIFIED ON LOCAL POSTGRES** | `d36b333`; seed source independently re-counted at audit time (below) |
| **Comms desk / mailer** | **BUILT · INERT UNTIL KEY LANDS** | `803c055`, `d64c689`, `979d091`, `60ef188`, `9a0d6a1` |
| **Resend webhook** | **BUILT · ENDPOINT LIVE, SECRET PENDING** | `bfe6296` |
| **P2 — Assessment (DAL)** | **NOT STARTED** — future phase | — |
| **P3 — Dual-track + taxonomy** | **NOT STARTED** — future phase (seed records carry track + Role×Realm mappings as data only; the P3 build has not begun) | — |
| **P4 — NEAR marketplace** | **NOT STARTED** — future phase | — |
| **P5 — Hardening** | **NOT STARTED** — future phase | — |
| **P6 — Open-repo gate** | **NOT STARTED · GATE CLOSED** — opens only on James's tap after P4 proves HR placement + payment live | — |

### P1 detail

- **App** — `apps/dev-library/`, zero-dependency Node: `server.mjs`; `lib/gate.mjs` (allowlist = Developer List records holding an active reading-room grant; 6-digit OTP, sha256-hashed, 15-minute expiry; HMAC session cookie bound to a per-developer `sessionEpoch`, so an access-affecting change ends live sessions and forces a fresh OTP); `lib/lifecycle.mjs` (stage transitions, reset-to-zero with the chronicle preserved); `lib/store.mjs` (JSON working set) behind the same interface as the Postgres store.
- **Core-side schema** — Alembic migration `d1ce7a1e5001` creates Postgres schema `talent` + 10 tables in the AssurativeV2 core. From-empty replay verified at build time: 15 migrations in a single pass from an empty database, 15/15 applied, zero failures (recorded in `83cb964`).
- **Catalog behaviour** — manifest-driven, filterable by developer email, topic, date, and full DEVBUILDSTACK repo name, plus track filter; external-track preview never sees INTERNAL_ONLY mocks; a direct fetch of an internal mock returns 404 (all asserted in the rehearsal, §3).
- **Deployment** — GitHub Actions workflow `.github/workflows/deploy-dev-library.yml` deploys to Vercel project **uze-dev-library** (team slug `uze2`). Run 1 failed on a missing project id (fixed `ae60a35`); run 2 failed on the sunset Vercel Postgres store endpoint (fixed `78f63d6`); run 3 completed all steps. Custom domain `dev.uzemarkets.com` is attached (one add-only CNAME at GoDaddy).
- **Live checks performed at audit time (2026-11-18, this audit, `curl`):**
  - `GET https://dev.uzemarkets.com/` → **200**
  - `GET https://dev.uzemarkets.com/api/catalog` → **401** (the allowlist gate refusing an unauthenticated request — the gate working, not an outage)
  - `GET https://uze-dev-library.vercel.app/` → **200**

### Data layer detail

- **Schema** — `apps/dev-library/db/schema.sql`: `developer`, `developer_status`, `repo_permission`, `mock`, `mock_alias`, `chronicle_entry`, `comms_send`, `comment`, `otp_code`. Write-through Postgres store `lib/store-pg.mjs` behind the `store.mjs` interface (hydrate at boot; DB wins when it holds state); accepts `POSTGRES_URL` beside `DATABASE_URL`. Sheet sync `db/sync-sheet.mjs` generates the ledger Sheet from the DB (`--dry-run` supported).
- **Seed** — `db/seed.mjs`, idempotent, from `db/professionals.mjs` (the verified 2026-11-18 GitHub scan; pre-system grants carry `grantedAt` null + origin "pre-system (verified 2026-11-18 scan)"; the seeding changes no GitHub permission).
- **Verification of record** — commit `d36b333`: seed counts `{developer 5, developer_status 5, repo_permission 59}` verified on local Postgres; rehearsal green in JSON mode and DB mode.
- **Independent re-count at audit time** — importing `db/professionals.mjs` directly: **5 professionals; grant rows 40 (Yagnik Moradiya) + 9 (Rohan Singla) + 10 (Shradhesh Jain) + 0 (Nithin Mengani) + 0 (Dipanshu Singh) = 59**. This reconciles with the recorded verification — subject to discrepancy #2 above (the addendum's prose figure of 41 for Yagnik).

### Mailer detail (the comms desk sending arm)

- **Mailer** — `lib/mailer.mjs` (commit `803c055`): `sendMail` POSTs to the Resend API (`RESEND_API_URL`, default `https://api.resend.com/emails`) with the API key as bearer; default sender `UZE Dev Library <desk@uzemarkets.com>` (`LIBRARY_FROM`). `drainComms` sends queued comms entries oldest-first at the moment of the triggering event (sign-in code requested; reading-room grant issued; access-affecting change / reset-to-zero; GitHub source grant), marks them sent with provider id + timestamp; failures stay queued with attempts + last error recorded — never dropped. **Inert until `RESEND_API_KEY` exists in the deployment environment** (see open blocks).
- **Branding** — commit `d64c689` (James, 2026-11-18): UZEmarkets-branded HTML + text (tangerine `#ff6b00` / cream `#f5f2ee` / ink `#1a1a1a`); greeting "Dear Development Partner," for desk correspondence, "Hello," for the sign-in code (code rendered large); desk signature block. Design revision v2 in commit `9a0d6a1` (current HEAD): ink header band with reversed wordmark, serif headline, facts card, social-engagement banner integrated for desk correspondence; the OTP email stays lean.
- **CTA layout rule** — commit `979d091` (James, 2026-11-18): the house calls to action (X, Instagram, podcast + the share/feedback line) sit succinctly, directly above the sender's signature; the UZEmarkets wordmark goes underneath. The WhatsApp group joins the CTA block as a real link only once the group exists (post–Dec 2 Meta gate); no link was invented.
- **Resend deep-dive adopts** — commit `979d091`, from the filed research report on Resend's official docs: requests now set `user-agent: uze-dev-library/1.0` (the docs record that a missing User-Agent returns 403 despite a valid key — this would have broken the first live send), an `idempotency-key` per comms entry (24h, retry-safe), and tags as the metadata channel (`app`, `kind` — echoed back in webhooks).

### Webhook detail

- Commit `bfe6296`: `lib/webhook.mjs` + `POST /api/resend-webhook`. Verifies the Svix signature over the **raw** body (HMAC-SHA256, 5-minute timestamp tolerance), records delivered / bounced / complained / failed / suppressed / delayed / sent onto the comms entry joined by provider id, dedupes on `svix-id`. Forged signatures are rejected (asserted in the rehearsal). The endpoint answers **503 until `RESEND_WEBHOOK_SECRET` is set** — see open blocks.

## 3. Rehearsal of record (run at audit time)

Command: `cd apps/dev-library && node test.mjs` — actual output, result line and evidence lines verbatim:

```
PASS house CTAs sit above the signature, logo underneath (James's layout rule)
PASS mail configured: invitation SENT at the grant event, from desk@
PASS invitation is branded: greeting, tangerine, library link, desk signature
PASS sign-in code SENT at the request event
PASS code email is branded and shows the code large
PASS the delivered code signs in
PASS failed send stays queued, attempt + error recorded (never dropped)
PASS webhook: delivered event recorded on the comms entry
PASS webhook: duplicate delivery deduped on svix id
PASS webhook: forged signature rejected
RESULT: 32 passed, 0 failed
```

The full 32-assertion run covers, additionally: catalog visibility and the topic/repo/track filters, the external-preview INTERNAL_ONLY exclusion and 404, pre-source commenting, master-only view-as, rename with alias + version bump + changelog growth, session kill on re-prompt, source-grant recording, revocation killing the session, reset-to-zero, and chronicle preservation across every transition. Repository state at audit time: HEAD `9a0d6a1`, identical to `origin/main`; working tree clean except the untracked asset in discrepancy #4.

## 4. Open blocks (stated honestly; nothing below is claimed as done)

1. **`RESEND_API_KEY` is not yet in the Vercel production environment.** Placement is blocked on a Vercel sign-in: Vercel emailed a 6-digit code to an inbox outside our connected access. **Unblock: James provides the code.** Until then the mailer is built, rehearsed, and inert; no live desk@ send has occurred through Resend.
2. **Resend domain verification status has not yet been reported back** from the dashboard session (domain `uzemarkets.com` added in the new, exclusive Resend account; the DNS records were to be added at GoDaddy add-only). Unverified at audit time.
3. **The Resend webhook endpoint is deployed but unarmed**: creating the webhook in the Resend dashboard and placing its signing secret (`RESEND_WEBHOOK_SECRET`) in the Vercel production environment rides with the same dashboard session as block 1. Until then the endpoint answers 503 by design.
4. **Neon Postgres attach is outstanding** (Marketplace install on the uze-dev-library project — a Vercel-side action for James). Until it lands, production runs on the `/tmp` JSON working set: state resets on cold start and, in JSON mode, OTP codes are held in memory, so a sign-in request and its verification must reach the same warm instance. The deploy workflow seeds the data layer automatically once a database URL exists.
5. **`LIBRARY_MASTER_TOKEN` is not set** (a secret James provides). The production admin API is therefore closed. Deliberate, not an oversight.
6. **The owner OTP test is pending the key**: the owner test persona (James, internal testing address) is seeded with a reading-room grant and a queued invitation; the end-to-end owner sign-in at dev.uzemarkets.com runs once block 1 clears. Per James's testing rule, everything is tested to James first, before any external party receives anything.
7. **Standing embargo (James, 2026-11-18): no outreach to any talent prospect — known or cold — until Resend has been optimized as an engagement and recruiting strategic tool.** Internal test mail to James continues; no prospect has been sent anything, and none will be while the embargo stands.

## 5. What this audit does not claim

- No live Resend send has occurred. No talent prospect has been contacted through this system. No GitHub permission was changed by the build or the seeding. Phases P2–P6 have not started. The Sheet is generated from the seeded data layer locally; its regeneration from a production database awaits block 4.

---

## Attestation

Prepared for attestation by James (Project Lead, 456iP).

I attest that the completion record above — Phase 0 filed, Phase 1 built and deployed with its gate verified live, the data layer seeded and verified, the mailer and webhook built and rehearsed, Phases P2–P6 not started, and the open blocks as stated — is accurate to the repository record and the live checks cited.

Signature: ______________________________

Name: James (Project Lead, 456iP)

Date: ______________________________
