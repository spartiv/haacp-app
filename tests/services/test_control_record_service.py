import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ControlPeriod
from app.services import auth_service, control_checklist_service, control_record_service


async def _signup_owner(db_session: AsyncSession, **overrides: str) -> tuple[uuid.UUID, uuid.UUID]:
    defaults = {
        "email": f"owner-{uuid.uuid4().hex}@polton.ua",
        "password": "supersecret123",
        "full_name": "Olena Polishchuk",
        "organization_name": "Polton",
    }
    defaults.update(overrides)
    result = await auth_service.signup(db_session, **defaults)  # type: ignore[arg-type]
    assert result.organization_id is not None
    return result.organization_id, result.user.id


async def _make_checklist(
    db_session: AsyncSession, org_id: uuid.UUID, period: ControlPeriod, labels: list[str]
) -> list[uuid.UUID]:
    items = []
    for label in labels:
        item = await control_checklist_service.add_control_checklist_item(
            db_session, organization_id=org_id, period=period, label=label
        )
        items.append(item.id)
    return items


def test_current_period_date_for_daily_and_monthly() -> None:
    daily = control_record_service.current_period_date(ControlPeriod.DAILY, "Europe/Kyiv")
    monthly = control_record_service.current_period_date(ControlPeriod.MONTHLY, "Europe/Kyiv")

    assert isinstance(daily, date)
    assert monthly.day == 1


async def test_upsert_current_control_creates_new_record(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1", "Q2"])

    record = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True, item_ids[1]: True},
    )

    assert record.has_deviation is False
    assert record.period == ControlPeriod.DAILY


async def test_upsert_current_control_with_no_answer_flags_deviation(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1", "Q2"])

    record = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True, item_ids[1]: False},
    )

    assert record.has_deviation is True


async def test_upsert_current_control_twice_edits_the_same_record(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1"])

    first = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True},
    )
    second = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: False},
    )

    assert second.id == first.id
    assert second.has_deviation is True

    history = await control_record_service.get_control_record_history(
        db_session, organization_id=org_id, record_id=first.id
    )
    assert len(history) == 1
    assert history[0].snapshot["has_deviation"] is False


async def test_upsert_current_control_rejects_checklist_mismatch(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1", "Q2"])

    with pytest.raises(control_record_service.ChecklistMismatchError):
        await control_record_service.upsert_current_control(
            db_session,
            organization_id=org_id,
            period=ControlPeriod.DAILY,
            signatory_user_id=user_id,
            answers={item_ids[0]: True},
        )


async def test_upsert_current_control_backfills_an_explicit_past_date(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1"])
    yesterday = date.today() - timedelta(days=1)

    record = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True},
        period_date=yesterday,
    )

    assert record.period_date == yesterday

    today = await control_record_service.get_current_control(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY
    )
    assert today is None


async def test_upsert_current_control_rejects_future_date(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1"])
    tomorrow = date.today() + timedelta(days=1)

    with pytest.raises(control_record_service.FuturePeriodDateError):
        await control_record_service.upsert_current_control(
            db_session,
            organization_id=org_id,
            period=ControlPeriod.DAILY,
            signatory_user_id=user_id,
            answers={item_ids[0]: True},
            period_date=tomorrow,
        )


async def test_upsert_current_control_normalizes_monthly_date_to_first_of_month(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.MONTHLY, ["M1"])
    mid_month = date.today().replace(day=1) - timedelta(days=20)

    record = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.MONTHLY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True},
        period_date=mid_month,
    )

    assert record.period_date == mid_month.replace(day=1)


async def test_daily_and_monthly_records_are_independent(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    daily_items = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["D1"])
    monthly_items = await _make_checklist(db_session, org_id, ControlPeriod.MONTHLY, ["M1"])

    daily_record = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={daily_items[0]: True},
    )
    monthly_record = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.MONTHLY,
        signatory_user_id=user_id,
        answers={monthly_items[0]: True},
    )

    assert daily_record.id != monthly_record.id
    assert monthly_record.period_date.day == 1


async def test_get_current_control_returns_none_when_not_filled(db_session: AsyncSession) -> None:
    org_id, _ = await _signup_owner(db_session)

    current = await control_record_service.get_current_control(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY
    )

    assert current is None


async def test_soft_deleted_record_does_not_block_refilling_same_period(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1"])
    first = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True},
    )

    await control_record_service.soft_delete_control_record(
        db_session, organization_id=org_id, record_id=first.id
    )

    second = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True},
    )

    assert second.id != first.id


async def test_list_control_records_orders_newest_first_and_excludes_deleted(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1"])
    current = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True},
    )

    records = await control_record_service.list_control_records(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY
    )

    assert [r.id for r in records] == [current.id]

    await control_record_service.soft_delete_control_record(
        db_session, organization_id=org_id, record_id=current.id
    )
    records_after_delete = await control_record_service.list_control_records(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY
    )
    assert records_after_delete == []


async def test_get_control_record_not_found_for_other_org(db_session: AsyncSession) -> None:
    org_a, user_id = await _signup_owner(db_session)
    org_b, _ = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_a, ControlPeriod.DAILY, ["Q1"])
    record = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_a,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True},
    )

    with pytest.raises(control_record_service.ControlRecordNotFoundError):
        await control_record_service.get_control_record(
            db_session, organization_id=org_b, record_id=record.id
        )


async def test_edit_control_record_by_id_snapshots_history(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1"])
    record = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True},
    )

    edited = await control_record_service.edit_control_record(
        db_session,
        organization_id=org_id,
        record_id=record.id,
        edited_by_user_id=user_id,
        answers={item_ids[0]: False},
    )

    assert edited.has_deviation is True
    history = await control_record_service.get_control_record_history(
        db_session, organization_id=org_id, record_id=record.id
    )
    assert len(history) == 1


async def test_upsert_current_control_sets_note_on_create(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1"])

    record = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True},
        note="Fridge #2 ran warm this morning",
    )

    assert record.note == "Fridge #2 ran warm this morning"


async def test_upsert_current_control_note_follows_put_semantics(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1"])

    first = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True},
        note="initial note",
    )
    assert first.note == "initial note"

    second = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True},
    )

    assert second.id == first.id
    assert second.note is None

    history = await control_record_service.get_control_record_history(
        db_session, organization_id=org_id, record_id=first.id
    )
    assert history[0].snapshot["note"] == "initial note"


async def test_edit_control_record_note_follows_patch_semantics(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1"])
    record = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True},
        note="original",
    )

    unchanged = await control_record_service.edit_control_record(
        db_session,
        organization_id=org_id,
        record_id=record.id,
        edited_by_user_id=user_id,
        answers={item_ids[0]: False},
    )
    assert unchanged.note == "original"

    updated = await control_record_service.edit_control_record(
        db_session,
        organization_id=org_id,
        record_id=record.id,
        edited_by_user_id=user_id,
        answers={item_ids[0]: True},
        note="revised",
    )
    assert updated.note == "revised"


async def test_edit_control_record_rejects_checklist_mismatch(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item_ids = await _make_checklist(db_session, org_id, ControlPeriod.DAILY, ["Q1", "Q2"])
    record = await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item_ids[0]: True, item_ids[1]: True},
    )

    with pytest.raises(control_record_service.ChecklistMismatchError):
        await control_record_service.edit_control_record(
            db_session,
            organization_id=org_id,
            record_id=record.id,
            edited_by_user_id=user_id,
            answers={item_ids[0]: True},
        )
