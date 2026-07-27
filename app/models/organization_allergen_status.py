import uuid

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OrganizationAllergenStatus(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Per-organization 'is this allergen present in our production' toggle.
    Auto-seeded (one row per Allergen) when an organization is created."""

    __tablename__ = "organization_allergen_status"
    __table_args__ = (UniqueConstraint("organization_id", "allergen_id", name="uq_org_allergen"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    allergen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("allergens.id", ondelete="CASCADE"), nullable=False
    )
    present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
