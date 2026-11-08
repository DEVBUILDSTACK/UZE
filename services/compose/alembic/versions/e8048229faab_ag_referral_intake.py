"""ag_referral_intake

Revision ID: e8048229faab
Revises: 85fe8850a6f9
Create Date: 2026-11-08

Evidence-gated architecture (docs/specifications/
06-EVIDENCE-GATED-ARCHITECTURE.md) — strictly additive:

  - new enum ag_referral_state (the 15-state A/D/R ladder)
  - new table ag_referral: the agriculture referral intake
    record (idempotency key unique; payload JSON; country code;
    macro-distress flag; epoch created-at). The referral is NOT
    an Intent — it accumulates evidence in linked records as the
    pipeline is built, per the governance spec §3.
  - new linked evidence tables: spatial_assessment,
    provider_proposal, observation, and ai_assessment. The AI
    table stores calculation, signed, scientifically_verified,
    and review_status as separate fields.

COUNTRY CODE TYPE REUSE: the country_code enum type already
exists (created by 85fe8850a6f9); this revision references it
with create_type=False and must not recreate or drop it.

Frozen artifact: literals only, no live application imports.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e8048229faab'
down_revision: Union[str, Sequence[str], None] = '85fe8850a6f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    ag_state = sa.Enum(
        'INTENT_RECEIVED', 'INPUT_VALIDATED',
        'SPATIAL_ASSESSMENT_PENDING', 'SPATIAL_ASSESSMENT_COMPLETED',
        'PROVIDER_ELIGIBILITY_PENDING', 'PROVIDER_PROPOSAL_RECEIVED',
        'FARMER_APPROVAL_PENDING', 'SERVICE_AUTHORIZED',
        'SERVICE_REPORTED_ACTIVE', 'OBSERVATIONS_COLLECTED',
        'OUTCOME_ASSESSED', 'FINANCING_REVIEW',
        'SALE_ELIGIBILITY_REVIEW', 'LISTING_APPROVAL_PENDING',
        'AUCTION_ADAPTER',
        name='ag_referral_state',
    )
    country_code = postgresql.ENUM(
        'BR', 'PY', 'UY', 'US', name='country_code', create_type=False
    )
    op.create_table(
        'ag_referral',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('idempotencyKey', sa.String(), nullable=False),
        sa.Column('state', ag_state, nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('countryCode', country_code, nullable=True),
        sa.Column('macroDistressExit', sa.Boolean(), nullable=True),
        sa.Column('createdAt', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_ag_referral_idempotencyKey',
        'ag_referral',
        ['idempotencyKey'],
        unique=True,
    )
    op.create_table(
        'spatial_assessment',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('referralId', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('geometry', sa.JSON(), nullable=False),
        sa.Column('registryMatches', sa.JSON(), nullable=False),
        sa.Column('confidenceScore', sa.Float(), nullable=True),
        sa.Column('ownershipEstablished', sa.Boolean(), nullable=False),
        sa.Column('createdAt', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['referralId'], ['ag_referral.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_spatial_assessment_referralId',
        'spatial_assessment',
        ['referralId'],
    )
    op.create_table(
        'provider_proposal',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('referralId', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('proposal', sa.JSON(), nullable=False),
        sa.Column('executionAuthorized', sa.Boolean(), nullable=False),
        sa.Column('createdAt', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['referralId'], ['ag_referral.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_provider_proposal_referralId',
        'provider_proposal',
        ['referralId'],
    )
    op.create_table(
        'observation',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('referralId', sa.String(), nullable=False),
        sa.Column('metric', sa.String(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(), nullable=False),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('createdAt', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['referralId'], ['ag_referral.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_observation_referralId', 'observation', ['referralId']
    )
    op.create_table(
        'ai_assessment',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('referralId', sa.String(), nullable=False),
        sa.Column('modelVersion', sa.String(), nullable=False),
        sa.Column('inputEvidenceRefs', sa.JSON(), nullable=False),
        sa.Column('calculation', sa.JSON(), nullable=False),
        sa.Column('estimatedDifferenceValue', sa.Float(), nullable=True),
        sa.Column('estimatedDifferenceUnit', sa.String(), nullable=True),
        sa.Column('signed', sa.Boolean(), nullable=False),
        sa.Column('scientificallyVerified', sa.Boolean(), nullable=False),
        sa.Column('reviewStatus', sa.String(), nullable=False),
        sa.Column('createdAt', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['referralId'], ['ag_referral.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_ai_assessment_referralId', 'ai_assessment', ['referralId']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_ai_assessment_referralId', table_name='ai_assessment')
    op.drop_table('ai_assessment')
    op.drop_index('ix_observation_referralId', table_name='observation')
    op.drop_table('observation')
    op.drop_index(
        'ix_provider_proposal_referralId', table_name='provider_proposal'
    )
    op.drop_table('provider_proposal')
    op.drop_index(
        'ix_spatial_assessment_referralId', table_name='spatial_assessment'
    )
    op.drop_table('spatial_assessment')
    op.drop_index('ix_ag_referral_idempotencyKey', table_name='ag_referral')
    op.drop_table('ag_referral')
    sa.Enum(name='ag_referral_state').drop(op.get_bind(), checkfirst=True)
