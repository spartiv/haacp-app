import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import Allergen, OrganizationAllergenStatus

logger = logging.getLogger(__name__)


class AllergenStatusNotFoundError(NotFoundError):
    code = "allergen_not_found"
    message = "Allergen not found"


async def seed_default_allergen_statuses(db: AsyncSession, *, organization_id: uuid.UUID) -> None:
    """Called once when an organization is created: gives every legal
    allergen a default 'not present' row for this org. Caller is
    responsible for the eventual commit (this only stages inserts)."""
    result = await db.execute(select(Allergen))
    for allergen in result.scalars().all():
        db.add(
            OrganizationAllergenStatus(
                organization_id=organization_id, allergen_id=allergen.id, present=False
            )
        )


async def list_allergen_statuses(
    db: AsyncSession, *, organization_id: uuid.UUID
) -> list[tuple[Allergen, OrganizationAllergenStatus]]:
    result = await db.execute(
        select(Allergen, OrganizationAllergenStatus)
        .join(OrganizationAllergenStatus, OrganizationAllergenStatus.allergen_id == Allergen.id)
        .where(OrganizationAllergenStatus.organization_id == organization_id)
        .order_by(Allergen.position)
    )
    return [(allergen, status) for allergen, status in result.all()]


async def set_allergen_presence(
    db: AsyncSession, *, organization_id: uuid.UUID, allergen_id: uuid.UUID, present: bool
) -> tuple[Allergen, OrganizationAllergenStatus]:
    result = await db.execute(
        select(Allergen, OrganizationAllergenStatus)
        .join(OrganizationAllergenStatus, OrganizationAllergenStatus.allergen_id == Allergen.id)
        .where(
            OrganizationAllergenStatus.organization_id == organization_id,
            Allergen.id == allergen_id,
        )
    )
    row = result.one_or_none()
    if row is None:
        raise AllergenStatusNotFoundError
    allergen, status = row
    status.present = present
    await db.commit()
    logger.info(
        "Allergen presence updated: organization_id=%s allergen_id=%s present=%s",
        organization_id,
        allergen_id,
        present,
    )
    return allergen, status
