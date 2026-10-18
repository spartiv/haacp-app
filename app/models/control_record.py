import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from app.models.control_checklist_item import ControlPeriod


class ControlRecordStatus(enum.StrEnum):
    """`draft` while items are being checked one by one; `submitted` once
    finalized. After submission, item changes are amendments that require a
    reason and are logged as `item_amended`."""

    DRAFT = "draft"
    SUBMITTED = "submitted"


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
        pg_enum(ControlPeriod, "control_period"), nullable=False
    )
    period_date: Mapped[date] = mapped_column(Date, nullable=False)
    signatory_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    has_deviation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ControlRecordStatus] = mapped_column(
        pg_enum(ControlRecordStatus, "control_record_status"),
        nullable=False,
        default=ControlRecordStatus.DRAFT,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
