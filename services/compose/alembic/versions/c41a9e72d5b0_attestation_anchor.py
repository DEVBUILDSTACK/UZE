"""Attestation anchors for panel verdicts (spec 08 §10).

Revision ID: c41a9e72d5b0
Revises: 4ab128b8c311
Create Date: 2026-11-09

One new table — attestation_anchor: when a juror panel reaches
a verdict, each verdict-returning seat's report hash is anchored
(or the attempt is honestly recorded as DISABLED / UNAVAILABLE).
claimId is a FK to claim.id; anchorStatus is the new
anchor_status enum (SUBMITTED | DISABLED | UNAVAILABLE).

Frozen-artifact discipline: enum and table layouts are written
as literals mirroring models.py (AnchorStatus /
AttestationAnchor); this revision never imports live
application source.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c41a9e72d5b0'
down_revision: Union[str, None] = '4ab128b8c311'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

anchor_status = sa.Enum(
    'SUBMITTED', 'DISABLED', 'UNAVAILABLE', name='anchor_status'
)


def upgrade() -> None:
    op.create_table(
        'attestation_anchor',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('claimId', sa.String(), nullable=False),
        sa.Column('juror', sa.String(), nullable=False),
        sa.Column('attestationHash', sa.String(), nullable=False),
        sa.Column('nearTxRef', sa.String(), nullable=True),
        sa.Column('anchorStatus', anchor_status, nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('createdAt', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['claimId'], ['claim.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_attestation_anchor_claimId',
        'attestation_anchor',
        ['claimId'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        'ix_attestation_anchor_claimId', table_name='attestation_anchor'
    )
    op.drop_table('attestation_anchor')
    anchor_status.drop(op.get_bind(), checkfirst=True)
