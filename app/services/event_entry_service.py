import logging
import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import EventEntry, EventLogSchema, EventLogType

logger = logging.getLogger(__name__)

WATER_TEST_PARAMETERS = frozenset({"pH", "Хлор", "Мутність", "Мікробіологія", "Твердість"})
WATER_RESULTS = frozenset({"ok", "deviation"})
PEST_DETECTED_VALUES = frozenset({"yes", "no"})


class EventLogTypeNotFoundError(NotFoundError):
    code = "event_log_type_not_found"
    message = "Event log type not found"


class EventEntryNotFoundError(NotFoundError):
    code = "event_entry_not_found"
    message = "Event entry not found"


class InvalidEventPayloadError(Exception):
    pass


async def list_event_log_types(db: AsyncSession) -> list[EventLogType]:
    result = await db.execute(select(EventLogType).order_by(EventLogType.position))
    return list(result.scalars().all())


async def get_event_log_type(db: AsyncSession, *, event_log_type_id: uuid.UUID) -> EventLogType:
    log_type = await db.get(EventLogType, event_log_type_id)
    if log_type is None:
        raise EventLogTypeNotFoundError
    return log_type


def _normalize_payload(
    schema: EventLogSchema, payload: dict[str, Any]
) -> tuple[dict[str, Any], bool]:
    if schema == EventLogSchema.STANDARD:
        details = payload.get("details", "")
        if not isinstance(details, str):
            raise InvalidEventPayloadError
        return {"details": details}, False

    if schema == EventLogSchema.WATER:
        params = payload.get("params", [])
        result = payload.get("result", "ok")
        if not isinstance(params, list) or any(p not in WATER_TEST_PARAMETERS for p in params):
            raise InvalidEventPayloadError
        if result not in WATER_RESULTS:
            raise InvalidEventPayloadError
        return {"params": params, "result": result}, result == "deviation"

    if schema == EventLogSchema.PESTS:
        detected = payload.get("detected", "no")
        actions = payload.get("actions", "")
        if detected not in PEST_DETECTED_VALUES or not isinstance(actions, str):
            raise InvalidEventPayloadError
        return {"detected": detected, "actions": actions}, detected == "yes"

    raise InvalidEventPayloadError


async def record_event_entry(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    event_log_type_id: uuid.UUID,
    entry_date: date,
    responsible_user_id: uuid.UUID,
    payload: dict[str, Any],
) -> EventEntry:
    log_type = await get_event_log_type(db, event_log_type_id=event_log_type_id)
    normalized_payload, has_deviation = _normalize_payload(log_type.schema, payload)

    entry = EventEntry(
        organization_id=organization_id,
        event_log_type_id=event_log_type_id,
        entry_date=entry_date,
        responsible_user_id=responsible_user_id,
        payload=normalized_payload,
        has_deviation=has_deviation,
    )
    db.add(entry)
    await db.commit()
    logger.info(
        "Event entry recorded: entry_id=%s event_log_type_id=%s has_deviation=%s",
        entry.id,
        event_log_type_id,
        has_deviation,
    )
    return entry


async def list_event_entries(
    db: AsyncSession, *, organization_id: uuid.UUID, event_log_type_id: uuid.UUID
) -> list[EventEntry]:
    result = await db.execute(
        select(EventEntry)
        .where(
            EventEntry.organization_id == organization_id,
            EventEntry.event_log_type_id == event_log_type_id,
            EventEntry.deleted_at.is_(None),
        )
        .order_by(EventEntry.entry_date.desc())
    )
    return list(result.scalars().all())


async def get_event_entry(
    db: AsyncSession, *, organization_id: uuid.UUID, entry_id: uuid.UUID
) -> EventEntry:
    result = await db.execute(
        select(EventEntry).where(
            EventEntry.id == entry_id,
            EventEntry.organization_id == organization_id,
            EventEntry.deleted_at.is_(None),
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise EventEntryNotFoundError
    return entry


async def soft_delete_event_entry(
    db: AsyncSession, *, organization_id: uuid.UUID, entry_id: uuid.UUID
) -> None:
    entry = await get_event_entry(db, organization_id=organization_id, entry_id=entry_id)
    entry.deleted_at = datetime.now(UTC)
    await db.commit()
    logger.info("Event entry deleted: entry_id=%s organization_id=%s", entry_id, organization_id)
