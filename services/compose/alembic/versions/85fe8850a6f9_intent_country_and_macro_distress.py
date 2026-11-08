"""intent_country_and_macro_distress

Revision ID: 85fe8850a6f9
Revises: 4efec7ad31a2
Create Date: 2026-11-08

Paraguay market extension (DeepSeek directive relayed by James,
2026-11-08) — strictly additive:

  - new enum country_code (BR, PY, UY, US) + intent."countryCode"
    — the dynamic country-extension axis: new markets arrive as
    enum members, not schema changes
  - intent."macroDistressExit" (boolean) — the dual-track flag:
    the owner is optimizing the asset while preparing its
    liquidation route (Arcium sealed-bid auction into USDC)

Both nullable: pre-existing rows stay valid. Frozen artifact:
literals only, no live application imports.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '85fe8850a6f9'
down_revision: Union[str, Sequence[str], None] = '4efec7ad31a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    country_code = sa.Enum('BR', 'PY', 'UY', 'US', name='country_code')
    country_code.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'intent', sa.Column('countryCode', country_code, nullable=True)
    )
    op.add_column(
        'intent', sa.Column('macroDistressExit', sa.Boolean(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('intent', 'macroDistressExit')
    op.drop_column('intent', 'countryCode')
    sa.Enum(name='country_code').drop(op.get_bind(), checkfirst=True)
