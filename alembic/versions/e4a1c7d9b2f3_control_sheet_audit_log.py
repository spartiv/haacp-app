"""control sheet workflow and append-only audit log

- control_records: status (draft/submitted), submitted_at, submitted_by_user_id
- control_answers: corrective_action, checked_by_user_id, checked_at
- control_audit_events: new append-only table, protected by a trigger

Existing data: every existing record was filled through the full-sheet
endpoint, so it is backfilled as `submitted` by its signatory; existing
answers are attributed to the record's signatory at the answer's last update.
No audit events are synthesized for old records (their pre-edit snapshots
remain in control_record_history).

Revision ID: e4a1c7d9b2f3
Revises: b89dab09c9d7
Create Date: 2026-10-18 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e4a1c7d9b2f3'
down_revision: Union[str, Sequence[str], None] = 'b89dab09c9d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Frozen copy of app/models/control_audit_event.py's trigger SQL (migrations must not
# change when app code does).
IMMUTABLE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION control_audit_events_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION USING
        MESSAGE = 'control_audit_events is append-only: ' || TG_OP || ' is not allowed',
        ERRCODE = 'insufficient_privilege';
END;
$$
"""
ROW_TRIGGER_SQL = """
CREATE TRIGGER control_audit_events_no_update_delete
BEFORE UPDATE OR DELETE ON control_audit_events
FOR EACH ROW EXECUTE FUNCTION control_audit_events_immutable()
"""
TRUNCATE_TRIGGER_SQL = """
CREATE TRIGGER control_audit_events_no_truncate
BEFORE TRUNCATE ON control_audit_events
FOR EACH STATEMENT EXECUTE FUNCTION control_audit_events_immutable()
"""
DROP_FUNCTION_SQL = "DROP FUNCTION IF EXISTS control_audit_events_immutable()"

record_status = postgresql.ENUM('draft', 'submitted', name='control_record_status')
item_status = postgresql.ENUM('pending', 'pass', 'deviation', name='control_item_status')
event_type = postgresql.ENUM(
    'item_checked', 'item_amended', 'record_submitted', name='control_audit_event_type'
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    record_status.create(bind, checkfirst=True)
    item_status.create(bind, checkfirst=True)
    event_type.create(bind, checkfirst=True)

    # ---- control_records ----
    op.add_column(
        'control_records',
        sa.Column(
            'status',
            postgresql.ENUM('draft', 'submitted', name='control_record_status', create_type=False),
            nullable=False,
            server_default='submitted',  # backfill only; dropped below
        ),
    )
    op.alter_column('control_records', 'status', server_default=None)
    op.add_column(
        'control_records', sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column('control_records', sa.Column('submitted_by_user_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'control_records_submitted_by_user_id_fkey',
        'control_records',
        'users',
        ['submitted_by_user_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    op.execute(
        "UPDATE control_records SET submitted_at = updated_at, "
        "submitted_by_user_id = signatory_user_id"
    )

    # ---- control_answers ----
    op.add_column('control_answers', sa.Column('corrective_action', sa.Text(), nullable=True))
    op.add_column('control_answers', sa.Column('checked_by_user_id', sa.UUID(), nullable=True))
    op.add_column(
        'control_answers',
        sa.Column(
            'checked_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
    )
    op.execute(
        "UPDATE control_answers AS a SET checked_by_user_id = r.signatory_user_id, "
        "checked_at = a.updated_at FROM control_records AS r WHERE r.id = a.control_record_id"
    )
    op.alter_column('control_answers', 'checked_by_user_id', nullable=False)
    op.create_foreign_key(
        'control_answers_checked_by_user_id_fkey',
        'control_answers',
        'users',
        ['checked_by_user_id'],
        ['id'],
        ondelete='RESTRICT',
    )

    # ---- control_audit_events ----
    op.create_table(
        'control_audit_events',
        sa.Column('seq', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('control_record_id', sa.UUID(), nullable=False),
        sa.Column('control_checklist_item_id', sa.UUID(), nullable=True),
        sa.Column(
            'event_type',
            postgresql.ENUM(
                'item_checked',
                'item_amended',
                'record_submitted',
                name='control_audit_event_type',
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            'previous_status',
            postgresql.ENUM(
                'pending', 'pass', 'deviation', name='control_item_status', create_type=False
            ),
            nullable=True,
        ),
        sa.Column(
            'new_status',
            postgresql.ENUM(
                'pending', 'pass', 'deviation', name='control_item_status', create_type=False
            ),
            nullable=True,
        ),
        sa.Column('corrective_action', sa.Text(), nullable=True),
        sa.Column('amendment_reason', sa.Text(), nullable=True),
        sa.Column('actor_user_id', sa.UUID(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('clock_timestamp()'),
            nullable=False,
        ),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(
            ['control_checklist_item_id'], ['control_checklist_items.id'], ondelete='RESTRICT'
        ),
        sa.ForeignKeyConstraint(
            ['control_record_id'], ['control_records.id'], ondelete='RESTRICT'
        ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('seq'),
    )
    op.create_index(
        'ix_control_audit_events_record_seq',
        'control_audit_events',
        ['control_record_id', 'seq'],
        unique=False,
    )
    op.execute(IMMUTABLE_FUNCTION_SQL)
    op.execute(ROW_TRIGGER_SQL)
    op.execute(TRUNCATE_TRIGGER_SQL)


def downgrade() -> None:
    """Downgrade schema. Drops the audit log — run only on non-production data."""
    op.drop_index('ix_control_audit_events_record_seq', table_name='control_audit_events')
    op.drop_table('control_audit_events')  # also drops its triggers
    op.execute(DROP_FUNCTION_SQL)

    op.drop_constraint(
        'control_answers_checked_by_user_id_fkey', 'control_answers', type_='foreignkey'
    )
    op.drop_column('control_answers', 'checked_at')
    op.drop_column('control_answers', 'checked_by_user_id')
    op.drop_column('control_answers', 'corrective_action')

    op.drop_constraint(
        'control_records_submitted_by_user_id_fkey', 'control_records', type_='foreignkey'
    )
    op.drop_column('control_records', 'submitted_by_user_id')
    op.drop_column('control_records', 'submitted_at')
    op.drop_column('control_records', 'status')

    bind = op.get_bind()
    event_type.drop(bind, checkfirst=True)
    item_status.drop(bind, checkfirst=True)
    record_status.drop(bind, checkfirst=True)
