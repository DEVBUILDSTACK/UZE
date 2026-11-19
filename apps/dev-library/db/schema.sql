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

-- One-time sign-in codes. Serverless functions share no memory, so in
-- DB mode the codes live here instead of gate.mjs's in-process map.
CREATE TABLE IF NOT EXISTS otp_code (
  email      text PRIMARY KEY,              -- lowercased
  code_hash  text NOT NULL,                 -- sha256 hex of the 6-digit code
  expires_at bigint NOT NULL                -- epoch ms
);

-- Role × Realm taxonomy (M1): the typed mirror of each developer's
-- pairs, written through from the developer record. The taxonomy is
-- enforced HERE, in the data: role/realm/rank value sets, the 1–5
-- ordinal bound, ordinal 1 ⇔ PRIMARY (I1), no duplicate (role, realm).
CREATE TABLE IF NOT EXISTS developer_expertise (
  email   text NOT NULL,
  ordinal int  NOT NULL CHECK (ordinal BETWEEN 1 AND 5),
  role    text NOT NULL CHECK (role IN ('DIGITAL_DESIGN_DEV','FULL_STACK_DEV','FRONT_END_DEV',
            'BLOCKCHAIN_DEV','SMART_CONTRACT_DEV','BLOCKCHAIN_CTO','DEVELOPER_ADVOCATE',
            'TALENT_HR_SPECIALIST','DATA_SCIENTIST','AI_SI_SPECIALIST','OTHER_ROLE')),
  realm   text NOT NULL CHECK (realm IN ('LIGHTNING','NFT_WALLETS','NEAR_AI','CROSS_CHAIN','LIGHTER','OTHER_REALM')),
  rank    text NOT NULL CHECK (rank IN ('PRIMARY','SECONDARY','TERTIARY','QUATERNARY','QUINARY')),
  PRIMARY KEY (email, ordinal),
  UNIQUE (email, role, realm),
  CHECK ((ordinal = 1) = (rank = 'PRIMARY'))
);

