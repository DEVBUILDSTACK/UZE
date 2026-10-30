"""QuestionManifest slots validated at the DB level (tap (a)).

Revision ID: d52f8b1a904c
Revises: b3d91c7e5a02
Create Date: 2026-10-30

WHY THIS REVISION EXISTS (James's tap (a), 2026-10-30): the
QuestionManifest slot shape is now tapped content — `questions` is a
typed list of QuestionSlot (key, type in QuestionSlotType,
enumValues iff type = ENUM, required, deferrable, dependsOn entries
of {slot, op, value}, moduleGate in ModuleType, validation,
promptHuman, promptAgent). The generated Pydantic enforces the shape
for API writers; this revision is the same law at the DB level, for
every writer — the DB-level presence of the tapped shape.

WHAT IT ADDS — one function + one trigger, nothing else:

  question_manifest_validate_slots() /
  trg_question_manifest_validate_slots
  BEFORE INSERT OR UPDATE ON question_manifest. For each slot in the
  questions array it raises on: a non-array questions value; a slot
  missing any required key; an unknown type; an ENUM slot without an
  enumValues array; a non-ENUM slot carrying enumValues (the iff
  rule, both directions); an unknown moduleGate; a dependsOn that is
  not an array of {slot, op, value} objects. The vocabularies below
  are QuestionSlotType's and ModuleType's value sets, frozen here as
  migrations must be (a migration never imports the live models).

DOWNGRADE drops exactly the trigger and function this revision added.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d52f8b1a904c"
down_revision = "b3d91c7e5a02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # HAND-WRITTEN (autogenerate cannot express triggers). The DB-level
    # enforcement of the tapped QuestionSlot shape.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION question_manifest_validate_slots()
        RETURNS trigger AS $$
        DECLARE
            slot jsonb;
            dep jsonb;
        BEGIN
            IF jsonb_typeof(NEW.questions::jsonb) IS DISTINCT FROM 'array' THEN
                RAISE EXCEPTION
                    'question_manifest.questions must be a JSON array of QuestionSlot objects';
            END IF;
            FOR slot IN
                SELECT value FROM jsonb_array_elements(NEW.questions::jsonb)
            LOOP
                IF jsonb_typeof(slot) <> 'object'
                   OR NOT (slot ?& ARRAY['key', 'type', 'required',
                                          'deferrable', 'promptHuman',
                                          'promptAgent']) THEN
                    RAISE EXCEPTION
                        'question_manifest slot is missing required keys (key, type, required, deferrable, promptHuman, promptAgent): %',
                        slot;
                END IF;
                IF slot ->> 'type' NOT IN
                   ('STRING', 'INT', 'DATE', 'BOOL', 'ENUM', 'OBJECT', 'ARRAY') THEN
                    RAISE EXCEPTION
                        'question_manifest slot has unknown type: %',
                        slot ->> 'type';
                END IF;
                IF slot ->> 'type' = 'ENUM' THEN
                    IF NOT (slot ? 'enumValues')
                       OR jsonb_typeof(slot -> 'enumValues') <> 'array' THEN
                        RAISE EXCEPTION
                            'question_manifest ENUM slot requires enumValues (a string array): %',
                            slot ->> 'key';
                    END IF;
                ELSIF slot ? 'enumValues' THEN
                    RAISE EXCEPTION
                        'question_manifest non-ENUM slot must not carry enumValues: %',
                        slot ->> 'key';
                END IF;
                IF (slot ? 'moduleGate')
                   AND slot ->> 'moduleGate' NOT IN
                   ('TICKETS', 'STAY', 'FLIGHT', 'PARKING', 'TRANSIT',
                    'DINING', 'TRANSFER', 'VIP_CONCIERGE', 'FACILITY') THEN
                    RAISE EXCEPTION
                        'question_manifest slot has unknown moduleGate: %',
                        slot ->> 'moduleGate';
                END IF;
                IF slot ? 'dependsOn' THEN
                    IF jsonb_typeof(slot -> 'dependsOn') <> 'array' THEN
                        RAISE EXCEPTION
                            'question_manifest slot dependsOn must be an array: %',
                            slot ->> 'key';
                    END IF;
                    FOR dep IN
                        SELECT value
                        FROM jsonb_array_elements(slot -> 'dependsOn')
                    LOOP
                        IF NOT (dep ?& ARRAY['slot', 'op', 'value']) THEN
                            RAISE EXCEPTION
                                'question_manifest dependsOn entry must carry slot, op and value: %',
                                dep;
                        END IF;
                    END LOOP;
                END IF;
            END LOOP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_question_manifest_validate_slots
        BEFORE INSERT OR UPDATE ON question_manifest
        FOR EACH ROW EXECUTE FUNCTION question_manifest_validate_slots()
        """
    )


def downgrade() -> None:
    # Drops only what this revision added (see module docstring).
    op.execute(
        "DROP TRIGGER IF EXISTS trg_question_manifest_validate_slots "
        "ON question_manifest"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS question_manifest_validate_slots()"
    )
