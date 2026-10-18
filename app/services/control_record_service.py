import logging
import uuid
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError, NotFoundError
from app.models import (
    ControlAnswer,
    ControlItemStatus,
    ControlItemType,
    ControlPeriod,
    ControlRecord,
    ControlRecordHistory,
    ControlRecordStatus,
)
from app.services import control_audit_service
from app.services.checklist_validation import ChecklistMismatchError as ChecklistMismatchError
from app.services.checklist_validation import validate_answer_ids
from app.services.control_checklist_service import list_control_checklist_items
from app.services.organization_service import get_organization_timezone

logger = logging.getLogger(__name__)

# The legacy full-sheet endpoints (PUT .../current, PATCH .../control-records/{id})
# can't send a per-item reason, so post-submit changes made through them are
# logged with this fixed reason instead.
LEGACY_AMENDMENT_REASON = "Changed via full-sheet endpoint (legacy client, no reason given)"


class NumericItemsNotSupportedError(DomainError):
    status_code = 422
    code = "numeric_items_not_supported"
    message = (
        "This checklist has measured items (e.g. temperatures). Fill it item by item "
        "via POST /controls/{period}/items/{item_id}/check"
    )


class ControlRecordNotFoundError(NotFoundError):
    code = "control_record_not_found"
    message = "Control record not found"


class FuturePeriodDateError(DomainError):
    """Raised when a control record is submitted for a date/month that
    hasn't happened yet in the organization's own timezone."""

    status_code = 422
    code = "future_period_date"
    message = "Cannot record a control for a future date"


class ControlRecordSubmittedError(DomainError):
    status_code = 409
    code = "control_record_submitted"
    message = "Submitted control records cannot be deleted"


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


async def resolve_period_date(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    period: ControlPeriod,
    requested_date: date | None,
) -> date:
    """The requested day/month (default: current one in the org's timezone),
    normalized for the period. Future periods are rejected."""
    org_timezone = await get_organization_timezone(db, organization_id)
    today_period_date = current_period_date(period, org_timezone)
    if requested_date is None:
        return today_period_date
    resolved = normalize_period_date(period, requested_date)
    if resolved > today_period_date:
        raise FuturePeriodDateError
    return resolved


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
    # The full-sheet format only carries Yes/No answers. Recording "OK" for a
    # temperature without the reading would defeat the point, so refuse.
    if any(item.item_type == ControlItemType.NUMERIC for item in active_items):
        raise NumericItemsNotSupportedError
    validate_answer_ids(
        required_ids={item.id for item in active_items},
        answers=answers,
        resource_label="organization's",
    )


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


async def refresh_has_deviation(db: AsyncSession, *, record: ControlRecord) -> None:
    """has_deviation = any answer on the record is a deviation."""
    await db.flush()
    result = await db.execute(
        select(
            exists().where(
                ControlAnswer.control_record_id == record.id,
                ControlAnswer.answer.is_(False),
            )
        )
    )
    record.has_deviation = bool(result.scalar_one())


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


async def _apply_full_sheet_answers(
    db: AsyncSession,
    *,
    record: ControlRecord,
    actor_user_id: uuid.UUID,
    answers: dict[uuid.UUID, bool],
    snapshot_first: bool,
) -> None:
    """Legacy full-sheet write: sets every item at once, then auto-submits.

    Answers are updated in place (not deleted and re-created) so that
    unchanged items keep their corrective action and who/when checked them.
    Each actual change is appended to the audit log. Corrective actions are
    not required here (backward compatibility with the mobile app)."""
    current_answers = await list_control_answers(db, control_record_id=record.id)
    if snapshot_first:
        db.add(
            ControlRecordHistory(
                control_record_id=record.id,
                snapshot=_snapshot(record, current_answers),
                edited_by_user_id=actor_user_id,
            )
        )

    current_by_item = {a.control_checklist_item_id: a for a in current_answers}
    now = datetime.now(UTC)
    for item_id, value in answers.items():
        existing = current_by_item.get(item_id)
        previous_status = control_audit_service.answer_status(existing)
        new_status = ControlItemStatus.PASS if value else ControlItemStatus.DEVIATION
        if previous_status == new_status:
            continue
        if existing is None:
            db.add(
                ControlAnswer(
                    control_record_id=record.id,
                    control_checklist_item_id=item_id,
                    answer=value,
                    checked_by_user_id=actor_user_id,
                    performed_by_user_id=actor_user_id,
                    checked_at=now,
                )
            )
        else:
            existing.answer = value
            existing.corrective_action = None
            existing.checked_by_user_id = actor_user_id
            existing.performed_by_user_id = actor_user_id
            existing.checked_at = now
        control_audit_service.append_item_event(
            db,
            record=record,
            actor_user_id=actor_user_id,
            item_id=item_id,
            previous_status=previous_status,
            new_status=new_status,
            corrective_action=None,
            amendment_reason=LEGACY_AMENDMENT_REASON,
        )

    await refresh_has_deviation(db, record=record)
    if record.status == ControlRecordStatus.DRAFT:
        control_audit_service.submit_record(db, record=record, actor_user_id=actor_user_id)


async def get_live_record(
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
    period_date = await resolve_period_date(
        db, organization_id=organization_id, period=period, requested_date=None
    )
    return await get_live_record(
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
    resolved_period_date = await resolve_period_date(
        db, organization_id=organization_id, period=period, requested_date=period_date
    )
    await _validate_answers(db, organization_id=organization_id, period=period, answers=answers)

    existing = await get_live_record(
        db, organization_id=organization_id, period=period, period_date=resolved_period_date
    )
    if existing is not None:
        await _apply_full_sheet_answers(
            db,
            record=existing,
            actor_user_id=signatory_user_id,
            answers=answers,
            snapshot_first=True,
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

    record = ControlRecord(
        organization_id=organization_id,
        period=period,
        period_date=resolved_period_date,
        signatory_user_id=signatory_user_id,
        has_deviation=False,
        status=ControlRecordStatus.DRAFT,
        note=note,
    )
    db.add(record)
    await db.flush()
    await _apply_full_sheet_answers(
        db, record=record, actor_user_id=signatory_user_id, answers=answers, snapshot_first=False
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
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    record_id: uuid.UUID,
    for_update: bool = False,
) -> ControlRecord:
    query = select(ControlRecord).where(
        ControlRecord.id == record_id,
        ControlRecord.organization_id == organization_id,
        ControlRecord.deleted_at.is_(None),
    )
    if for_update:
        query = query.with_for_update().execution_options(populate_existing=True)
    result = await db.execute(query)
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
    await _apply_full_sheet_answers(
        db, record=record, actor_user_id=edited_by_user_id, answers=answers, snapshot_first=True
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
    """Only drafts can be deleted; submitted records are part of the
    compliance trail and can only be amended."""
    record = await get_control_record(db, organization_id=organization_id, record_id=record_id)
    if record.status == ControlRecordStatus.SUBMITTED:
        raise ControlRecordSubmittedError
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
