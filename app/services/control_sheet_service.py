"""Per-item control sheet workflow: check items one by one (draft), submit,
amend after submission with a reason. Every change is appended to the
immutable ControlAuditEvent log."""

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.errors import DomainError
from app.models import (
    ControlAnswer,
    ControlAuditEvent,
    ControlChecklistItem,
    ControlItemStatus,
    ControlItemType,
    ControlPeriod,
    ControlRecord,
    ControlRecordStatus,
    User,
)
from app.services import control_audit_service, control_record_service, organization_service
from app.services.control_checklist_service import (
    ControlChecklistItemNotFoundError,
    is_within_range,
    list_control_checklist_items,
    quantize,
)

logger = logging.getLogger(__name__)

MIN_CORRECTIVE_ACTION_LENGTH = 3
MIN_AMENDMENT_REASON_LENGTH = 3


class CorrectiveActionRequiredError(DomainError):
    status_code = 422
    code = "corrective_action_required"
    message = "Describe the corrective action taken for this deviation"


class AmendmentReasonRequiredError(DomainError):
    status_code = 422
    code = "amendment_reason_required"
    message = "This record is already submitted. Give a reason for the change"


class InvalidCheckStatusError(DomainError):
    status_code = 422
    code = "invalid_check_status"
    message = "An item can only be checked as pass or deviation"


class NumericValueRequiredError(DomainError):
    status_code = 422
    code = "numeric_value_required"
    message = "Enter the measured value for this item"


class NumericValueNotApplicableError(DomainError):
    status_code = 422
    code = "numeric_value_not_applicable"
    message = "This is a Yes/No item: send a status, not a value"


class ControlRecordAlreadySubmittedError(DomainError):
    status_code = 409
    code = "control_record_already_submitted"
    message = "This control record is already submitted"


class ControlRecordIncompleteError(DomainError):
    status_code = 409
    code = "control_record_incomplete"
    message = "Every item must be checked before submitting"


class InvalidCursorError(DomainError):
    status_code = 422
    code = "invalid_cursor"
    message = "Invalid pagination cursor"


@dataclass(frozen=True)
class UserRef:
    id: uuid.UUID
    full_name: str


@dataclass(frozen=True)
class SheetItem:
    item_id: uuid.UUID
    label: str
    position: int
    item_type: ControlItemType
    unit: str | None
    # Numeric items: the limits the current value was judged against (the
    # item's current limits until the first reading).
    min_value: Decimal | None
    max_value: Decimal | None
    value: Decimal | None
    status: ControlItemStatus
    corrective_action: str | None
    checked_by: UserRef | None  # the signed-in account that saved the check
    performed_by: UserRef | None  # who physically did it (shared devices)
    checked_at: datetime | None


@dataclass(frozen=True)
class ControlSheet:
    period: ControlPeriod
    period_date: date
    record: ControlRecord | None
    submitted_by: UserRef | None
    items: list[SheetItem]


@dataclass(frozen=True)
class AuditEventView:
    event: ControlAuditEvent
    actor: UserRef
    performed_by: UserRef
    item_label: str | None
    item_unit: str | None


@dataclass(frozen=True)
class AuditEventPage:
    events: list[AuditEventView]
    next_cursor: str | None


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


async def _load_user_refs(db: AsyncSession, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, UserRef]:
    if not user_ids:
        return {}
    result = await db.execute(select(User.id, User.full_name).where(User.id.in_(user_ids)))
    return {row.id: UserRef(id=row.id, full_name=row.full_name) for row in result}


