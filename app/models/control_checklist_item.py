import enum
import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum


class ControlPeriod(enum.StrEnum):
    DAILY = "daily"
    MONTHLY = "monthly"


class ControlItemType(enum.StrEnum):
    BOOL = "bool"  # Так/Ні: "Ні" is the deviation
    NUMERIC = "numeric"  # a measured value (e.g. °C): outside [min, max] is the deviation


# Readings are stored with 2 decimals, e.g. -18.50 or 123.45.
NUMERIC_VALUE = Numeric(7, 2)


class ControlChecklistItem(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A question on the org-wide daily or monthly checklist (distinct from a
    product's batch checklist): either Yes/No ('No' is the deviation) or a
    numeric reading with a safe range (outside it is the deviation). The type
    is fixed at creation. Soft-deleted (never hard-deleted) because past
    ControlAnswer rows reference it."""

    __tablename__ = "control_checklist_items"
    __table_args__ = (
        CheckConstraint(
            "(item_type = 'bool' AND unit IS NULL AND min_value IS NULL AND max_value IS NULL)"
            " OR (item_type = 'numeric' AND unit IS NOT NULL"
            " AND (min_value IS NOT NULL OR max_value IS NOT NULL)"
            " AND (min_value IS NULL OR max_value IS NULL OR min_value <= max_value))",
            name="ck_control_checklist_items_type_config",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    period: Mapped[ControlPeriod] = mapped_column(
        pg_enum(ControlPeriod, "control_period"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    item_type: Mapped[ControlItemType] = mapped_column(
        pg_enum(ControlItemType, "control_item_type"),
        nullable=False,
        default=ControlItemType.BOOL,
        server_default=ControlItemType.BOOL.value,
    )
    # Numeric items only. Either bound may be open (e.g. freezer: max -18 only).
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    min_value: Mapped[Decimal | None] = mapped_column(NUMERIC_VALUE, nullable=True)
    max_value: Mapped[Decimal | None] = mapped_column(NUMERIC_VALUE, nullable=True)
