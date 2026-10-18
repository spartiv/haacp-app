import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import delete, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ControlAuditEvent,
    ControlAuditEventType,
    ControlItemStatus,
    ControlPeriod,
    ControlRecordStatus,
)
from app.services import (
    auth_service,
    control_checklist_service,
    control_record_service,
    control_sheet_service,
)
from app.services.control_checklist_service import ControlChecklistItemNotFoundError
from app.services.control_record_service import LEGACY_AMENDMENT_REASON, FuturePeriodDateError
from app.services.control_sheet_service import (
    AmendmentReasonRequiredError,
    ControlRecordAlreadySubmittedError,
    ControlRecordIncompleteError,
    ControlSheet,
    CorrectiveActionRequiredError,
    InvalidCheckStatusError,
    InvalidCursorError,
)

PASS = ControlItemStatus.PASS
DEVIATION = ControlItemStatus.DEVIATION
PENDING = ControlItemStatus.PENDING


async def _signup_owner(db_session: AsyncSession) -> tuple[uuid.UUID, uuid.UUID]:
    result = await auth_service.signup(
        db_session,
        email=f"owner-{uuid.uuid4().hex}@polton.ua",
        password="supersecret123",
        full_name="Olena Polishchuk",
        organization_name="Polton",
    )
    assert result.organization_id is not None
    return result.organization_id, result.user.id


async def _make_checklist(
    db_session: AsyncSession, org_id: uuid.UUID, labels: list[str]
) -> list[uuid.UUID]:
    ids = []
    for label in labels:
        item = await control_checklist_service.add_control_checklist_item(
            db_session, organization_id=org_id, period=ControlPeriod.DAILY, label=label
        )
        ids.append(item.id)
    return ids


async def _check(
    db_session: AsyncSession,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    item_id: uuid.UUID,
    status: ControlItemStatus,
    *,
    corrective_action: str | None = None,
    amendment_reason: str | None = None,
    period_date: date | None = None,
) -> ControlSheet:
    return await control_sheet_service.check_item(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        item_id=item_id,
        status=status,
        corrective_action=corrective_action,
        amendment_reason=amendment_reason,
        period_date=period_date,
        actor_user_id=user_id,
    )


async def _events(
    db_session: AsyncSession, org_id: uuid.UUID, record_id: uuid.UUID
) -> list[ControlAuditEvent]:
    page = await control_sheet_service.list_audit_events(
        db_session, organization_id=org_id, record_id=record_id, cursor=None, limit=200
    )
    return [view.event for view in reversed(page.events)]  # oldest first


def _status_by_item(sheet: ControlSheet) -> dict[uuid.UUID, ControlItemStatus]:
    return {item.item_id: item.status for item in sheet.items}


# ---- Reading the sheet ----


async def test_sheet_without_record_lists_every_item_as_pending(db_session: AsyncSession) -> None:
    org_id, _ = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ["Q1", "Q2"])

    sheet = await control_sheet_service.get_sheet(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY, period_date=None
    )

    assert sheet.record is None
    assert [item.item_id for item in sheet.items] == item_ids
    assert {item.status for item in sheet.items} == {PENDING}


async def test_sheet_rejects_future_date(db_session: AsyncSession) -> None:
    org_id, _ = await _signup_owner(db_session)

    with pytest.raises(FuturePeriodDateError):
        await control_sheet_service.get_sheet(
            db_session,
            organization_id=org_id,
            period=ControlPeriod.DAILY,
            period_date=date.today() + timedelta(days=2),
        )


# ---- Checking items ----


