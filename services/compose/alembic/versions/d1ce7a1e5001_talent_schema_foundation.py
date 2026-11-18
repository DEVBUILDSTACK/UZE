"""Talent vertical foundation — schema `talent`, Phase 1 (reading room).

Revision ID: d1ce7a1e5001
Revises: f0b56811b3ea
Create Date: 2026-11-18

Implements Part A §1 of docs/talent/BUILD-SCOPE-AND-PHASED-SPRINT-v1.0.md
(field-level detail: docs/talent/CONSOLIDATED-SCOPE-v3.1.md §1). The
talent vertical lives in its own PostgreSQL schema per Scope Tenet 01.
Phase 1 tables only: developer list (talent + expertise pairs), grants,
the mock manifest with its alias chain and changelog, sessions, the
append-only chronicle (event), and the comms send log. Marketplace,
assessment, and payment tables arrive with their phases.

Status is DERIVED (grants + contact history) and is never a column.
Revocation is a state transition; the chronicle is append-only.

Frozen-artifact discipline: all layouts are literals; this revision
never imports live application source.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'd1ce7a1e5001'
down_revision: Union[str, None] = 'f0b56811b3ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS talent")

    op.execute("""
        CREATE TYPE talent.talent_type AS ENUM ('HUMAN', 'AGENTIC');
        CREATE TYPE talent.track AS ENUM ('INTERNAL_ONLY', 'EXTERNAL_PLACED', 'EITHER');
        CREATE TYPE talent.mock_track AS ENUM ('INTERNAL_ONLY', 'EXTERNAL_VISIBLE', 'BOTH');
        CREATE TYPE talent.role AS ENUM (
            'DIGITAL_DESIGN_DEV', 'FULL_STACK_DEV', 'FRONT_END_DEV', 'BLOCKCHAIN_DEV',
            'SMART_CONTRACT_DEV', 'BLOCKCHAIN_CTO', 'DEVELOPER_ADVOCATE',
            'TALENT_HR_SPECIALIST', 'DATA_SCIENTIST', 'AI_SI_SPECIALIST', 'OTHER_ROLE');
        CREATE TYPE talent.realm AS ENUM (
            'LIGHTNING', 'NFT_WALLETS', 'NEAR_AI', 'CROSS_CHAIN', 'LIGHTER', 'OTHER_REALM');
        CREATE TYPE talent.proficiency AS ENUM ('PRIMARY', 'SECONDARY', 'TERTIARY', 'QUATERNARY', 'QUINARY');
        CREATE TYPE talent.grant_surface AS ENUM ('RR', 'GITHUB', 'CLIENT_PREVIEW');
        CREATE TYPE talent.mock_status AS ENUM ('DRAFT', 'PUBLISHED', 'SUPERSEDED', 'ARCHIVED');
        CREATE TYPE talent.settlement_rail AS ENUM (
            'BASE_USDC', 'SOLANA_USDC', 'ROBINHOOD_USDG', 'TEMPO_CASH', 'INTERNAL_INVOICE');
        CREATE TYPE talent.comms_kind AS ENUM (
            'invitation', 'otp', 'change-notice', 'source-grant', 'revocation', 'reminder');
    """)

    op.execute("""
        CREATE TABLE talent.talent (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            type talent.talent_type NOT NULL DEFAULT 'HUMAN',
            track talent.track NOT NULL DEFAULT 'EITHER',
            name text NOT NULL,
            email text NOT NULL,
            whatsapp text,
            contact_email_done boolean NOT NULL DEFAULT false,
            contact_email_at timestamptz,
            contact_whatsapp_done boolean NOT NULL DEFAULT false,
            contact_whatsapp_at timestamptz,
            is_owner boolean NOT NULL DEFAULT false,
            migration_pending boolean NOT NULL DEFAULT false,
            preferred_rail talent.settlement_rail,
            world_participant boolean NOT NULL DEFAULT false,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE UNIQUE INDEX talent_email_lower_uniq ON talent.talent (lower(email));
        CREATE TABLE talent.talent_expertise (
            talent_id uuid NOT NULL REFERENCES talent.talent(id),
            ordinal int NOT NULL CHECK (ordinal BETWEEN 1 AND 5),
            role talent.role NOT NULL,
            realm talent.realm NOT NULL,
            proficiency talent.proficiency NOT NULL,
            PRIMARY KEY (talent_id, ordinal),
            UNIQUE (talent_id, role, realm),
            CHECK ((ordinal = 1) = (proficiency = 'PRIMARY'))
        );

        CREATE TABLE talent.roadmap_binding (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            talent_id uuid NOT NULL REFERENCES talent.talent(id),
            scope_ref text NOT NULL,
            bound_at timestamptz NOT NULL DEFAULT now(),
            unbound_at timestamptz
        );

        CREATE TABLE talent.grant (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            talent_id uuid NOT NULL REFERENCES talent.talent(id),
            surface talent.grant_surface NOT NULL,
            scope text,
            granted_at timestamptz NOT NULL DEFAULT now(),
            revoked_at timestamptz,
            last_activity_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX grant_active_by_talent ON talent.grant (talent_id) WHERE revoked_at IS NULL;

        CREATE TABLE talent.mock (
            id text PRIMARY KEY,
            title text NOT NULL,
            objective text,
            topic text NOT NULL,
            track talent.mock_track NOT NULL DEFAULT 'BOTH',
            repo text NOT NULL,
            clearance text[] NOT NULL DEFAULT '{}',
            status talent.mock_status NOT NULL DEFAULT 'PUBLISHED',
            version text NOT NULL DEFAULT '1.0.0',
            view_link text,
            source_link text,
            created_at timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE talent.mock_alias (
            old_slug text PRIMARY KEY,
            mock_id text NOT NULL REFERENCES talent.mock(id)
        );

        CREATE TABLE talent.mock_changelog (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            mock_id text NOT NULL REFERENCES talent.mock(id),
            version text NOT NULL,
            at timestamptz NOT NULL DEFAULT now(),
            note text NOT NULL
        );

        CREATE TABLE talent.session (
            token_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            talent_id uuid NOT NULL REFERENCES talent.talent(id),
            issued_at timestamptz NOT NULL DEFAULT now(),
            expires_at timestamptz NOT NULL,
            bound_email text NOT NULL
        );

        CREATE TABLE talent.event (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            type text NOT NULL,
            entity_kind text NOT NULL,
            entity_id text NOT NULL,
            actor_id uuid,
            at timestamptz NOT NULL DEFAULT now(),
            payload jsonb NOT NULL DEFAULT '{}'
        );
        CREATE INDEX event_by_entity ON talent.event (entity_kind, entity_id, at);

        CREATE TABLE talent.comms_send (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            talent_id uuid REFERENCES talent.talent(id),
            from_addr text NOT NULL DEFAULT 'desk@uzemarkets.com',
            kind talent.comms_kind NOT NULL,
            subject text NOT NULL,
            sent_at timestamptz,
            queued_at timestamptz NOT NULL DEFAULT now(),
            provider_ref text
        );
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS talent.comms_send;
        DROP TABLE IF EXISTS talent.event;
        DROP TABLE IF EXISTS talent.session;
        DROP TABLE IF EXISTS talent.mock_changelog;
        DROP TABLE IF EXISTS talent.mock_alias;
        DROP TABLE IF EXISTS talent.mock;
        DROP TABLE IF EXISTS talent.grant;
        DROP TABLE IF EXISTS talent.roadmap_binding;
        DROP TABLE IF EXISTS talent.talent_expertise;
        DROP TABLE IF EXISTS talent.talent;
        DROP TYPE IF EXISTS talent.comms_kind;
        DROP TYPE IF EXISTS talent.settlement_rail;
        DROP TYPE IF EXISTS talent.mock_status;
        DROP TYPE IF EXISTS talent.grant_surface;
        DROP TYPE IF EXISTS talent.proficiency;
        DROP TYPE IF EXISTS talent.realm;
        DROP TYPE IF EXISTS talent.role;
        DROP TYPE IF EXISTS talent.mock_track;
        DROP TYPE IF EXISTS talent.track;
        DROP TYPE IF EXISTS talent.talent_type;
        DROP SCHEMA IF EXISTS talent;
    """)
