import enum
import uuid
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Connection,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Table,
    Text,
    event,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin, pg_enum
from app.models.control_checklist_item import NUMERIC_VALUE


class ControlItemStatus(enum.StrEnum):
    PENDING = "pending"
    PASS = "pass"
    DEVIATION = "deviation"


class ControlAuditEventType(enum.StrEnum):
    ITEM_CHECKED = "item_checked"  # item changed while the record is a draft
    ITEM_AMENDED = "item_amended"  # item changed after submission (reason required)
    RECORD_SUBMITTED = "record_submitted"


class ControlAuditEvent(UUIDPrimaryKeyMixin, Base):
    """Append-only audit log for control records. Rows are never updated or
    deleted: a Postgres trigger (below, and in the migration) rejects UPDATE,
    DELETE and TRUNCATE, and every foreign key is RESTRICT so deleting a user,
    item or record can't erase history either.

    `seq` gives a strict total order (timestamps can tie within a
    transaction) and doubles as the pagination cursor."""

    __tablename__ = "control_audit_events"
    __table_args__ = (Index("ix_control_audit_events_record_seq", "control_record_id", "seq"),)
    # Fetch server-generated seq/created_at via RETURNING on insert.
    __mapper_args__ = {"eager_defaults": True}

    seq: Mapped[int] = mapped_column(BigInteger, Identity(always=True), nullable=False, unique=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    control_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("control_records.id", ondelete="RESTRICT"), nullable=False
    )
    # Null for record-level events (record_submitted).
    control_checklist_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("control_checklist_items.id", ondelete="RESTRICT"),
        nullable=True,
    )
    event_type: Mapped[ControlAuditEventType] = mapped_column(
        pg_enum(ControlAuditEventType, "control_audit_event_type"), nullable=False
    )
    previous_status: Mapped[ControlItemStatus | None] = mapped_column(
        pg_enum(ControlItemStatus, "control_item_status"), nullable=True
    )
    new_status: Mapped[ControlItemStatus | None] = mapped_column(
        pg_enum(ControlItemStatus, "control_item_status"), nullable=True
    )
    # The reading, for numeric items (null for Yes/No items and record events).
    numeric_value: Mapped[Decimal | None] = mapped_column(NUMERIC_VALUE, nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    amendment_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    # Who physically did the work (picked on a shared kitchen device). The
    # signed-in account that saved it is recorded separately. Null only on rows
    # written before this field existed.
    performed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    # clock_timestamp(), not now(): the real moment of the write, not the
    # start of the transaction. Always set by the database, never the client.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )


# Immutability trigger. Kept identical to the migration so tests (which build
# tables with create_all) exercise the same protection as production.
# Each DDL is a single statement: asyncpg can't prepare multi-statement SQL.
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


def _execute(sql: str) -> Callable[..., None]:
    def _listener(target: Table, connection: Connection, **_: object) -> None:
        connection.execute(text(sql))

    return _listener


_table = ControlAuditEvent.__table__
event.listen(_table, "after_create", _execute(IMMUTABLE_FUNCTION_SQL))
event.listen(_table, "after_create", _execute(ROW_TRIGGER_SQL))
event.listen(_table, "after_create", _execute(TRUNCATE_TRIGGER_SQL))
event.listen(_table, "after_drop", _execute(DROP_FUNCTION_SQL))
