"""staging_provider_snapshot

Revision ID: 7cef249c9b40
Revises: 4a9a010e2218
Create Date: 2026-11-08

DevPartner onboarding gate (James directive, 2026-11-08 evening) —
strictly additive:

  - new table staging_provider_snapshot: the staging area for the
    partner ingestion API. POST /api/v1/partners/ingest writes here
    by default with approvalStatus PENDING; nothing reaches the
    live provider_snapshot table until an admin approves the staged
    payload via POST /api/v1/admin/partners/approve/{staging_id}.
    Rejections record approvalStatus REJECTED plus rejectionReason.
    reviewedAt / reviewedBy capture the decision.

    This is the Evidence-Gated Architecture applied to partner
    onboarding: partner data is reviewed before it can be consumed,
    and staged payloads remain provider_status UNVERIFIED even
    after approval (approval gates consumption, not truth).

Frozen artifact: literals only, no live application imports.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7cef249c9b40'
down_revision: Union[str, Sequence[str], None] = '4a9a010e2218'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'staging_provider_snapshot',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('partnerId', sa.String(), nullable=False),
        sa.Column('dataCategory', sa.String(), nullable=False),
        sa.Column('rawPayload', sa.JSON(), nullable=False),
        sa.Column('fetchedAt', sa.BigInteger(), nullable=False),
        sa.Column('approvalStatus', sa.String(), nullable=False),
        sa.Column('rejectionReason', sa.String(), nullable=True),
        sa.Column('reviewedAt', sa.BigInteger(), nullable=True),
        sa.Column('reviewedBy', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_staging_provider_snapshot_partnerId'),
        'staging_provider_snapshot',
        ['partnerId'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_staging_provider_snapshot_partnerId'),
        table_name='staging_provider_snapshot',
    )
    op.drop_table('staging_provider_snapshot')
