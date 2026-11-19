"""Talent vertical Phase 3 (merged program M1) — clients + engagements.

Revision ID: b7e3f1a9c204
Revises: d1ce7a1e5001
Create Date: 2026-11-18

Implements the Phase 3 slice of docs/talent/CONSOLIDATED-SCOPE-v3.1.md
§1 (Client, Engagement) under the merged program
(docs/merged/P1-P3-MERGED-SCOPE-AND-PHASED-SPRINT-v0.1.md §5 M1):
dual-track placement with the commercial models of record
(ADDENDUM-TALENT-COMMERCIAL-MODELS-2026-11-18 — OUTSTAFFING: UZE pays
the talent, bills the client; PLACEMENT: fee of at least one month of
salary, the client pays the individual; the two never blended) and
the confidentiality doctrine (no talent exposure before signed
engagement + deposit — signed_at / deposit_at are the facts the
reveal derives from; deposit requires a prior signature).

Engagement invariants enforced here (mach-int-05):
- I2: type=INTERNAL ⇒ client_id, service, deployment, settlement_rail
  all NULL (and, by table separation, no Payment rows — the payment
  table arrives with its phase).
- I3: type=EXTERNAL_PLACED ⇒ client + service + deployment required.
  Escrow/rail are NOT required at insert: engagements run on invoice
  through M3 (merged-program amendment C2) and the settlement rail is
  chosen at signing (mach-int-04 note; I16 immutability applies from
  signing) — the columns exist, nullable until then.
- Engagement.type is IMMUTABLE after insert (trigger below).
- PLACEMENT ⇒ fee_months >= 1; OUTSTAFFING ⇒ fee_months NULL.
- deposit_at requires signed_at (the reveal order).

The 11 engagement states are the Track B state machine of
mach-int-04 (DISCOVERY … REFUNDED); Track A engagements sit in
DISCOVERY's internal lane per the same exhibit. The Role × Realm
taxonomy itself landed in d1ce7a1e5001 (talent_expertise) and is not
repeated here.

Frozen-artifact discipline: all layouts are literals; this revision
never imports live application source.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'b7e3f1a9c204'
down_revision: Union[str, None] = 'd1ce7a1e5001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TYPE talent.service_category AS ENUM ('AUG', 'OUTSTAFF', 'PLACE', 'PROJECT');
        CREATE TYPE talent.deployment_shape AS ENUM ('REMOTE', 'HYBRID', 'MIXED', 'ONSITE');
        CREATE TYPE talent.commercial_model AS ENUM ('OUTSTAFFING', 'PLACEMENT');
        CREATE TYPE talent.engagement_type AS ENUM ('INTERNAL', 'EXTERNAL_PLACED');
        CREATE TYPE talent.engagement_state AS ENUM (
            'DISCOVERY', 'PREVIEW_SHOWN', 'INTENTS_POSTED', 'MATCH_PROPOSED',
            'MATCH_SIGNED', 'ESCROW_HELD', 'MILESTONE_IN_PROGRESS',
            'MILESTONE_COMPLETE', 'SETTLED', 'DISPUTED', 'REFUNDED');
    """)

    op.execute("""
        CREATE TABLE talent.client (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            name text NOT NULL,
            contact text,
            service_categories talent.service_category[] NOT NULL DEFAULT '{}',
            created_at timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE talent.engagement (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            type talent.engagement_type NOT NULL,
            talent_id uuid REFERENCES talent.talent(id),
            client_id uuid REFERENCES talent.client(id),
            service talent.service_category,
            deployment talent.deployment_shape,
            commercial_model talent.commercial_model,
            fee_months numeric(6,2),
            salary_basis numeric(20,2),
            bookends jsonb NOT NULL DEFAULT '{}',
            state talent.engagement_state NOT NULL DEFAULT 'DISCOVERY',
            signed_at timestamptz,
            signed_ref text,
            deposit_at timestamptz,
            deposit_ref text,
            settlement_rail talent.settlement_rail,
            settlement_bridge text,
            nft_output boolean NOT NULL DEFAULT false,
            nft_chain text,
            created_at timestamptz NOT NULL DEFAULT now(),
            CHECK (type <> 'INTERNAL' OR (client_id IS NULL AND service IS NULL
                   AND deployment IS NULL AND settlement_rail IS NULL)),
            CHECK (type <> 'EXTERNAL_PLACED' OR (client_id IS NOT NULL
                   AND service IS NOT NULL AND deployment IS NOT NULL)),
            CHECK (commercial_model IS DISTINCT FROM 'PLACEMENT' OR fee_months >= 1),
            CHECK (commercial_model IS DISTINCT FROM 'OUTSTAFFING' OR fee_months IS NULL),
            CHECK (deposit_at IS NULL OR signed_at IS NOT NULL)
        );
        CREATE INDEX engagement_by_client ON talent.engagement (client_id);
        CREATE INDEX engagement_by_talent ON talent.engagement (talent_id);
        CREATE INDEX engagement_by_state ON talent.engagement (state);
    """)

    # Engagement.type is immutable after insert (§1). A trigger, not a
    # convention: any UPDATE that changes it raises.
    op.execute("""
        CREATE OR REPLACE FUNCTION talent.engagement_type_immutable() RETURNS trigger AS $$
        BEGIN
            IF NEW.type IS DISTINCT FROM OLD.type THEN
                RAISE EXCEPTION 'engagement.type is immutable after insert';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER engagement_type_immutable
            BEFORE UPDATE ON talent.engagement
            FOR EACH ROW EXECUTE FUNCTION talent.engagement_type_immutable();
    """)


def downgrade() -> None:
    op.execute("""
        DROP TRIGGER IF EXISTS engagement_type_immutable ON talent.engagement;
        DROP FUNCTION IF EXISTS talent.engagement_type_immutable();
        DROP TABLE IF EXISTS talent.engagement;
        DROP TABLE IF EXISTS talent.client;
        DROP TYPE IF EXISTS talent.engagement_state;
        DROP TYPE IF EXISTS talent.engagement_type;
        DROP TYPE IF EXISTS talent.commercial_model;
        DROP TYPE IF EXISTS talent.deployment_shape;
        DROP TYPE IF EXISTS talent.service_category;
    """)