async def test_first_check_creates_draft_and_logs_event(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    q1, q2 = await _make_checklist(db_session, org_id, ["Q1", "Q2"])

    sheet = await _check(db_session, org_id, user_id, q1, PASS)

    assert sheet.record is not None
    assert sheet.record.status == ControlRecordStatus.DRAFT
    assert _status_by_item(sheet) == {q1: PASS, q2: PENDING}
    checked = sheet.items[0]
    assert checked.checked_by is not None and checked.checked_by.full_name == "Olena Polishchuk"
    assert checked.checked_at is not None

    [audit_event] = await _events(db_session, org_id, sheet.record.id)
    assert audit_event.event_type == ControlAuditEventType.ITEM_CHECKED
    assert audit_event.previous_status == PENDING
    assert audit_event.new_status == PASS
    assert audit_event.actor_user_id == user_id
    assert audit_event.created_at is not None


@pytest.mark.parametrize("corrective_action", [None, "", "   ", "ok"])
async def test_deviation_requires_corrective_action(
    db_session: AsyncSession, corrective_action: str | None
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    [q1] = await _make_checklist(db_session, org_id, ["Q1"])

    with pytest.raises(CorrectiveActionRequiredError):
        await _check(
            db_session, org_id, user_id, q1, DEVIATION, corrective_action=corrective_action
        )


async def test_pending_is_not_a_valid_check(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    [q1] = await _make_checklist(db_session, org_id, ["Q1"])

    with pytest.raises(InvalidCheckStatusError):
        await _check(db_session, org_id, user_id, q1, PENDING)


async def test_deviation_then_pass_updates_state_and_logs_both(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    [q1] = await _make_checklist(db_session, org_id, ["Q1"])

    deviated = await _check(
        db_session, org_id, user_id, q1, DEVIATION, corrective_action="  Moved stock to FRG-04  "
    )
    assert deviated.record is not None and deviated.record.has_deviation is True
    assert deviated.items[0].corrective_action == "Moved stock to FRG-04"

    passed = await _check(db_session, org_id, user_id, q1, PASS, corrective_action="ignored")
    assert passed.record is not None and passed.record.has_deviation is False
    assert passed.items[0].corrective_action is None

    events = await _events(db_session, org_id, passed.record.id)
    assert [(e.previous_status, e.new_status) for e in events] == [
        (PENDING, DEVIATION),
        (DEVIATION, PASS),
    ]
    assert events[0].corrective_action == "Moved stock to FRG-04"


async def test_repeating_the_same_check_does_not_log_again(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    [q1] = await _make_checklist(db_session, org_id, ["Q1"])

    sheet = await _check(db_session, org_id, user_id, q1, DEVIATION, corrective_action="Fixed")
    await _check(db_session, org_id, user_id, q1, DEVIATION, corrective_action="Fixed")
    await _check(db_session, org_id, user_id, q1, DEVIATION, corrective_action="Fixed again")

    assert sheet.record is not None
    events = await _events(db_session, org_id, sheet.record.id)
    assert [e.corrective_action for e in events] == ["Fixed", "Fixed again"]


async def test_check_rejects_unknown_item_and_item_from_other_period(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    monthly = await control_checklist_service.add_control_checklist_item(
        db_session, organization_id=org_id, period=ControlPeriod.MONTHLY, label="Monthly"
    )

    with pytest.raises(ControlChecklistItemNotFoundError):
        await _check(db_session, org_id, user_id, uuid.uuid4(), PASS)
    with pytest.raises(ControlChecklistItemNotFoundError):
        await _check(db_session, org_id, user_id, monthly.id, PASS)


async def test_check_can_backfill_a_past_day(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    [q1] = await _make_checklist(db_session, org_id, ["Q1"])
    past = date.today() - timedelta(days=5)

    sheet = await _check(db_session, org_id, user_id, q1, PASS, period_date=past)

    assert sheet.period_date == past
    assert sheet.record is not None and sheet.record.period_date == past


# ---- Submitting ----


async def test_submit_requires_every_item_checked(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    q1, q2 = await _make_checklist(db_session, org_id, ["Q1", "Q2"])
    sheet = await _check(db_session, org_id, user_id, q1, PASS)
    assert sheet.record is not None

    with pytest.raises(ControlRecordIncompleteError) as exc_info:
        await control_sheet_service.submit_record(
            db_session, organization_id=org_id, record_id=sheet.record.id, actor_user_id=user_id
        )

    assert exc_info.value.details == [{"control_checklist_item_id": str(q2), "label": "Q2"}]


async def test_submit_finalizes_record_once(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    [q1] = await _make_checklist(db_session, org_id, ["Q1"])
    draft = await _check(db_session, org_id, user_id, q1, PASS)
    assert draft.record is not None

    submitted = await control_sheet_service.submit_record(
        db_session, organization_id=org_id, record_id=draft.record.id, actor_user_id=user_id
    )

    assert submitted.record is not None
    assert submitted.record.status == ControlRecordStatus.SUBMITTED
    assert submitted.submitted_by is not None and submitted.submitted_by.id == user_id
    events = await _events(db_session, org_id, draft.record.id)
    assert events[-1].event_type == ControlAuditEventType.RECORD_SUBMITTED
    assert events[-1].control_checklist_item_id is None

    with pytest.raises(ControlRecordAlreadySubmittedError):
        await control_sheet_service.submit_record(
            db_session, organization_id=org_id, record_id=draft.record.id, actor_user_id=user_id
        )


# ---- Amending after submission ----


async def test_change_after_submit_requires_reason_and_logs_amendment(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    [q1] = await _make_checklist(db_session, org_id, ["Q1"])
    draft = await _check(db_session, org_id, user_id, q1, PASS)
    assert draft.record is not None
    await control_sheet_service.submit_record(
        db_session, organization_id=org_id, record_id=draft.record.id, actor_user_id=user_id
    )

    with pytest.raises(AmendmentReasonRequiredError):
        await _check(db_session, org_id, user_id, q1, DEVIATION, corrective_action="Re-chilled")

    amended = await _check(
        db_session,
        org_id,
        user_id,
        q1,
        DEVIATION,
        corrective_action="Re-chilled",
        amendment_reason="Wrong reading entered at 08:00",
    )

    assert amended.record is not None
    assert amended.record.status == ControlRecordStatus.SUBMITTED
    assert amended.record.has_deviation is True
    last = (await _events(db_session, org_id, draft.record.id))[-1]
    assert last.event_type == ControlAuditEventType.ITEM_AMENDED
    assert (last.previous_status, last.new_status) == (PASS, DEVIATION)
    assert last.amendment_reason == "Wrong reading entered at 08:00"


async def test_amendment_reason_is_not_stored_for_draft_checks(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    [q1] = await _make_checklist(db_session, org_id, ["Q1"])

    sheet = await _check(db_session, org_id, user_id, q1, PASS, amendment_reason="not needed")

    assert sheet.record is not None
    [audit_event] = await _events(db_session, org_id, sheet.record.id)
    assert audit_event.amendment_reason is None


# ---- Audit log ----


async def test_audit_events_paginate_newest_first(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    q1, q2, q3 = await _make_checklist(db_session, org_id, ["Q1", "Q2", "Q3"])
    for item_id in (q1, q2, q3):
        sheet = await _check(db_session, org_id, user_id, item_id, PASS)
    assert sheet.record is not None

    first = await control_sheet_service.list_audit_events(
        db_session, organization_id=org_id, record_id=sheet.record.id, cursor=None, limit=2
    )
    assert [v.item_label for v in first.events] == ["Q3", "Q2"]
    assert first.next_cursor is not None

    second = await control_sheet_service.list_audit_events(
        db_session,
        organization_id=org_id,
        record_id=sheet.record.id,
        cursor=first.next_cursor,
        limit=2,
    )
    assert [v.item_label for v in second.events] == ["Q1"]
    assert second.next_cursor is None
    assert second.events[0].actor.full_name == "Olena Polishchuk"


async def test_audit_events_reject_malformed_cursor(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    [q1] = await _make_checklist(db_session, org_id, ["Q1"])
    sheet = await _check(db_session, org_id, user_id, q1, PASS)
    assert sheet.record is not None

    with pytest.raises(InvalidCursorError):
        await control_sheet_service.list_audit_events(
            db_session, organization_id=org_id, record_id=sheet.record.id, cursor="abc", limit=10
        )


async def test_audit_events_cannot_be_updated_or_deleted(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    [q1] = await _make_checklist(db_session, org_id, ["Q1"])
    sheet = await _check(db_session, org_id, user_id, q1, PASS)
    assert sheet.record is not None
    record_id = sheet.record.id

    for statement in (
        update(ControlAuditEvent)
        .where(ControlAuditEvent.control_record_id == record_id)
        .values(corrective_action="tampered"),
        delete(ControlAuditEvent).where(ControlAuditEvent.control_record_id == record_id),
        text("TRUNCATE control_audit_events"),
    ):
        with pytest.raises(DBAPIError, match="append-only"):
            async with db_session.begin_nested():
                await db_session.execute(statement)

    assert len(await _events(db_session, org_id, record_id)) == 1


# ---- Legacy full-sheet endpoint compatibility ----


async def test_legacy_upsert_logs_every_item_and_submission(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    q1, q2 = await _make_checklist(db_session, org_id, ["Q1", "Q2"])

    record = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={q1: True, q2: False},
    )

    events = await _events(db_session, org_id, record.id)
    assert [(e.event_type, e.new_status) for e in events] == [
        (ControlAuditEventType.ITEM_CHECKED, PASS),
        (ControlAuditEventType.ITEM_CHECKED, DEVIATION),
        (ControlAuditEventType.RECORD_SUBMITTED, None),
    ]


async def test_legacy_edit_after_submit_logs_amendment_and_keeps_unchanged_notes(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    q1, q2 = await _make_checklist(db_session, org_id, ["Q1", "Q2"])
    await _check(db_session, org_id, user_id, q1, DEVIATION, corrective_action="Door seal fixed")
    sheet = await _check(db_session, org_id, user_id, q2, PASS)
    assert sheet.record is not None
    await control_sheet_service.submit_record(
        db_session, organization_id=org_id, record_id=sheet.record.id, actor_user_id=user_id
    )

    # Mobile app re-sends the whole sheet with q2 flipped; q1 is unchanged.
    await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={q1: False, q2: False},
    )

    after = await control_sheet_service.get_sheet(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY, period_date=None
    )
    by_item = {item.item_id: item for item in after.items}
    assert by_item[q1].corrective_action == "Door seal fixed"
    assert by_item[q2].status == DEVIATION
    last = (await _events(db_session, org_id, sheet.record.id))[-1]
    assert last.event_type == ControlAuditEventType.ITEM_AMENDED
    assert last.amendment_reason == LEGACY_AMENDMENT_REASON


async def test_sheet_keeps_answered_items_removed_from_checklist(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    q1, q2 = await _make_checklist(db_session, org_id, ["Q1", "Q2"])
    await _check(db_session, org_id, user_id, q1, PASS)
    await control_checklist_service.remove_control_checklist_item(
        db_session, organization_id=org_id, item_id=q1
    )

    sheet = await control_sheet_service.get_sheet(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY, period_date=None
    )

    assert _status_by_item(sheet) == {q1: PASS, q2: PENDING}