async def _build_sheet(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    period: ControlPeriod,
    period_date: date,
    record: ControlRecord | None,
) -> ControlSheet:
    active_items = await list_control_checklist_items(
        db, organization_id=organization_id, period=period
    )
    answers = (
        await control_record_service.list_control_answers(db, control_record_id=record.id)
        if record is not None
        else []
    )
    answers_by_item = {a.control_checklist_item_id: a for a in answers}

    # Items removed from the checklist after being answered still belong on
    # this record's sheet, so include them (soft-deleted rows included).
    items_by_id = {item.id: item for item in active_items}
    removed_ids = set(answers_by_item) - set(items_by_id)
    if removed_ids:
        result = await db.execute(
            select(ControlChecklistItem).where(ControlChecklistItem.id.in_(removed_ids))
        )
        items_by_id.update({item.id: item for item in result.scalars().all()})

    user_ids = {a.checked_by_user_id for a in answers} | {
        a.performed_by_user_id for a in answers if a.performed_by_user_id is not None
    }
    if record is not None and record.submitted_by_user_id is not None:
        user_ids.add(record.submitted_by_user_id)
    users = await _load_user_refs(db, user_ids)

    items = []
    for item in sorted(items_by_id.values(), key=lambda i: (i.position, i.label)):
        answer = answers_by_item.get(item.id)
        judged = answer is not None and answer.numeric_value is not None
        items.append(
            SheetItem(
                item_id=item.id,
                label=item.label,
                position=item.position,
                item_type=item.item_type,
                unit=item.unit,
                min_value=answer.min_value if answer is not None and judged else item.min_value,
                max_value=answer.max_value if answer is not None and judged else item.max_value,
                value=answer.numeric_value if answer is not None else None,
                status=control_audit_service.answer_status(answer),
                corrective_action=answer.corrective_action if answer else None,
                checked_by=users.get(answer.checked_by_user_id) if answer else None,
                performed_by=(
                    users.get(answer.performed_by_user_id or answer.checked_by_user_id)
                    if answer
                    else None
                ),
                checked_at=answer.checked_at if answer else None,
            )
        )

    submitted_by = (
        users.get(record.submitted_by_user_id)
        if record is not None and record.submitted_by_user_id is not None
        else None
    )
    return ControlSheet(
        period=period,
        period_date=period_date,
        record=record,
        submitted_by=submitted_by,
        items=items,
    )


async def get_sheet(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    period: ControlPeriod,
    period_date: date | None,
) -> ControlSheet:
    """The sheet for a day/month. Never 404s: with no record yet, every
    active item is simply PENDING."""
    resolved = await control_record_service.resolve_period_date(
        db, organization_id=organization_id, period=period, requested_date=period_date
    )
    record = await control_record_service.get_live_record(
        db, organization_id=organization_id, period=period, period_date=resolved
    )
    return await _build_sheet(
        db, organization_id=organization_id, period=period, period_date=resolved, record=record
    )


