"""Talent vertical P2 (Scope 2, separated track) — assessment layer.

Revision ID: c9a4e7b21f08
Revises: b7e3f1a9c204
Create Date: 2026-11-18

Implements Sprint 1 of docs/talent/P2-SCOPE-AND-PHASED-SPRINT-v0.1.md
(tapped by James 2026-11-18 21:26 ET): role configuration, the
curated template library, generated assessments behind the TWO human
gates, candidate runs with scoring, and the publication store.

Design carried from the filed instruments:
- Role records key to the Role × Realm taxonomy of d1ce7a1e5001
  (pairs ride as jsonb of enum literals — role/realm values are the
  talent.role / talent.realm enum labels, frozen here).
- The two gates are FACTS (gate1_*, gate2_*). Gate order is enforced
  in the data: a Gate 2 signature cannot exist without Gate 1
  (CHECK below), mirroring the console rule that nothing runs before
  both gates pass, in order. Signer kind is recorded; the value
  'AGENT' is excluded by CHECK — an agent identity can never satisfy
  either gate, in any store.
- Status is DERIVED from facts, never a column (v3.1 invariant).
- The publication table is the publication STORE of the three-store
  separation (P2 §4): it carries the redacted artifact only —
  pseudonym, cohort key, CID, banded facts. It has NO foreign key to
  talent.talent and no name/email/company column exists in it; the
  publisher holds no identity-store read path, in this schema as in
  the app.
- Validity is a statement of one enforced shape (population + metric)
  or an explicit gap acknowledgment; the run's validity jsonb carries
  exactly one of the two forms.

Frozen-artifact discipline: all layouts are literals; this revision
never imports live application source.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c9a4e7b21f08'
down_revision: Union[str, None] = 'b7e3f1a9c204'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE talent.role_config (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            employer_ref text NOT NULL,
            vertical text NOT NULL,
            title text NOT NULL,
            seniority text,
            market text,
            engagement_mode text,
            budget_band text,
            pairs jsonb NOT NULL DEFAULT '[]',
            skills jsonb NOT NULL DEFAULT '[]',
            judgment_dimensions jsonb NOT NULL DEFAULT '[]',
            work_history_required boolean NOT NULL DEFAULT true,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX role_config_by_vertical ON talent.role_config (vertical);

        CREATE TABLE talent.assessment_template (
            id text PRIMARY KEY,
            vertical text NOT NULL,
            title text NOT NULL,
            dimensions jsonb NOT NULL DEFAULT '[]',
            calibration_population text,
            calibration_metric text,
            version int NOT NULL DEFAULT 1,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX assessment_template_by_vertical ON talent.assessment_template (vertical);

        CREATE TABLE talent.assessment (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            role_config_id uuid NOT NULL REFERENCES talent.role_config(id),
            template_id text NOT NULL REFERENCES talent.assessment_template(id),
            instrument jsonb NOT NULL DEFAULT '{}',
            signals jsonb NOT NULL DEFAULT '{}',
            instrument_version int NOT NULL DEFAULT 1,
            gate1_by text,
            gate1_at timestamptz,
            gate1_kind text,
            gate2_by text,
            gate2_at timestamptz,
            gate2_kind text,
            gate2_basis text,
            created_at timestamptz NOT NULL DEFAULT now(),
            CHECK (gate1_kind IS NULL OR gate1_kind = 'HUMAN'),
            CHECK (gate2_kind IS NULL OR gate2_kind = 'HUMAN'),
            CHECK (gate2_at IS NULL OR gate1_at IS NOT NULL)
        );
        CREATE INDEX assessment_by_role_config ON talent.assessment (role_config_id);

        CREATE TABLE talent.assessment_run (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            assessment_id uuid NOT NULL REFERENCES talent.assessment(id),
            talent_id uuid REFERENCES talent.talent(id),
            talent_did text NOT NULL,
            responses jsonb NOT NULL DEFAULT '{}',
            score numeric(6,2),
            grade_band text,
            human_review boolean,
            review_threshold numeric(6,2),
            validity jsonb,
            retake_of uuid REFERENCES talent.assessment_run(id),
            taken_at timestamptz NOT NULL DEFAULT now(),
            scored_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX assessment_run_by_assessment ON talent.assessment_run (assessment_id);
        CREATE INDEX assessment_run_by_talent_did ON talent.assessment_run (talent_did);

        CREATE TABLE talent.publication (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id uuid REFERENCES talent.assessment_run(id),
            pseudonym text NOT NULL,
            cohort_key text NOT NULL,
            cid text,
            pin_adapter text,
            artifact jsonb NOT NULL DEFAULT '{}',
            published_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX publication_by_cohort ON talent.publication (cohort_key);
        CREATE INDEX publication_by_pseudonym ON talent.publication (pseudonym);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS talent.publication;
        DROP TABLE IF EXISTS talent.assessment_run;
        DROP TABLE IF EXISTS talent.assessment;
        DROP TABLE IF EXISTS talent.assessment_template;
        DROP TABLE IF EXISTS talent.role_config;
    """)
