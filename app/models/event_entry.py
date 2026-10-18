import uuid
from datetime import date
from typing import Any

from sqlalchemy import Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class EventEntry(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """One logged event under an EventLogType. `payload` shape depends on
    the log type's schema (standard/water/pests); `has_deviation` is
    computed server-side from that payload at write time."""

    __tablename__ = "event_entries"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    event_log_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("event_log_types.id", ondelete="CASCADE"), nullable=False
    )
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    responsible_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Who physically did the work (picked on a shared kitchen device). The
    # signed-in account that saved it is recorded separately. Null only on rows
    # written before this field existed.
    performed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    has_deviation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
