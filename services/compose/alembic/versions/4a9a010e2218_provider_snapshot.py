"""provider_snapshot

Revision ID: 4a9a010e2218
Revises: e8048229faab
Create Date: 2026-11-08

DevPartner Software Stack Portal (partners/README.md) — strictly
additive:

  - new table provider_snapshot: the Snapshot Pattern cache for the
    partner ingestion API (POST /api/v1/partners/ingest). Stores the
    partner's validated payload verbatim (rawPayload JSON), the
    partner id, a data category, the fetch timestamp, and two status
    fields: cacheStatus (LIVE) and providerStatus — written
    "UNVERIFIED" for every snapshot under the Evidence-Gated
    Architecture (docs/specifications/
    06-EVIDENCE-GATED-ARCHITECTURE.md): a snapshot is partner-claimed
    data, never verified fact, and triggers nothing downstream.

Frozen artifact: literals only, no live application imports.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a9a010e2218'
down_revision: Union[str, Sequence[str], None] = 'e8048229faab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'provider_snapshot',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('partnerId', sa.String(), nullable=False),
        sa.Column('dataCategory', sa.String(), nullable=False),
        sa.Column('rawPayload', sa.JSON(), nullable=False),
        sa.Column('fetchedAt', sa.BigInteger(), nullable=False),
        sa.Column('cacheStatus', sa.String(), nullable=False),
        sa.Column('providerStatus', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_provider_snapshot_partnerId'),
        'provider_snapshot',
        ['partnerId'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_provider_snapshot_partnerId'),
        table_name='provider_snapshot',
    )
    op.drop_table('provider_snapshot')
