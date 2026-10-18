import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Batch(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A партія (production batch/lot) of a product, with its filled-in
    checklist. `has_deviation` is computed and stored at write time (any
    'No' answer) so dashboards don't need to recompute it on every read."""

    __tablename__ = "batches"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    production_date: Mapped[date] = mapped_column(Date, nullable=False)
    has_deviation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deviation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    signatory_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Who physically did the work (picked on a shared kitchen device). The
    # signed-in account that saved it is recorded separately. Null only on rows
    # written before this field existed.
    performed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
