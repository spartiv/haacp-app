import logging
import uuid
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import (
    ControlAnswer,
    ControlPeriod,
    ControlRecord,
    ControlRecordHistory,
)
from app.services.checklist_validation import ChecklistMismatchError as ChecklistMismatchError
from app.services.checklist_validation import has_deviation as compute_has_deviation
from app.services.checklist_validation import validate_answer_ids
from app.services.control_checklist_service import list_control_checklist_items
from app.services.organization_service import get_organization_timezone

logger = logging.getLogger(__name__)


class ControlRecordNotFoundError(NotFoundError):
    code = "control_record_not_found"
    message = "Control record not found"


class FuturePeriodDateError(Exception):
    """Raised when a control record is submitted for a date/month that
    hasn't happened yet in the organization's own timezone."""


def normalize_period_date(period: ControlPeriod, requested_date: date) -> date:
    """Daily controls key off the exact day; monthly controls are stored
    under that month's first day regardless of which day within the month
    was requested."""
    if period == ControlPeriod.MONTHLY:
        return requested_date.replace(day=1)
    return requested_date


def current_period_date(period: ControlPeriod, org_timezone: str) -> date:
    """'Today' or 'this month' in the organization's own timezone, not the
    server's or the requesting device's — a facility-wide daily control has
    to key off the facility's calendar day."""
    now_local = datetime.now(UTC).astimezone(ZoneInfo(org_timezone))
    return normalize_period_date(period, now_local.date())


async def _validate_answers(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    period: ControlPeriod,
    answers: dict[uuid.UUID, bool],
) -> None:
    active_items = await list_control_checklist_items(
        db, organization_id=organization_id, period=period
    )
    validate_answer_ids(required_ids={item.id for item in active_items}, answers=answers)


async def list_control_answers(
    db: AsyncSession, *, control_record_id: uuid.UUID
) -> list[ControlAnswer]:
    result = await db.execute(
        select(ControlAnswer).where(ControlAnswer.control_record_id == control_record_id)
    )
    return list(result.scalars().all())


async def list_control_answers_by_record_ids(
    db: AsyncSession, *, control_record_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[ControlAnswer]]:
    """Single-query counterpart to list_control_answers for rendering a
    list of records, so callers don't issue one query per record."""
    if not control_record_ids:
        return {}
    result = await db.execute(
        select(ControlAnswer).where(ControlAnswer.control_record_id.in_(control_record_ids))
    )
    answers_by_record_id: dict[uuid.UUID, list[ControlAnswer]] = {
        record_id: [] for record_id in control_record_ids
    }
    for answer in result.scalars().all():
        answers_by_record_id[answer.control_record_id].append(answer)
    return answers_by_record_id


def _snapshot(record: ControlRecord, answers: list[ControlAnswer]) -> dict[str, Any]:
    return {
        "period_date": record.period_date.isoformat(),
        "has_deviation": record.has_deviation,
        "note": record.note,
        "answers": [
            {"control_checklist_item_id": str(a.control_checklist_item_id), "answer": a.answer}
            for a in answers
        ],
    }


async def _snapshot_and_replace_answers(
    db: AsyncSession,
    *,
    record: ControlRecord,
    edited_by_user_id: uuid.UUID,
    answers: dict[uuid.UUID, bool],
) -> None:
    current_answers = await list_control_answers(db, control_record_id=record.id)
    db.add(
        ControlRecordHistory(
            control_record_id=record.id,
            snapshot=_snapshot(record, current_answers),
            edited_by_user_id=edited_by_user_id,
        )
    )
    for existing_answer in current_answers:
        await db.delete(existing_answer)
    await db.flush()
    for item_id, answer in answers.items():
        db.add(
            ControlAnswer(
                control_record_id=record.id, control_checklist_item_id=item_id, answer=answer
            )
        )
    record.has_deviation = compute_has_deviation(answers)


