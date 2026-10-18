import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError, NotFoundError
from app.models import ControlChecklistItem, ControlItemType, ControlPeriod

logger = logging.getLogger(__name__)


class ControlChecklistItemNotFoundError(NotFoundError):
    code = "control_checklist_item_not_found"
    message = "Control checklist item not found"


class InvalidChecklistItemConfigError(DomainError):
    status_code = 422
    code = "invalid_checklist_item_config"
    message = "Invalid checklist item configuration"


VALUE_STEP = Decimal("0.01")  # readings and limits are stored with 2 decimals


def quantize(value: Decimal | None) -> Decimal | None:
    return None if value is None else value.quantize(VALUE_STEP)


@dataclass(frozen=True)
class NumericConfig:
    """Unit and safe range of a numeric item. Either bound may be open."""

    unit: str | None
    min_value: Decimal | None
    max_value: Decimal | None


def _validated_config(item_type: ControlItemType, config: NumericConfig) -> NumericConfig:
    """Mirrors the table's check constraint, with readable errors."""
    if item_type == ControlItemType.BOOL:
        if config.unit is not None or config.min_value is not None or config.max_value is not None:
            raise InvalidChecklistItemConfigError(
                "Yes/No items have no unit or range", details=[{"field": "item_type"}]
            )
        return config

    unit = (config.unit or "").strip()
    if not unit:
        raise InvalidChecklistItemConfigError(
            "Numeric items need a unit (e.g. °C)", details=[{"field": "unit"}]
        )
    min_value, max_value = quantize(config.min_value), quantize(config.max_value)
    if min_value is None and max_value is None:
        raise InvalidChecklistItemConfigError(
            "Numeric items need a minimum, a maximum, or both", details=[{"field": "min_value"}]
        )
    if min_value is not None and max_value is not None and min_value > max_value:
        raise InvalidChecklistItemConfigError(
            "The minimum cannot be greater than the maximum", details=[{"field": "min_value"}]
        )
    return NumericConfig(unit=unit, min_value=min_value, max_value=max_value)


def is_within_range(
    value: Decimal, *, min_value: Decimal | None, max_value: Decimal | None
) -> bool:
    """Inclusive bounds: a reading exactly on a limit is within the safe range."""
    if min_value is not None and value < min_value:
        return False
    return not (max_value is not None and value > max_value)


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
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    period: ControlPeriod,
    label: str,
    item_type: ControlItemType = ControlItemType.BOOL,
    config: NumericConfig | None = None,
) -> ControlChecklistItem:
    resolved = _validated_config(item_type, config or NumericConfig(None, None, None))
    existing = await list_control_checklist_items(
        db, organization_id=organization_id, period=period
    )
    next_position = max((item.position for item in existing), default=-1) + 1

    item = ControlChecklistItem(
        organization_id=organization_id,
        period=period,
        label=label,
        position=next_position,
        item_type=item_type,
        unit=resolved.unit,
        min_value=resolved.min_value,
        max_value=resolved.max_value,
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


async def get_control_checklist_item(
    db: AsyncSession, *, organization_id: uuid.UUID, item_id: uuid.UUID
) -> ControlChecklistItem:
    return await _get_control_checklist_item(db, organization_id=organization_id, item_id=item_id)


async def update_control_checklist_item(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    item_id: uuid.UUID,
    label: str,
    config: NumericConfig | None = None,
) -> ControlChecklistItem:
    """Updates the label and (numeric items) the unit/range. The item type is
    fixed. `config` is the complete new state; None keeps the current one.
    Past answers keep the limits they were judged against."""
    item = await _get_control_checklist_item(db, organization_id=organization_id, item_id=item_id)
    if config is not None:
        resolved = _validated_config(item.item_type, config)
        item.unit = resolved.unit
        item.min_value = resolved.min_value
        item.max_value = resolved.max_value
    item.label = label
    await db.commit()
    logger.info("Control checklist item updated: item_id=%s", item_id)
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
