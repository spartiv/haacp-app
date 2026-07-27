import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ControlPeriod(enum.StrEnum):
    DAILY = "daily"
    MONTHLY = "monthly"


class ControlChecklistItem(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A Yes/No audit question on the org-wide daily or monthly checklist
    (distinct from a product's batch checklist). 'No' is always the
    deviation answer. Soft-deleted (never hard-deleted) because past
    ControlAnswer rows reference it."""

    __tablename__ = "control_checklist_items"

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
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
