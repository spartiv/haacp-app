"""performed_by: who physically did the work (shared kitchen devices)

Adds performed_by_user_id to control_answers, control_audit_events,
event_entries and batches. The signed-in account that saved the row is still
recorded in the existing columns (checked_by / actor / responsible / signatory).

Backfill: existing answers, entries and batches were done by whoever saved
them. control_audit_events is append-only (UPDATE is blocked by a trigger),
so its old rows stay NULL; the API falls back to the actor for those.

Revision ID: a3c5e7f9b1d2
Revises: f7b2d4e6a8c1
Create Date: 2026-10-18 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a3c5e7f9b1d2'
down_revision: Union[str, Sequence[str], None] = 'f7b2d4e6a8c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# table -> column holding the account that saved the row (used to backfill)
TABLES = {
    'control_answers': 'checked_by_user_id',
    'control_audit_events': None,
    'event_entries': 'responsible_user_id',
    'batches': 'signatory_user_id',
}


def upgrade() -> None:
    for table, saved_by in TABLES.items():
        op.add_column(table, sa.Column('performed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            f'fk_{table}_performed_by_user_id_users',
            table,
            'users',
            ['performed_by_user_id'],
            ['id'],
            ondelete='RESTRICT',
        )
        if saved_by is not None:
            op.execute(f'UPDATE {table} SET performed_by_user_id = {saved_by}')


def downgrade() -> None:
    for table in TABLES:
        op.drop_constraint(f'fk_{table}_performed_by_user_id_users', table, type_='foreignkey')
        op.drop_column(table, 'performed_by_user_id')
