-- =====================================================================
-- Ticket owner guard — trg_ticket_owner_guard
-- services/api manual migration, filed 2026-10-30.
-- Direction: DeepSeek, via James (2026-10-30), closing the ownerId
-- coupling surfaced by the UZEMARKETS read-through contract (R4)
-- divergence-code firing map.
--
-- THE COUPLING THIS CLOSES
-- R4 §5 defines TICKET_TRANSFERRED with two detection branches: the
-- ticket's status is 'transferred', OR its ownerId differs from the
-- owner recorded at quote time. The narrowed reconciliation read
-- (GET /tickets/{ticket_id} -> {id, eventId, tier, status}) does not
-- return ownerId, so the owner branch is detectable only while every
-- ownerId writer also flips status. Today exactly one post-creation
-- writer of Ticket."ownerId" exists — the transfer endpoint
-- (src/routers/tickets.py), which sets "ownerId" and
-- status='transferred' in the same update — so the status branch
-- happens to subsume the owner branch. That was recorded as a watch
-- item: a future writer mutating ownerId silently would make the
-- owner branch the only detector, discovered after the fact.
--
-- This trigger replaces surveillance with an invariant: at the
-- database layer, "ownerId" may change only in a row operation that
-- also sets status='transferred'. A silent ownerId writer cannot
-- exist against a database carrying this trigger, so R4's owner
-- branch is redundant UNCONDITIONALLY, not just for today's writer
-- set.
--
-- WRITER INVENTORY IT MUST NOT BREAK (verified in source 2026-10-30)
--   * transfer (tickets.py): UPDATE "ownerId" + status='transferred'
--     in one statement — passes (the positive case).
--   * listing creation (listings.py): UPDATE status='listed',
--     "ownerId" untouched — passes (the guard fires only when
--     "ownerId" itself changes).
--   * ticket creation (tickets.py): INSERT carrying the initial
--     "ownerId" — passes (the guard is BEFORE UPDATE only).
--
-- FIRING CONDITION (exact)
--   BEFORE UPDATE on "Ticket", FOR EACH ROW: RAISE iff
--     NEW."ownerId" IS DISTINCT FROM OLD."ownerId"
--     AND NEW."status" IS DISTINCT FROM 'transferred'
--   IS DISTINCT FROM is NULL-safe ("ownerId" is nullable): value->NULL
--   and NULL->value changes are guarded exactly like value->value.
--
-- APPLICATION STATE
--   Additive and re-runnable (CREATE OR REPLACE FUNCTION +
--   DROP TRIGGER IF EXISTS). NOT applied to any live database by
--   this filing: services/api carries no migration chain (only
--   schema.prisma), so this file is the reviewed artifact — apply by
--   hand (psql -f) or with the next services/api schema deployment.
--   Local evidence: tests/test_ticket_owner_guard.py, run log at
--   tests/ticket_owner_guard_evidence.log (real PostgreSQL 16.2).
--
-- DDL LEDGER (added 2026-10-30, schema-review direction)
--   services/api has no migration chain, so applied DDL needs a
--   reconstructible history inside the database itself. This file
--   therefore OPENS by creating public.ddl_ledger (id, applied_at,
--   note) if absent, and CLOSES by recording its own application
--   in it under id '2026-10-30-ticket-owner-guard' (INSERT ...
--   ON CONFLICT DO NOTHING, so re-running this file stays a
--   ledger no-op, matching the artifact's re-runnable posture).
--
-- PRESENCE CHECK (what the composition layer uses to confirm this
--   guard is in place — e.g. before relying on R4's owner branch
--   being unconditionally redundant):
--     SELECT 1 FROM pg_trigger
--      WHERE tgname = 'trg_ticket_owner_guard' AND NOT tgisinternal;
--   corroborated by the ledger row:
--     SELECT 1 FROM public.ddl_ledger
--      WHERE id = '2026-10-30-ticket-owner-guard';
--
-- ROLLBACK (drops the guard; the ledger ROW intentionally STAYS —
--   it is the application record, and a rollback is itself an
--   event the application history should keep):
--   DROP TRIGGER IF EXISTS trg_ticket_owner_guard ON "Ticket";
--   DROP FUNCTION IF EXISTS ticket_owner_guard();
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.ddl_ledger (
    id text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now(),
    note text
);

CREATE OR REPLACE FUNCTION ticket_owner_guard() RETURNS trigger AS $$
BEGIN
    IF NEW."ownerId" IS DISTINCT FROM OLD."ownerId"
       AND NEW."status" IS DISTINCT FROM 'transferred' THEN
        RAISE EXCEPTION 'TICKET_OWNER_GUARD: "ownerId" may only change together with status = ''transferred'' (ticket %)', OLD.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_ticket_owner_guard ON "Ticket";

CREATE TRIGGER trg_ticket_owner_guard
    BEFORE UPDATE ON "Ticket"
    FOR EACH ROW
    EXECUTE FUNCTION ticket_owner_guard();

INSERT INTO public.ddl_ledger (id, note)
VALUES ('2026-10-30-ticket-owner-guard',
        'Ticket ownerId guard trigger (trg_ticket_owner_guard)')
ON CONFLICT (id) DO NOTHING;
