import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import Equipment, EquipmentType
from app.services import attachment_service
from app.services.storage import StorageBackend

logger = logging.getLogger(__name__)


class EquipmentNotFoundError(NotFoundError):
    code = "equipment_not_found"
    message = "Equipment not found"


async def create_equipment(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    type: EquipmentType,
    name: str,
    frequency: str,
    amount: int,
    affects_product_safety: bool,
) -> Equipment:
    equipment = Equipment(
        organization_id=organization_id,
        type=type,
        name=name,
        frequency=frequency,
        amount=amount,
        affects_product_safety=affects_product_safety,
    )
    db.add(equipment)
    await db.commit()
    logger.info(
        "Equipment created: equipment_id=%s organization_id=%s", equipment.id, organization_id
    )
    return equipment


async def list_equipment(db: AsyncSession, *, organization_id: uuid.UUID) -> list[Equipment]:
    result = await db.execute(
        select(Equipment)
        .where(Equipment.organization_id == organization_id, Equipment.deleted_at.is_(None))
        .order_by(Equipment.name)
    )
    return list(result.scalars().all())


async def get_equipment(
    db: AsyncSession, *, organization_id: uuid.UUID, equipment_id: uuid.UUID
) -> Equipment:
    result = await db.execute(
        select(Equipment).where(
            Equipment.id == equipment_id,
            Equipment.organization_id == organization_id,
            Equipment.deleted_at.is_(None),
        )
    )
    equipment = result.scalar_one_or_none()
    if equipment is None:
        raise EquipmentNotFoundError
    return equipment


async def update_equipment(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    type: EquipmentType | None = None,
    name: str | None = None,
    frequency: str | None = None,
    amount: int | None = None,
    affects_product_safety: bool | None = None,
) -> Equipment:
    equipment = await get_equipment(db, organization_id=organization_id, equipment_id=equipment_id)
    if type is not None:
        equipment.type = type
    if name is not None:
        equipment.name = name
    if frequency is not None:
        equipment.frequency = frequency
    if amount is not None:
        equipment.amount = amount
    if affects_product_safety is not None:
        equipment.affects_product_safety = affects_product_safety
    await db.commit()
    return equipment


async def soft_delete_equipment(
    db: AsyncSession, *, organization_id: uuid.UUID, equipment_id: uuid.UUID
) -> None:
    equipment = await get_equipment(db, organization_id=organization_id, equipment_id=equipment_id)
    equipment.deleted_at = datetime.now(UTC)
    await db.commit()
    logger.info(
        "Equipment deleted: equipment_id=%s organization_id=%s", equipment_id, organization_id
    )


async def attach_document(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    attachment_id: uuid.UUID,
    storage: StorageBackend,
) -> Equipment:
    equipment = await get_equipment(db, organization_id=organization_id, equipment_id=equipment_id)
    # Validate the attachment exists and belongs to this org before linking it.
    await attachment_service.get_attachment(
        db, organization_id=organization_id, attachment_id=attachment_id
    )
    if equipment.attachment_id is not None:
        old_attachment = await attachment_service.get_attachment(
            db, organization_id=organization_id, attachment_id=equipment.attachment_id
        )
        await attachment_service.delete_attachment(db, attachment=old_attachment, storage=storage)
    equipment.attachment_id = attachment_id
    await db.commit()
    return equipment


async def detach_document(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    storage: StorageBackend,
) -> Equipment:
    equipment = await get_equipment(db, organization_id=organization_id, equipment_id=equipment_id)
    if equipment.attachment_id is not None:
        attachment = await attachment_service.get_attachment(
            db, organization_id=organization_id, attachment_id=equipment.attachment_id
        )
        equipment.attachment_id = None
        await attachment_service.delete_attachment(db, attachment=attachment, storage=storage)
    return equipment
