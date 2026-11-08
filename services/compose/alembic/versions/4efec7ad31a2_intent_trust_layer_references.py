"""intent_trust_layer_references

Revision ID: 4efec7ad31a2
Revises: 851420c2adc4
Create Date: 2026-11-08

James's Assurative V2 / UZEmarkets stack clarification
(2026-11-08) — strictly additive:

  - intent."entityId" / intent."affiliateId": nullable STRING
    references to the trust layer's Entity / Affiliate (UUID
    values carried as strings; cross-database references are
    never foreign keys — Scope Tenet 01 + the R4 rule)
  - new enum execution_environment (NEAR_INTENTS, ARCIUM_AUCTION)
    + intent."executionEnvironment"
  - new enum agent_attestation (HUMAN, AGENT_X401)
    + intent."agentAttestation"

All nullable: pre-existing rows stay valid. Frozen artifact:
literals only, no live application imports.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4efec7ad31a2'
down_revision: Union[str, Sequence[str], None] = '851420c2adc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    execution_environment = sa.Enum(
        'NEAR_INTENTS', 'ARCIUM_AUCTION', name='execution_environment'
    )
    execution_environment.create(op.get_bind(), checkfirst=True)
    agent_attestation = sa.Enum(
        'HUMAN', 'AGENT_X401', name='agent_attestation'
    )
    agent_attestation.create(op.get_bind(), checkfirst=True)
    op.add_column('intent', sa.Column('entityId', sa.String(), nullable=True))
    op.add_column(
        'intent', sa.Column('affiliateId', sa.String(), nullable=True)
    )
    op.add_column(
        'intent',
        sa.Column('executionEnvironment', execution_environment, nullable=True),
    )
    op.add_column(
        'intent',
        sa.Column('agentAttestation', agent_attestation, nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('intent', 'agentAttestation')
    op.drop_column('intent', 'executionEnvironment')
    op.drop_column('intent', 'affiliateId')
    op.drop_column('intent', 'entityId')
    sa.Enum(name='agent_attestation').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='execution_environment').drop(op.get_bind(), checkfirst=True)
