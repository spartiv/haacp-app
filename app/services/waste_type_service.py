import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import WasteType

logger = logging.getLogger(__name__)


class WasteTypeNotFoundError(NotFoundError):
    code = "waste_type_not_found"
    message = "Waste type not found"


async def create_waste_type(
    db: AsyncSession, *, organization_id: uuid.UUID, name: str, disposal_method: str
) -> WasteType:
    waste_type = WasteType(
        organization_id=organization_id, name=name, disposal_method=disposal_method
    )
    db.add(waste_type)
    await db.commit()
    logger.info(
        "Waste type created: waste_type_id=%s organization_id=%s", waste_type.id, organization_id
    )
    return waste_type


async def list_waste_types(db: AsyncSession, *, organization_id: uuid.UUID) -> list[WasteType]:
    result = await db.execute(
        select(WasteType)
        .where(WasteType.organization_id == organization_id, WasteType.deleted_at.is_(None))
        .order_by(WasteType.name)
    )
    return list(result.scalars().all())


async def get_waste_type(
    db: AsyncSession, *, organization_id: uuid.UUID, waste_type_id: uuid.UUID
) -> WasteType:
    result = await db.execute(
        select(WasteType).where(
            WasteType.id == waste_type_id,
            WasteType.organization_id == organization_id,
            WasteType.deleted_at.is_(None),
        )
    )
    waste_type = result.scalar_one_or_none()
    if waste_type is None:
        raise WasteTypeNotFoundError
    return waste_type


async def update_waste_type(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    waste_type_id: uuid.UUID,
    name: str | None = None,
    disposal_method: str | None = None,
) -> WasteType:
    waste_type = await get_waste_type(
        db, organization_id=organization_id, waste_type_id=waste_type_id
    )
    if name is not None:
        waste_type.name = name
    if disposal_method is not None:
        waste_type.disposal_method = disposal_method
    await db.commit()
    return waste_type


async def soft_delete_waste_type(
    db: AsyncSession, *, organization_id: uuid.UUID, waste_type_id: uuid.UUID
) -> None:
    waste_type = await get_waste_type(
        db, organization_id=organization_id, waste_type_id=waste_type_id
    )
    waste_type.deleted_at = datetime.now(UTC)
    await db.commit()
    logger.info(
        "Waste type deleted: waste_type_id=%s organization_id=%s", waste_type_id, organization_id
    )
