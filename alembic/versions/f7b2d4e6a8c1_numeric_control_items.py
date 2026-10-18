"""numeric checklist items (temperature readings with a safe range)

- control_checklist_items: item_type (bool/numeric), unit, min_value, max_value
- control_answers: numeric_value + the limits it was judged against
- control_audit_events: numeric_value (adding a column is DDL, so the
  append-only row triggers don't block it; existing rows get NULL)

Existing items become `bool`, so current checklists behave exactly as before.

Revision ID: f7b2d4e6a8c1
Revises: e4a1c7d9b2f3
Create Date: 2026-10-18 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f7b2d4e6a8c1'
down_revision: Union[str, Sequence[str], None] = 'e4a1c7d9b2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

item_type = postgresql.ENUM('bool', 'numeric', name='control_item_type')
VALUE = sa.Numeric(7, 2)


def upgrade() -> None:
    item_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'control_checklist_items',
        sa.Column(
            'item_type',
            postgresql.ENUM('bool', 'numeric', name='control_item_type', create_type=False),
            nullable=False,
            server_default='bool',
        ),
    )
    op.add_column('control_checklist_items', sa.Column('unit', sa.String(length=20), nullable=True))
    op.add_column('control_checklist_items', sa.Column('min_value', VALUE, nullable=True))
    op.add_column('control_checklist_items', sa.Column('max_value', VALUE, nullable=True))
    op.create_check_constraint(
        'ck_control_checklist_items_type_config',
        'control_checklist_items',
        "(item_type = 'bool' AND unit IS NULL AND min_value IS NULL AND max_value IS NULL)"
        " OR (item_type = 'numeric' AND unit IS NOT NULL"
        " AND (min_value IS NOT NULL OR max_value IS NOT NULL)"
        " AND (min_value IS NULL OR max_value IS NULL OR min_value <= max_value))",
    )

    op.add_column('control_answers', sa.Column('numeric_value', VALUE, nullable=True))
    op.add_column('control_answers', sa.Column('min_value', VALUE, nullable=True))
    op.add_column('control_answers', sa.Column('max_value', VALUE, nullable=True))

    op.add_column('control_audit_events', sa.Column('numeric_value', VALUE, nullable=True))


def downgrade() -> None:
    op.drop_column('control_audit_events', 'numeric_value')
    op.drop_column('control_answers', 'max_value')
    op.drop_column('control_answers', 'min_value')
    op.drop_column('control_answers', 'numeric_value')
    op.drop_constraint('ck_control_checklist_items_type_config', 'control_checklist_items', type_='check')
    op.drop_column('control_checklist_items', 'max_value')
    op.drop_column('control_checklist_items', 'min_value')
    op.drop_column('control_checklist_items', 'unit')
    op.drop_column('control_checklist_items', 'item_type')
    item_type.drop(op.get_bind(), checkfirst=True)
