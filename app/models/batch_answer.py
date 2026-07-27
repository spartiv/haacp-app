import uuid

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BatchAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One Yes/No response to a ChecklistItem, for a specific Batch."""

    __tablename__ = "batch_answers"
    __table_args__ = (
        UniqueConstraint("batch_id", "checklist_item_id", name="uq_batch_answer_item"),
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False
    )
    checklist_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checklist_items.id", ondelete="CASCADE"), nullable=False
    )
    answer: Mapped[bool] = mapped_column(Boolean, nullable=False)
