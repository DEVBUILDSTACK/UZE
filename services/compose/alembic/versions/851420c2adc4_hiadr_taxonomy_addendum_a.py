"""hiadr_taxonomy_addendum_a

Revision ID: 851420c2adc4
Revises: a6347160a7eb
Create Date: 2026-11-08

Addendum A (HIADR taxonomy, ratified 2026-11-08 via DeepSeek,
relayed by James) — strictly additive:

  - new enum asset_subclass (H, I, A, D, R)
  - intent."assetSubclass"  (nullable — pre-HIADR rows stay valid;
    the API enforces the track rules on new specs)
  - intent."targetArea"     (JSON: Radius form or GeoJSON Polygon)
  - intent."subterraneanContext" (JSON: the A/R data layer)
  - micro_region."pulseData"     (JSON: the Content Desk layer)

Frozen artifact: literals only, no live application imports.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '851420c2adc4'
down_revision: Union[str, Sequence[str], None] = 'a6347160a7eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    asset_subclass = sa.Enum('H', 'I', 'A', 'D', 'R', name='asset_subclass')
    asset_subclass.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'intent',
        sa.Column('assetSubclass', asset_subclass, nullable=True),
    )
    op.add_column('intent', sa.Column('targetArea', sa.JSON(), nullable=True))
    op.add_column(
        'intent', sa.Column('subterraneanContext', sa.JSON(), nullable=True)
    )
    op.add_column(
        'micro_region', sa.Column('pulseData', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('micro_region', 'pulseData')
    op.drop_column('intent', 'subterraneanContext')
    op.drop_column('intent', 'targetArea')
    op.drop_column('intent', 'assetSubclass')
    sa.Enum(name='asset_subclass').drop(op.get_bind(), checkfirst=True)
