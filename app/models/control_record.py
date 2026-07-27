import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.control_checklist_item import ControlPeriod


class ControlRecord(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """One filled-in org-wide checklist for a single day (period=daily) or
    calendar month (period=monthly, stored as that month's first day).
    At most one *live* record per (org, period, period_date) — enforced by
    a partial unique index that ignores soft-deleted rows, so a deleted
    record doesn't block re-filling that same day/month."""

    __tablename__ = "control_records"
    __table_args__ = (
        Index(
            "uq_control_record_live_period",
            "organization_id",
            "period",
            "period_date",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    period: Mapped[ControlPeriod] = mapped_column(
        Enum(
            ControlPeriod,
            name="control_period",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    period_date: Mapped[date] = mapped_column(Date, nullable=False)
    signatory_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    has_deviation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