async def _get_live_record(
    db: AsyncSession, *, organization_id: uuid.UUID, period: ControlPeriod, period_date: date
) -> ControlRecord | None:
    result = await db.execute(
        select(ControlRecord).where(
            ControlRecord.organization_id == organization_id,
            ControlRecord.period == period,
            ControlRecord.period_date == period_date,
            ControlRecord.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_current_control(
    db: AsyncSession, *, organization_id: uuid.UUID, period: ControlPeriod
) -> ControlRecord | None:
    org_timezone = await get_organization_timezone(db, organization_id)
    period_date = current_period_date(period, org_timezone)
    return await _get_live_record(
        db, organization_id=organization_id, period=period, period_date=period_date
    )


async def upsert_current_control(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    period: ControlPeriod,
    signatory_user_id: uuid.UUID,
    answers: dict[uuid.UUID, bool],
    period_date: date | None = None,
    note: str | None = None,
) -> ControlRecord:
    org_timezone = await get_organization_timezone(db, organization_id)
    today_period_date = current_period_date(period, org_timezone)
    resolved_period_date = (
        normalize_period_date(period, period_date) if period_date is not None else today_period_date
    )
    if resolved_period_date > today_period_date:
        raise FuturePeriodDateError
    await _validate_answers(db, organization_id=organization_id, period=period, answers=answers)

    existing = await _get_live_record(
        db, organization_id=organization_id, period=period, period_date=resolved_period_date
    )
    if existing is not None:
        await _snapshot_and_replace_answers(
            db, record=existing, edited_by_user_id=signatory_user_id, answers=answers
        )
        existing.signatory_user_id = signatory_user_id
        existing.note = note
        await db.commit()
        logger.info(
            "Control record updated: record_id=%s period=%s period_date=%s",
            existing.id,
            period.value,
            resolved_period_date,
        )
        return existing

    has_deviation = compute_has_deviation(answers)
    record = ControlRecord(
        organization_id=organization_id,
        period=period,
        period_date=resolved_period_date,
        signatory_user_id=signatory_user_id,
        has_deviation=has_deviation,
        note=note,
    )
    db.add(record)
    await db.flush()
    for item_id, answer in answers.items():
        db.add(
            ControlAnswer(
                control_record_id=record.id, control_checklist_item_id=item_id, answer=answer
            )
        )
    await db.commit()
    logger.info(
        "Control record created: record_id=%s period=%s period_date=%s",
        record.id,
        period.value,
        resolved_period_date,
    )
    return record


async def list_control_records(
    db: AsyncSession, *, organization_id: uuid.UUID, period: ControlPeriod
) -> list[ControlRecord]:
    result = await db.execute(
        select(ControlRecord)
        .where(
            ControlRecord.organization_id == organization_id,
            ControlRecord.period == period,
            ControlRecord.deleted_at.is_(None),
        )
        .order_by(ControlRecord.period_date.desc())
    )
    return list(result.scalars().all())


async def get_control_record(
    db: AsyncSession, *, organization_id: uuid.UUID, record_id: uuid.UUID
) -> ControlRecord:
    result = await db.execute(
        select(ControlRecord).where(
            ControlRecord.id == record_id,
            ControlRecord.organization_id == organization_id,
            ControlRecord.deleted_at.is_(None),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise ControlRecordNotFoundError
    return record


async def edit_control_record(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    record_id: uuid.UUID,
    edited_by_user_id: uuid.UUID,
    answers: dict[uuid.UUID, bool],
    note: str | None = None,
) -> ControlRecord:
    record = await get_control_record(db, organization_id=organization_id, record_id=record_id)
    await _validate_answers(
        db, organization_id=organization_id, period=record.period, answers=answers
    )
    await _snapshot_and_replace_answers(
        db, record=record, edited_by_user_id=edited_by_user_id, answers=answers
    )
    if note is not None:
        record.note = note
    await db.commit()
    logger.info(
        "Control record edited: record_id=%s organization_id=%s", record_id, organization_id
    )
    return record


async def soft_delete_control_record(
    db: AsyncSession, *, organization_id: uuid.UUID, record_id: uuid.UUID
) -> None:
    record = await get_control_record(db, organization_id=organization_id, record_id=record_id)
    record.deleted_at = datetime.now(UTC)
    await db.commit()
    logger.info(
        "Control record deleted: record_id=%s organization_id=%s", record_id, organization_id
    )


async def get_control_record_history(
    db: AsyncSession, *, organization_id: uuid.UUID, record_id: uuid.UUID
) -> list[ControlRecordHistory]:
    await get_control_record(db, organization_id=organization_id, record_id=record_id)
    result = await db.execute(
        select(ControlRecordHistory)
        .where(ControlRecordHistory.control_record_id == record_id)
        .order_by(ControlRecordHistory.created_at.desc())
    )
    return list(result.scalars().all())
