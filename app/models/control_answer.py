import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.control_checklist_item import NUMERIC_VALUE


class ControlAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Current state of one ControlChecklistItem on a ControlRecord.
    No row = PENDING, answer=True = PASS, answer=False = DEVIATION.
    For numeric items the server sets `answer` from the reading and keeps a
    copy of the limits it was judged against, so later range changes never
    rewrite past verdicts.
    Rows hold the *current* state only; every change is also appended to
    ControlAuditEvent, which is the immutable history."""

    __tablename__ = "control_answers"
    __table_args__ = (
        UniqueConstraint(
            "control_record_id", "control_checklist_item_id", name="uq_control_answer_item"
        ),
    )

    control_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("control_records.id", ondelete="CASCADE"), nullable=False
    )
    control_checklist_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("control_checklist_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    answer: Mapped[bool] = mapped_column(Boolean, nullable=False)
    numeric_value: Mapped[Decimal | None] = mapped_column(NUMERIC_VALUE, nullable=True)
    min_value: Mapped[Decimal | None] = mapped_column(NUMERIC_VALUE, nullable=True)
    max_value: Mapped[Decimal | None] = mapped_column(NUMERIC_VALUE, nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    # Who physically did the work (picked on a shared kitchen device). The
    # signed-in account that saved it is recorded separately. Null only on rows
    # written before this field existed.
    performed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
