"""OfferSnapshot divergence annotation — EventLog mirror trigger.

Revision ID: 9d4c1f7a2b58
Revises: cd548e517e5e
Create Date: 2026-10-30

WHY THIS REVISION EXISTS (schema review, term 1 of the ratified
immutability exception): the initial revision permits exactly one
post-insert write on offer_snapshot — the divergence annotation
(divergenceCode/divergenceAt, NULL -> code, once). The review ratified
that exception ONLY on the term that the annotation is a DERIVED
PROJECTION of the authoritative EventLog entry, not an independent
second record. Until this revision, nothing at the DB level bound the
two writes together: a writer could annotate without logging, which is
precisely the shadow-state failure the exception's terms exist to
prevent.

WHAT IT ADDS — one function + one trigger, nothing else:

  offer_snapshot_divergence_mirror() / trg_offer_snapshot_divergence_mirror
  AFTER UPDATE OF "divergenceCode" ON offer_snapshot. When (and only
  when) divergenceCode transitions NULL -> a code, the function inserts
  the SNAPSHOT_DIVERGED row into event_log IN THE SAME TRANSACTION:
  aggregateType='OfferSnapshot', aggregateId = the snapshot id,
  eventType='SNAPSHOT_DIVERGED', actor='system:divergence-annotation',
  payload carrying the divergence code (plus divergenceAt, sourceRef
  and rail for the record). The EventLog entry is authoritative; the
  column is its derived projection, materialized atomically — there is
  no annotation write that is not simultaneously an EventLog write,
  and no writer (ORM or raw SQL) can bypass a DB trigger.

INTERACTION WITH THE EXISTING TRIGGERS: the immutability trigger is
BEFORE UPDATE and still refuses every other write first (a refused
UPDATE never reaches this AFTER trigger); the append-only trigger
refuses UPDATE/DELETE on event_log and does not touch INSERT. The
immutability trigger also guarantees the NULL -> code transition can
happen at most once per snapshot, so the mirror fires exactly once
per annotation.

DOWNGRADE drops ONLY the mirror trigger and its function (the two
objects this revision created). EventLog rows already written by the
mirror are append-only history and are deliberately NOT deleted —
downgrading removes the mechanism, not the record. Additive
discipline: this revision changes no table, column, or prior object.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "9d4c1f7a2b58"
down_revision = "cd548e517e5e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # HAND-WRITTEN (autogenerate cannot express triggers). The mirror
    # behind schema-review term 1 for the divergence-annotation
    # exception: derived, not independent.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION offer_snapshot_divergence_mirror() RETURNS trigger AS $$
        BEGIN
            IF OLD."divergenceCode" IS NULL AND NEW."divergenceCode" IS NOT NULL THEN
                INSERT INTO event_log
                    ("aggregateType", "aggregateId", "eventType", actor, payload, ts)
                VALUES (
                    'OfferSnapshot',
                    NEW.id,
                    'SNAPSHOT_DIVERGED',
                    'system:divergence-annotation',
                    jsonb_build_object(
                        'divergenceCode', NEW."divergenceCode"::text,
                        'divergenceAt', NEW."divergenceAt",
                        'sourceRef', NEW."sourceRef",
                        'rail', NEW.rail::text
                    )::json,
                    COALESCE(NEW."divergenceAt", now())
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_offer_snapshot_divergence_mirror
        AFTER UPDATE OF "divergenceCode" ON offer_snapshot
        FOR EACH ROW EXECUTE FUNCTION offer_snapshot_divergence_mirror()
        """
    )


def downgrade() -> None:
    # Drops only what this revision added (see module docstring):
    # the mirror trigger + function. Mirrored EventLog history stays.
    op.execute(
        "DROP TRIGGER IF EXISTS trg_offer_snapshot_divergence_mirror "
        "ON offer_snapshot"
    )
    op.execute("DROP FUNCTION IF EXISTS offer_snapshot_divergence_mirror()")
