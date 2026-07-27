import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import ControlChecklistItem, ControlPeriod

logger = logging.getLogger(__name__)


class ControlChecklistItemNotFoundError(NotFoundError):
    code = "control_checklist_item_not_found"
    message = "Control checklist item not found"


async def list_control_checklist_items(
    db: AsyncSession, *, organization_id: uuid.UUID, period: ControlPeriod
) -> list[ControlChecklistItem]:
    result = await db.execute(
        select(ControlChecklistItem)
        .where(
            ControlChecklistItem.organization_id == organization_id,
            ControlChecklistItem.period == period,
            ControlChecklistItem.deleted_at.is_(None),
        )
        .order_by(ControlChecklistItem.position)
    )
    return list(result.scalars().all())


async def add_control_checklist_item(
    db: AsyncSession, *, organization_id: uuid.UUID, period: ControlPeriod, label: str
) -> ControlChecklistItem:
    existing = await list_control_checklist_items(
        db, organization_id=organization_id, period=period
    )
    next_position = max((item.position for item in existing), default=-1) + 1

    item = ControlChecklistItem(
        organization_id=organization_id, period=period, label=label, position=next_position
    )
    db.add(item)
    await db.commit()
    logger.info(
        "Control checklist item added: item_id=%s organization_id=%s period=%s",
        item.id,
        organization_id,
        period.value,
    )
    return item


async def _get_control_checklist_item(
    db: AsyncSession, *, organization_id: uuid.UUID, item_id: uuid.UUID
) -> ControlChecklistItem:
    result = await db.execute(
        select(ControlChecklistItem).where(
            ControlChecklistItem.id == item_id,
            ControlChecklistItem.organization_id == organization_id,
            ControlChecklistItem.deleted_at.is_(None),
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise ControlChecklistItemNotFoundError
    return item


async def update_control_checklist_item(
    db: AsyncSession, *, organization_id: uuid.UUID, item_id: uuid.UUID, label: str
) -> ControlChecklistItem:
    item = await _get_control_checklist_item(db, organization_id=organization_id, item_id=item_id)
    item.label = label
    await db.commit()
    return item


async def remove_control_checklist_item(
    db: AsyncSession, *, organization_id: uuid.UUID, item_id: uuid.UUID
) -> None:
    item = await _get_control_checklist_item(db, organization_id=organization_id, item_id=item_id)
    item.deleted_at = datetime.now(UTC)
    await db.commit()
    logger.info(
        "Control checklist item removed: item_id=%s organization_id=%s", item_id, organization_id
    )