-- Track B engagements (M1): typed columns carry the facts the state
-- is derived from; the full record rides in `data`. The reveal order
-- is enforced in the data: no deposit without a signature first.
-- Engagements run on invoice through M3 (amendment C2) — no payment
-- columns exist here by design.
CREATE TABLE IF NOT EXISTS engagement (
  id               text PRIMARY KEY,
  title            text NOT NULL,
  client_name      text NOT NULL,
  service          text NOT NULL CHECK (service IN ('AUG','OUTSTAFF','PLACE','PROJECT')),
  deployment       text NOT NULL CHECK (deployment IN ('REMOTE','HYBRID','MIXED','ONSITE')),
  commercial_model text NOT NULL CHECK (commercial_model IN ('OUTSTAFFING','PLACEMENT')),
  fee_months       numeric,
  developer_email  text,
  signed_at        timestamptz,
  deposit_at       timestamptz,
  closed_at        timestamptz,
  cancelled_at     timestamptz,
  created_at       timestamptz NOT NULL,
  data             jsonb NOT NULL DEFAULT '{}'::jsonb,
  CHECK ((commercial_model = 'PLACEMENT') = (fee_months IS NOT NULL)),
  CHECK (commercial_model <> 'PLACEMENT' OR fee_months >= 1),
  CHECK (deposit_at IS NULL OR signed_at IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS comment (
  id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  slug     text NOT NULL,
  by_email text NOT NULL,
  at       timestamptz NOT NULL,
  text     text NOT NULL,
  dedupe   text UNIQUE NOT NULL
);

-- P2 Assessment (Scope 2, separated track — Sprint 1): role configs,
-- generated assessments behind the two human gates, scored runs, and
-- the publication store. Typed columns carry the gate/score facts;
-- the full records ride in `data`. The publication table is the
-- publication store of the three-store separation: pseudonym, cohort
-- key, content address, banded artifact — no name, email, or company
-- column exists in it, by design (P2 §4).
CREATE TABLE IF NOT EXISTS role_config (
  id           text PRIMARY KEY,
  employer_ref text NOT NULL,
  vertical     text NOT NULL CHECK (vertical IN ('HOSPITALITY','CRE_UNDERWRITING')),
  title        text NOT NULL,
  created_at   timestamptz NOT NULL,
  data         jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS assessment (
  id             text PRIMARY KEY,
  role_config_id text NOT NULL,
  template_id    text NOT NULL,
  gate1_at       timestamptz,
  gate2_at       timestamptz,
  created_at     timestamptz NOT NULL,
  data           jsonb NOT NULL DEFAULT '{}'::jsonb,
  CHECK (gate2_at IS NULL OR gate1_at IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS assessment_run (
  id            text PRIMARY KEY,
  assessment_id text NOT NULL,
  talent_did    text NOT NULL,
  score         numeric,
  human_review  boolean,
  taken_at      timestamptz NOT NULL,
  data          jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS publication (
  id           text PRIMARY KEY,
  cid          text,
  pseudonym    text NOT NULL,
  cohort_key   text NOT NULL,
  published_at timestamptz NOT NULL,
  data         jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- Doc-level P2 state that is not a record: the scoring/publication
-- config, the per-vertical approver registry, and Path A quotes.
CREATE TABLE IF NOT EXISTS assessment_meta (
  id   int PRIMARY KEY CHECK (id = 1),
  data jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- Organizations are first-class (James's steering, 2026-11-19):
-- contacts attach to organizations. The registry is seeded from
-- db/orgs.mjs; advisor records carry an org KEY referencing it.
CREATE TABLE IF NOT EXISTS org (
  key      text PRIMARY KEY,                  -- DFI | FVC | UZE | L2Launch
  name     text NOT NULL,
  acronym  text,
  position int  NOT NULL DEFAULT 0,
  data     jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- L2L & Ecosystem Advisors (James's directive, 2026-11-19): a roster
-- parallel to the Developer List but distinct — no tracks, no
-- expertise pairs, no grants, no sign-in lifecycle. Typed columns
-- carry the roster fields; the full record rides in `data`, as with
-- the developer and engagement tables. `org` is an org-registry key.
-- Email is OPTIONAL — unique only when present (a Postgres UNIQUE
-- column admits any number of NULLs, which is exactly the rule).
CREATE TABLE IF NOT EXISTS advisor (
  id       text PRIMARY KEY,
  name     text NOT NULL,
  email    text UNIQUE,                       -- lowercased, nullable
  title    text,
  org      text,
  base     text,
  lane     text,
  added_at timestamptz NOT NULL,
  data     jsonb NOT NULL DEFAULT '{}'::jsonb
);
-- The advisor table first shipped (2026-11-19) with email NOT NULL;
-- keep an already-created table in step. A no-op where the column
-- is already nullable.
ALTER TABLE advisor ALTER COLUMN email DROP NOT NULL;

-- ── UZE Buildr Team (eco contributor surface, buildr-eco.uzemarkets.com) ──
-- Contributors are principals and ecosystem contributors who do NOT use
-- GitHub: email + one-time code only. The Ecosystem top level is visible
-- to every signed-in contributor; org sections are granted per
-- contributor in eco_contributor_org (org keys mirror the `org` table:
-- DFI | FVC | UZE | L2Launch).
CREATE TABLE IF NOT EXISTS eco_contributor (
  id text PRIMARY KEY,
  name text NOT NULL,
  email text UNIQUE,               -- unique only when present (NULL allowed)
  role text,
  stage text NOT NULL DEFAULT 'seeded',
  session_epoch int NOT NULL DEFAULT 0,
  added_at timestamptz NOT NULL,
  data jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS eco_contributor_org (
  contributor_id text NOT NULL REFERENCES eco_contributor(id) ON DELETE CASCADE,
  org_key text NOT NULL,
  PRIMARY KEY (contributor_id, org_key)
);
-- Eco OTP codes live in their own table so Dev Library codes and eco
-- codes never mix, even for an email that holds grants on both surfaces.
CREATE TABLE IF NOT EXISTS eco_otp_code (
  email text PRIMARY KEY,
  code_hash text NOT NULL,
  expires_at bigint NOT NULL
);
-- Flow-completion events: append-only, one row per transition. A
-- contributor's current step is DERIVED from these rows, never a flag.
CREATE TABLE IF NOT EXISTS eco_flow_event (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  contributor_id text NOT NULL,
  step text NOT NULL,
  at timestamptz NOT NULL,
  dedupe text UNIQUE NOT NULL,
  data jsonb NOT NULL DEFAULT '{}'::jsonb
);
