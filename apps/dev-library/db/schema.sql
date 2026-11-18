-- UZE Dev Library — Vercel Postgres schema (Talent Vertical phased sprint,
-- data layer per ADDENDUM-VERCEL-DB-AND-PERMISSIONS-LEDGER-2026-11-18).
-- Plain DDL, no extensions; idempotent (safe to apply on every boot/seed).
-- The reading room's entities are rows; nested attributes ride in `data`
-- jsonb so the app's document interface (lib/store.mjs) is preserved.

CREATE TABLE IF NOT EXISTS developer (
  email          text PRIMARY KEY,              -- lowercased
  name           text NOT NULL,
  dev_class      text NOT NULL DEFAULT 'COLD_RECRUIT',  -- PRIOR_TEAM | PEER_PROSPECT | COLD_RECRUIT
  track          text NOT NULL DEFAULT 'EITHER',
  stage          text NOT NULL DEFAULT 'prospect',
  session_epoch  int  NOT NULL DEFAULT 0,
  roadmap        text,
  roadmap_exempt boolean NOT NULL DEFAULT false,
  data           jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- The known professionals' standing record (classification register).
CREATE TABLE IF NOT EXISTS developer_status (
  email             text PRIMARY KEY,
  name              text NOT NULL,
  dev_class         text NOT NULL,
  github_username   text,
  whatsapp          text,
  telegram          text,
  linkedin          text,
  x_handle          text,
  expertise_summary text,
  repos_with_access int NOT NULL DEFAULT 0,
  access_summary    text,
  gating_status     text NOT NULL DEFAULT 'not-granted',  -- not-granted | granted | revoked
  status_recorded_on date NOT NULL DEFAULT CURRENT_DATE,
  notes             text
);

-- The permissions ledger: one row per grant event. Modifications and
-- removals update the lifecycle columns; the row is never deleted, and
-- a re-grant is a new row — the sheet's history is this table's history.
CREATE TABLE IF NOT EXISTS repo_permission (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  org             text NOT NULL DEFAULT 'DEVBUILDSTACK',
  repo            text NOT NULL,
  repo_url        text NOT NULL,
  developer_email text NOT NULL,
  developer_name  text NOT NULL,
  permission      text NOT NULL,                -- admin | maintain | write | triage | read
  date_recorded   date NOT NULL,
  date_modified   date,
  date_removed    date,
  status          text NOT NULL DEFAULT 'active',  -- active | removed
  origin          text NOT NULL DEFAULT 'verified-scan',
  UNIQUE (org, repo, developer_email, date_recorded)
);

CREATE TABLE IF NOT EXISTS mock (
  slug    text PRIMARY KEY,
  title   text NOT NULL,
  topic   text,
  date    date,
  repo    text,
  track   text NOT NULL DEFAULT 'BOTH',
  version int  NOT NULL DEFAULT 1,
  data    jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS mock_alias (
  alias text PRIMARY KEY,
  slug  text NOT NULL REFERENCES mock(slug) ON DELETE CASCADE
);

-- The chronicle: append-only. `dedupe` makes write-through idempotent.
CREATE TABLE IF NOT EXISTS chronicle_entry (
  id     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  at     timestamptz NOT NULL,
  type   text NOT NULL,
  dedupe text UNIQUE NOT NULL,
  data   jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS comms_send (
  id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  at        timestamptz NOT NULL,
  sender    text NOT NULL,
  recipient text NOT NULL,
  kind      text NOT NULL,
  subject   text,
  status    text NOT NULL DEFAULT 'queued',     -- queued until desk@ sending is verified live (G8)
  dedupe    text UNIQUE NOT NULL,
  data      jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS comment (
  id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  slug     text NOT NULL,
  by_email text NOT NULL,
  at       timestamptz NOT NULL,
  text     text NOT NULL,
  dedupe   text UNIQUE NOT NULL
);
