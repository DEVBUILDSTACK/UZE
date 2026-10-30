"""OfferKind is the OfferSnapshot payload discriminator (tap (c)).

Revision ID: b3d91c7e5a02
Revises: 9d4c1f7a2b58
Create Date: 2026-10-30

WHY THIS REVISION EXISTS (schema review finding, James's tap (c)
2026-10-30): the payload discriminated union was keyed on Rail, whose
set includes DINING_TASK — a task rail in a different state machine
that produces no offer. It sat in the offer union as a dead branch.
The resolution, landed in the authoring source in the same change:
OfferKind (ticket | stay | flight | facility | parking | transfer)
is the discriminator; the payload tag property is renamed `rail` ->
`kind`; union members are named for their kind (TicketOfferDetail,
...); Rail is retained for routing and dispatch; the ONE mapping is
offer_kind_for_rail() (DINING_TASK -> None).

WHAT THIS REVISION ADDS at the DB level — one CHECK constraint,
nothing else:

  ck_offer_snapshot_payload_kind ON offer_snapshot:
      (payload ->> 'kind') IN
      ('ticket', 'stay', 'flight', 'facility', 'parking', 'transfer')

The generated Pydantic union refuses out-of-set tags for API writers;
this constraint is the same law for raw-SQL writers — the DB-level
presence of the discriminator split. The value set is OfferKind's,
frozen here as migrations must be (a migration never imports the
live models). No table, column, or prior object changes; no backfill
exists to run — the schema is pre-staging and no production rows
exist anywhere.

DOWNGRADE drops exactly the constraint this revision added.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b3d91c7e5a02"
down_revision = "9d4c1f7a2b58"
branch_labels = None
depends_on = None

_KIND_SET = "('ticket', 'stay', 'flight', 'facility', 'parking', 'transfer')"


def upgrade() -> None:
    # HAND-WRITTEN: the DB-level presence of the OfferKind split —
    # the payload's `kind` tag must be one of the six OfferKind
    # values, for every writer, not only generated-Pydantic writers.
    op.execute(
        "ALTER TABLE offer_snapshot "
        "ADD CONSTRAINT ck_offer_snapshot_payload_kind "
        f"CHECK ((payload ->> 'kind') IN {_KIND_SET})"
    )


def downgrade() -> None:
    # Drops only what this revision added (see module docstring).
    op.execute(
        "ALTER TABLE offer_snapshot "
        "DROP CONSTRAINT ck_offer_snapshot_payload_kind"
    )
