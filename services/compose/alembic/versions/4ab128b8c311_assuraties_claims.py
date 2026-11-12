"""assuraties_claims

Revision ID: 4ab128b8c311
Revises: 7cef249c9b40
Create Date: 2026-11-09

ASSURATIES — the claim > judge > resolved extension
(docs/specifications/07-ASSURATIES-CLAIM-RESOLUTION-EXTENSION.md).
Strictly additive:

  - new enums claim_class (RWA | HICRE_ASSET | HICRE_PERIOD),
    claim_period_kind (MONTHLY | QUARTERLY | ANNUAL |
    HISTORICAL_TOTAL), claim_status (ISSUED | CHALLENGED |
    UNDER_RESOLUTION | RESOLVED_TRUE | RESOLVED_FALSE |
    ASSURATIZED), confidential_tier (STANDARD | ARCIUM).
  - new table claim: one attributable claim hanging off a
    marketplace Intent (real FK, the Bid precedent), claimed by a
    trust-layer Entity (plain string, the R4 rule). bondAmount is
    mock units — recorded, never moved (the Iron Rule). The
    jurorReport and challenge columns carry the resolution record;
    the append-only EventLog carries the trail.

Frozen artifact: literals only, no live application imports.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ab128b8c311'
down_revision: Union[str, Sequence[str], None] = '7cef249c9b40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    claim_class = sa.Enum(
        'RWA', 'HICRE_ASSET', 'HICRE_PERIOD', name='claim_class'
    )
    claim_period_kind = sa.Enum(
        'MONTHLY', 'QUARTERLY', 'ANNUAL', 'HISTORICAL_TOTAL',
        name='claim_period_kind',
    )
    claim_status = sa.Enum(
        'ISSUED', 'CHALLENGED', 'UNDER_RESOLUTION', 'RESOLVED_TRUE',
        'RESOLVED_FALSE', 'ASSURATIZED', name='claim_status',
    )
    confidential_tier = sa.Enum(
        'STANDARD', 'ARCIUM', name='confidential_tier'
    )
    op.create_table(
        'claim',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('intentId', sa.String(), nullable=False),
        sa.Column(
            'claimClass', claim_class, nullable=False
        ),
        sa.Column(
            'periodKind', claim_period_kind, nullable=True
        ),
        sa.Column('statement', sa.String(), nullable=False),
        sa.Column('claimedValue', sa.JSON(), nullable=False),
        sa.Column('claimantEntityId', sa.String(), nullable=False),
        sa.Column('bondAmount', sa.BigInteger(), nullable=False),
        sa.Column('status', claim_status, nullable=False),
        sa.Column(
            'confidentialTier', confidential_tier, nullable=False
        ),
        sa.Column('jurorReport', sa.JSON(), nullable=True),
        sa.Column('challenge', sa.JSON(), nullable=True),
        sa.Column('createdAt', sa.BigInteger(), nullable=False),
        sa.Column('resolvedAt', sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(['intentId'], ['intent.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_claim_intentId'), 'claim', ['intentId'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_claim_intentId'), table_name='claim')
    op.drop_table('claim')
    sa.Enum(name='confidential_tier').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='claim_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='claim_period_kind').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='claim_class').drop(op.get_bind(), checkfirst=True)
