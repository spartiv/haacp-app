import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import Chemical, ChemicalCategory
from app.services import attachment_service
from app.services.storage import StorageBackend

logger = logging.getLogger(__name__)


class ChemicalNotFoundError(NotFoundError):
    code = "chemical_not_found"
    message = "Chemical not found"


async def create_chemical(
    db: AsyncSession, *, organization_id: uuid.UUID, name: str, category: ChemicalCategory
) -> Chemical:
    chemical = Chemical(organization_id=organization_id, name=name, category=category)
    db.add(chemical)
    await db.commit()
    logger.info("Chemical created: chemical_id=%s organization_id=%s", chemical.id, organization_id)
    return chemical


async def list_chemicals(db: AsyncSession, *, organization_id: uuid.UUID) -> list[Chemical]:
    result = await db.execute(
        select(Chemical)
        .where(Chemical.organization_id == organization_id, Chemical.deleted_at.is_(None))
        .order_by(Chemical.name)
    )
    return list(result.scalars().all())


async def get_chemical(
    db: AsyncSession, *, organization_id: uuid.UUID, chemical_id: uuid.UUID
) -> Chemical:
    result = await db.execute(
        select(Chemical).where(
            Chemical.id == chemical_id,
            Chemical.organization_id == organization_id,
            Chemical.deleted_at.is_(None),
        )
    )
    chemical = result.scalar_one_or_none()
    if chemical is None:
        raise ChemicalNotFoundError
    return chemical


async def update_chemical(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    chemical_id: uuid.UUID,
    name: str | None = None,
    category: ChemicalCategory | None = None,
) -> Chemical:
    chemical = await get_chemical(db, organization_id=organization_id, chemical_id=chemical_id)
    if name is not None:
        chemical.name = name
    if category is not None:
        chemical.category = category
    await db.commit()
    return chemical


async def soft_delete_chemical(
    db: AsyncSession, *, organization_id: uuid.UUID, chemical_id: uuid.UUID
) -> None:
    chemical = await get_chemical(db, organization_id=organization_id, chemical_id=chemical_id)
    chemical.deleted_at = datetime.now(UTC)
    await db.commit()
    logger.info("Chemical deleted: chemical_id=%s organization_id=%s", chemical_id, organization_id)


async def attach_document(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    chemical_id: uuid.UUID,
    attachment_id: uuid.UUID,
    storage: StorageBackend,
) -> Chemical:
    chemical = await get_chemical(db, organization_id=organization_id, chemical_id=chemical_id)
    await attachment_service.attach_document_to(
        db,
        entity=chemical,
        organization_id=organization_id,
        attachment_id=attachment_id,
        storage=storage,
    )
    await db.commit()
    return chemical


async def detach_document(
    db: AsyncSession, *, organization_id: uuid.UUID, chemical_id: uuid.UUID, storage: StorageBackend
) -> Chemical:
    chemical = await get_chemical(db, organization_id=organization_id, chemical_id=chemical_id)
    await attachment_service.detach_document_from(
        db, entity=chemical, organization_id=organization_id, storage=storage
    )
    return chemical