async def _get_active_item(
    db: AsyncSession, *, organization_id: uuid.UUID, period: ControlPeriod, item_id: uuid.UUID
) -> ControlChecklistItem:
    result = await db.execute(
        select(ControlChecklistItem).where(
            ControlChecklistItem.id == item_id,
            ControlChecklistItem.organization_id == organization_id,
            ControlChecklistItem.period == period,
            ControlChecklistItem.deleted_at.is_(None),
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise ControlChecklistItemNotFoundError
    return item


async def _lock_or_create_record(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    period: ControlPeriod,
    period_date: date,
    actor_user_id: uuid.UUID,
) -> ControlRecord:
    """Returns the live record for the period, creating a draft if needed,
    with a row lock held until commit. INSERT ... ON CONFLICT DO NOTHING makes
    two simultaneous first checks safe: one creates, both then lock the same
    row, so each sees the other's change as its `previous_status`."""
    await db.execute(
        pg_insert(ControlRecord)
        .values(
            id=uuid.uuid4(),
            organization_id=organization_id,
            period=period,
            period_date=period_date,
            signatory_user_id=actor_user_id,
            has_deviation=False,
            status=ControlRecordStatus.DRAFT,
        )
        .on_conflict_do_nothing(
            index_elements=["organization_id", "period", "period_date"],
            index_where=ControlRecord.deleted_at.is_(None),
        )
    )
    result = await db.execute(
        select(ControlRecord)
        .where(
            ControlRecord.organization_id == organization_id,
            ControlRecord.period == period,
            ControlRecord.period_date == period_date,
            ControlRecord.deleted_at.is_(None),
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()


async def check_item(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    period: ControlPeriod,
    item_id: uuid.UUID,
    status: ControlItemStatus | None,
    corrective_action: str | None,
    amendment_reason: str | None,
    period_date: date | None,
    actor_user_id: uuid.UUID,
    value: Decimal | None = None,
    performed_by_user_id: uuid.UUID | None = None,
) -> ControlSheet:
    """Yes/No items take a `status`. Numeric items take a `value`; the server
    judges it against the item's range (any `status` sent is ignored)."""
    resolved = await control_record_service.resolve_period_date(
        db, organization_id=organization_id, period=period, requested_date=period_date
    )
    item = await _get_active_item(
        db, organization_id=organization_id, period=period, item_id=item_id
    )

    performer = await organization_service.resolve_performer(
        db,
        organization_id=organization_id,
        performer_user_id=performed_by_user_id,
        actor_user_id=actor_user_id,
    )

    reading = quantize(value)
    limits: tuple[Decimal | None, Decimal | None] = (None, None)
    if item.item_type == ControlItemType.NUMERIC:
        if reading is None:
            raise NumericValueRequiredError
        limits = (item.min_value, item.max_value)
        within = is_within_range(reading, min_value=limits[0], max_value=limits[1])
        status = ControlItemStatus.PASS if within else ControlItemStatus.DEVIATION
    else:
        if reading is not None:
            raise NumericValueNotApplicableError
        if status is None or status == ControlItemStatus.PENDING:
            raise InvalidCheckStatusError

    action = _clean_text(corrective_action) if status == ControlItemStatus.DEVIATION else None
    if status == ControlItemStatus.DEVIATION and (
        action is None or len(action) < MIN_CORRECTIVE_ACTION_LENGTH
    ):
        raise CorrectiveActionRequiredError

    record = await _lock_or_create_record(
        db,
        organization_id=organization_id,
        period=period,
        period_date=resolved,
        actor_user_id=actor_user_id,
    )
    reason = _clean_text(amendment_reason)
    if record.status == ControlRecordStatus.SUBMITTED and (
        reason is None or len(reason) < MIN_AMENDMENT_REASON_LENGTH
    ):
        raise AmendmentReasonRequiredError

    result = await db.execute(
        select(ControlAnswer).where(
            ControlAnswer.control_record_id == record.id,
            ControlAnswer.control_checklist_item_id == item_id,
        )
    )
    answer = result.scalar_one_or_none()
    previous_status = control_audit_service.answer_status(answer)

    if (
        answer is not None
        and previous_status == status
        and answer.corrective_action == action
        and answer.numeric_value == reading
        and (answer.min_value, answer.max_value) == limits
        and (answer.performed_by_user_id or answer.checked_by_user_id) == performer
    ):
        # Nothing changed: don't clutter the audit log.
        await db.commit()
        return await _build_sheet(
            db, organization_id=organization_id, period=period, period_date=resolved, record=record
        )

    now = datetime.now(UTC)
    if answer is None:
        db.add(
            ControlAnswer(
                control_record_id=record.id,
                control_checklist_item_id=item_id,
                answer=status == ControlItemStatus.PASS,
                numeric_value=reading,
                min_value=limits[0],
                max_value=limits[1],
                corrective_action=action,
                checked_by_user_id=actor_user_id,
                performed_by_user_id=performer,
                checked_at=now,
            )
        )
    else:
        answer.answer = status == ControlItemStatus.PASS
        answer.numeric_value = reading
        answer.min_value, answer.max_value = limits
        answer.corrective_action = action
        answer.checked_by_user_id = actor_user_id
        answer.performed_by_user_id = performer
        answer.checked_at = now

    await control_record_service.refresh_has_deviation(db, record=record)
    control_audit_service.append_item_event(
        db,
        record=record,
        actor_user_id=actor_user_id,
        item_id=item_id,
        previous_status=previous_status,
        new_status=status,
        corrective_action=action,
        amendment_reason=reason,
        numeric_value=reading,
        performed_by_user_id=performer,
    )
    await db.commit()
    logger.info(
        "Control item checked: record_id=%s item_id=%s %s->%s amended=%s",
        record.id,
        item_id,
        previous_status.value,
        status.value,
        record.status == ControlRecordStatus.SUBMITTED,
    )
    return await _build_sheet(
        db, organization_id=organization_id, period=period, period_date=resolved, record=record
    )


async def submit_record(
    db: AsyncSession, *, organization_id: uuid.UUID, record_id: uuid.UUID, actor_user_id: uuid.UUID
) -> ControlSheet:
    record = await control_record_service.get_control_record(
        db, organization_id=organization_id, record_id=record_id, for_update=True
    )
    if record.status == ControlRecordStatus.SUBMITTED:
        raise ControlRecordAlreadySubmittedError

    active_items = await list_control_checklist_items(
        db, organization_id=organization_id, period=record.period
    )
    answers = await control_record_service.list_control_answers(db, control_record_id=record.id)
    answered_ids = {a.control_checklist_item_id for a in answers}
    pending = [item for item in active_items if item.id not in answered_ids]
    if pending:
        raise ControlRecordIncompleteError(
            f"{len(pending)} item(s) still pending",
            details=[
                {"control_checklist_item_id": str(item.id), "label": item.label} for item in pending
            ],
        )

    control_audit_service.submit_record(db, record=record, actor_user_id=actor_user_id)
    await db.commit()
    logger.info("Control record submitted: record_id=%s", record.id)
    return await _build_sheet(
        db,
        organization_id=organization_id,
        period=record.period,
        period_date=record.period_date,
        record=record,
    )


def _parse_cursor(cursor: str | None) -> int | None:
    if cursor is None:
        return None
    if not cursor.isdigit():
        raise InvalidCursorError
    return int(cursor)


async def list_audit_events(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    record_id: uuid.UUID,
    cursor: str | None,
    limit: int,
) -> AuditEventPage:
    """Newest first. `cursor` is the `next_cursor` of the previous page."""
    await control_record_service.get_control_record(
        db, organization_id=organization_id, record_id=record_id
    )
    before_seq = _parse_cursor(cursor)

    performer = aliased(User)
    query = (
        select(
            ControlAuditEvent,
            User.full_name,
            performer.full_name,
            ControlChecklistItem.label,
            ControlChecklistItem.unit,
        )
        .join(User, User.id == ControlAuditEvent.actor_user_id)
        # Rows from before performers were recorded have none: fall back to the actor.
        .outerjoin(performer, performer.id == ControlAuditEvent.performed_by_user_id)
        .outerjoin(
            ControlChecklistItem,
            ControlChecklistItem.id == ControlAuditEvent.control_checklist_item_id,
        )
        .where(
            ControlAuditEvent.control_record_id == record_id,
            ControlAuditEvent.organization_id == organization_id,
        )
        .order_by(ControlAuditEvent.seq.desc())
        .limit(limit + 1)
    )
    if before_seq is not None:
        query = query.where(ControlAuditEvent.seq < before_seq)

    rows = (await db.execute(query)).all()
    has_more = len(rows) > limit
    page_rows = rows[:limit]
    events = [
        AuditEventView(
            event=audit_event,
            actor=UserRef(id=audit_event.actor_user_id, full_name=full_name),
            performed_by=(
                UserRef(id=audit_event.performed_by_user_id, full_name=performer_name)
                if audit_event.performed_by_user_id is not None and performer_name is not None
                else UserRef(id=audit_event.actor_user_id, full_name=full_name)
            ),
            item_label=label,
            item_unit=unit,
        )
        for audit_event, full_name, performer_name, label, unit in page_rows
    ]
    next_cursor = str(events[-1].event.seq) if has_more and events else None
    return AuditEventPage(events=events, next_cursor=next_cursor)
