"""underwrite_reports

Revision ID: f0b56811b3ea
Revises: c41a9e72d5b0
Create Date: 2026-11-13

UZE Underwrite reports (2026-11-13 night sprint). Strictly
additive: three new tables —

  - underwrite_report: one persisted underwrite run per door
    (multiyear / mcp / email), with its input hash, engine
    version, request payload of record, result verbatim, and
    the honest record of claim issuance (claimId FK to
    claim.id when a claim was issued, claimStatus, claimNote).
  - report_notification: the notification beats the service
    composes for a report (status QUEUED — composed, never
    claimed sent).
  - comp_pool_entry: anonymized opt-in comp contributions —
    per-unit canonical lines only, contributorRef is a hash,
    never an identity.

Frozen artifact: literals only, mirroring models.py
(UnderwriteReport / ReportNotification / CompPoolEntry); this
revision never imports live application source.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0b56811b3ea'
down_revision: Union[str, Sequence[str], None] = 'c41a9e72d5b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'underwrite_report',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('createdAt', sa.BigInteger(), nullable=False),
        sa.Column('door', sa.String(), nullable=False),
        sa.Column('sender', sa.String(), nullable=True),
        sa.Column('subjectProfile', sa.JSON(), nullable=True),
        sa.Column('inputHash', sa.String(), nullable=False),
        sa.Column('engineVersion', sa.String(), nullable=False),
        sa.Column('requestPayload', sa.JSON(), nullable=False),
        sa.Column('result', sa.JSON(), nullable=False),
        sa.Column('contributeComps', sa.Boolean(), nullable=False),
        sa.Column('claimId', sa.String(), nullable=True),
        sa.Column('claimStatus', sa.String(), nullable=False),
        sa.Column('claimNote', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['claimId'], ['claim.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'report_notification',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('reportId', sa.String(), nullable=False),
        sa.Column('beat', sa.Integer(), nullable=False),
        sa.Column('recipient', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('createdAt', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['reportId'], ['underwrite_report.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_report_notification_reportId'),
        'report_notification',
        ['reportId'],
        unique=False,
    )
    op.create_table(
        'comp_pool_entry',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('microRegion', sa.String(), nullable=False),
        sa.Column('propertyType', sa.String(), nullable=True),
        sa.Column('propertyClass', sa.String(), nullable=True),
        sa.Column('vintageBand', sa.String(), nullable=True),
        sa.Column('unitCount', sa.Integer(), nullable=True),
        sa.Column('period', sa.String(), nullable=True),
        sa.Column('lines', sa.JSON(), nullable=False),
        sa.Column('contributorRef', sa.String(), nullable=False),
        sa.Column('creditUnits', sa.Integer(), nullable=False),
        sa.Column('createdAt', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_comp_pool_entry_microRegion'),
        'comp_pool_entry',
        ['microRegion'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_comp_pool_entry_microRegion'),
        table_name='comp_pool_entry',
    )
    op.drop_table('comp_pool_entry')
    op.drop_index(
        op.f('ix_report_notification_reportId'),
        table_name='report_notification',
    )
    op.drop_table('report_notification')
    op.drop_table('underwrite_report')
