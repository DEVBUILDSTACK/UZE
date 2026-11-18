# ADDENDUM — Vercel DB, Permissions Ledger, and the Known Professionals
## To: BUILD-SCOPE-AND-PHASED-SPRINT-v1.0.md (Talent Vertical) · 2026-11-18 · James's direction, relayed in chat
## Status: part of the updated request for tap; on tap it amends the Phase 1 build

## 1. The linkage (James, 2026-11-18)

The database is not a separate store beside the phased sprint — **it is the phased sprint's data layer.** The reading room built in Phase 1 runs on it; the permissions ledger is one of its tables; the Google Sheet is one of its outputs; the reading-room chronicle and gating status are its event and grant records. Phases 2–5 extend the same database (assessment, marketplace, settlement). Nothing in this addendum creates a second system of record for the talent vertical.

## 2. The database

> **Supersession note (2026-11-18, added by addition — §2's original text below is not rewritten):** the provider name in this section is overtaken. **Vercel Postgres was sunset in June 2025** — the legacy create-store API returns `not_found` (deploy commit `78f63d6`). The attach path is now a **Marketplace Postgres (Neon)**, which injects the database URL into the project env. This addendum's architecture — one data layer for the phased sprint, the sheet generated from the DB — is unchanged; only the provider named in the first bullet is superseded.

- **Vercel Postgres**, a dedicated database, separate from the compose core's Postgres (Scope Tenet 01 keeps business data distinct; this is the talent vertical's store for the developer-facing plane), attached to the dev-library deployment (dev.uzemarkets.com).
- The compose-side `talent` schema (migration d1ce7a1e5001) remains the core integration contract; the Vercel DB carries the same entities for the reading-room plane: developers, expertise, grants, mocks, sessions, events, comms.
- The Phase 1 app's JSON store (apps/dev-library/lib/store.mjs) is replaced by this database behind the same interface; the rehearsal suite must pass unchanged against it.

## 3. Tables added by this addendum

- **repo_permission** — the permissions ledger: org, repo, developer (FK), email of record, permission (admin | maintain | write | triage | read), date recorded, date modified, date removed, status (active | removed). One row per grant event; modifications and removals append, never overwrite — the sheet's history is the table's history.
- **developer_status** — the known professionals' standing record: class (PRIOR_TEAM | PEER_PROSPECT | COLD_RECRUIT), track, Role×Realm pairs, contact state (email / WhatsApp), reading-room gating status, GitHub username.
- The reading-room **grant** and **event** (chronicle) tables double as the gating-status record James named: who holds reading-room access, since when, and every change — the chronicle of what has been built and who may see it.

## 4. Outputs

- **The Google Sheet** — "DEVBUILDSTACK — Developer Permissions Ledger" — is generated from repo_permission + developer_status: by repo, then name/email, dates newest-first, with the modified/removed lifecycle columns and the word "removed" on removal. First edition written from the verified live scan of 2026-11-18 (59 grant rows; sheet id 1n-D2eCYFYTLiTvExkstjXBljQYD9tSxBCqbAAXS6hRM). After this addendum is built, the sheet is regenerated from the DB, never hand-edited.
- **The reading room** reads the same DB: catalog, gating, chronicle views.

## 5. The known professionals — seeded with verified status

On tap, the DB's first records are the five known professionals, carrying their **verified 2026-11-18 status** (live GitHub scan; see the sheet's Developer Status tab):

- **Yagnik Moradiya** (GitHub YagnikMoradiya) — prior team, internal track. Access on **41 of 41** repos: 7 admin (assurative, assurative-v2, Fundio, JsonDealzFlow, SurfSafe-SalesShortcut, monolithic-backend, super-admin-panel), 2 maintain, 5 write, 27 read.
- **Rohan Singla** (GitHub Rohan-Singla) — prior team. **9 repos**: 2 maintain, 3 write, 1 triage, 3 read.
- **Shradhesh Jain** (GitHub Shradhesh71) — prior team. **10 repos**: 2 maintain, 7 write, 1 read.
- **Nithin Mengani** (GitHub Nithin-Varma) — peer prospect. **No DEVBUILDSTACK repo access** (verified; private membership / pending invitation not visible to the day PAT).
- **Dipanshu Singh** (GitHub dipanshuhappy) — peer prospect. **No DEVBUILDSTACK repo access** (verified).

No permission is changed by this addendum or by the seeding — current access stands exactly as found (James, 2026-11-18). Permission adjustments are a later, separate decision.

## 6. Phasing

- **Phase 1, Day 2** (schema day) now provisions the Vercel DB and lands repo_permission + developer_status beside the reading-room tables; the five professionals are seeded that day.
- **Phase 1, Day 3** adds the sheet sync (DB → Google Sheet) to the catalog day.
- All other Phase 1 days and exit gates are unchanged; the D7 rehearsal additionally reads gating status from the DB.

## 7. The tap

James's tap on the parent scope **as amended by this addendum** authorizes: the Vercel DB provisioning, the Phase 1 build on it, the seeding of the five known professionals with the status above, and the sheet sync. It does not authorize any permission change on any repo, any grant to a real developer beyond the seeding records themselves, any desk@ send, or Phases 2–6 — those keep their gates.
