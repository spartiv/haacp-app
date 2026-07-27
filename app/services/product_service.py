import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import ChecklistItem, Product

logger = logging.getLogger(__name__)


class ProductNotFoundError(NotFoundError):
    code = "product_not_found"
    message = "Product not found"


class ChecklistItemNotFoundError(NotFoundError):
    code = "checklist_item_not_found"
    message = "Checklist item not found"


async def create_product(db: AsyncSession, *, organization_id: uuid.UUID, name: str) -> Product:
    product = Product(organization_id=organization_id, name=name)
    db.add(product)
    await db.commit()
    logger.info("Product created: product_id=%s organization_id=%s", product.id, organization_id)
    return product


async def list_products(db: AsyncSession, *, organization_id: uuid.UUID) -> list[Product]:
    result = await db.execute(
        select(Product)
        .where(Product.organization_id == organization_id, Product.deleted_at.is_(None))
        .order_by(Product.name)
    )
    return list(result.scalars().all())


async def get_product(
    db: AsyncSession, *, organization_id: uuid.UUID, product_id: uuid.UUID
) -> Product:
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.organization_id == organization_id,
            Product.deleted_at.is_(None),
        )
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise ProductNotFoundError
    return product


async def soft_delete_product(
    db: AsyncSession, *, organization_id: uuid.UUID, product_id: uuid.UUID
) -> None:
    product = await get_product(db, organization_id=organization_id, product_id=product_id)
    product.deleted_at = datetime.now(UTC)
    await db.commit()
    logger.info("Product deleted: product_id=%s organization_id=%s", product_id, organization_id)


async def list_checklist_items(
    db: AsyncSession, *, organization_id: uuid.UUID, product_id: uuid.UUID
) -> list[ChecklistItem]:
    await get_product(db, organization_id=organization_id, product_id=product_id)
    result = await db.execute(
        select(ChecklistItem)
        .where(
            ChecklistItem.product_id == product_id,
            ChecklistItem.organization_id == organization_id,
            ChecklistItem.deleted_at.is_(None),
        )
        .order_by(ChecklistItem.position)
    )
    return list(result.scalars().all())


async def add_checklist_item(
    db: AsyncSession, *, organization_id: uuid.UUID, product_id: uuid.UUID, label: str
) -> ChecklistItem:
    await get_product(db, organization_id=organization_id, product_id=product_id)
    existing = await list_checklist_items(
        db, organization_id=organization_id, product_id=product_id
    )
    next_position = max((item.position for item in existing), default=-1) + 1

    item = ChecklistItem(
        organization_id=organization_id,
        product_id=product_id,
        label=label,
        position=next_position,
    )
    db.add(item)
    await db.commit()
    logger.info("Checklist item added: product_id=%s item_id=%s", product_id, item.id)
    return item


async def _get_checklist_item(
    db: AsyncSession, *, organization_id: uuid.UUID, product_id: uuid.UUID, item_id: uuid.UUID
) -> ChecklistItem:
    result = await db.execute(
        select(ChecklistItem).where(
            ChecklistItem.id == item_id,
            ChecklistItem.product_id == product_id,
            ChecklistItem.organization_id == organization_id,
            ChecklistItem.deleted_at.is_(None),
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise ChecklistItemNotFoundError
    return item


async def update_checklist_item(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    item_id: uuid.UUID,
    label: str,
) -> ChecklistItem:
    item = await _get_checklist_item(
        db, organization_id=organization_id, product_id=product_id, item_id=item_id
    )
    item.label = label
    await db.commit()
    return item


async def remove_checklist_item(
    db: AsyncSession, *, organization_id: uuid.UUID, product_id: uuid.UUID, item_id: uuid.UUID
) -> None:
    item = await _get_checklist_item(
        db, organization_id=organization_id, product_id=product_id, item_id=item_id
    )
    item.deleted_at = datetime.now(UTC)
    await db.commit()
    logger.info("Checklist item removed: product_id=%s item_id=%s", product_id, item_id)
