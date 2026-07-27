import uuid

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ControlAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One Yes/No response to a ControlChecklistItem, for a specific
    ControlRecord."""

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
