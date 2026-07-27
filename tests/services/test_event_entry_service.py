import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EventLogSchema
from app.services import auth_service, event_entry_service


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


async def _log_type_id(db_session: AsyncSession, key: str) -> uuid.UUID:
    log_types = await event_entry_service.list_event_log_types(db_session)
    return next(t.id for t in log_types if t.key == key)


async def test_list_event_log_types_returns_all_9_ordered_by_position(
    db_session: AsyncSession,
) -> None:
    log_types = await event_entry_service.list_event_log_types(db_session)

    assert len(log_types) == 9
    positions = [t.position for t in log_types]
    assert positions == sorted(positions)
    assert log_types[0].key == "glass"
    assert log_types[1].schema == EventLogSchema.WATER


async def test_record_standard_entry_never_has_deviation(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    log_type_id = await _log_type_id(db_session, "eq")

    entry = await event_entry_service.record_event_entry(
        db_session,
        organization_id=org_id,
        event_log_type_id=log_type_id,
        entry_date=date(2026, 7, 10),
        responsible_user_id=user_id,
        payload={"details": "Планове ТО фасувального автомата"},
    )

    assert entry.has_deviation is False
    assert entry.payload == {"details": "Планове ТО фасувального автомата"}


async def test_record_standard_entry_rejects_non_string_details(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    log_type_id = await _log_type_id(db_session, "eq")

    with pytest.raises(event_entry_service.InvalidEventPayloadError):
        await event_entry_service.record_event_entry(
            db_session,
            organization_id=org_id,
            event_log_type_id=log_type_id,
            entry_date=date(2026, 7, 10),
            responsible_user_id=user_id,
            payload={"details": 12345},
        )


async def test_record_water_entry_deviation_follows_result(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    log_type_id = await _log_type_id(db_session, "water")

    ok_entry = await event_entry_service.record_event_entry(
        db_session,
        organization_id=org_id,
        event_log_type_id=log_type_id,
        entry_date=date(2026, 7, 5),
        responsible_user_id=user_id,
        payload={"params": ["pH", "Мікробіологія"], "result": "ok"},
    )
    assert ok_entry.has_deviation is False

    deviation_entry = await event_entry_service.record_event_entry(
        db_session,
        organization_id=org_id,
        event_log_type_id=log_type_id,
        entry_date=date(2026, 7, 6),
        responsible_user_id=user_id,
        payload={"params": ["Хлор"], "result": "deviation"},
    )
    assert deviation_entry.has_deviation is True


async def test_record_water_entry_rejects_unknown_parameter(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    log_type_id = await _log_type_id(db_session, "water")

    with pytest.raises(event_entry_service.InvalidEventPayloadError):
        await event_entry_service.record_event_entry(
            db_session,
            organization_id=org_id,
            event_log_type_id=log_type_id,
            entry_date=date(2026, 7, 5),
            responsible_user_id=user_id,
            payload={"params": ["Радіоактивність"], "result": "ok"},
        )


async def test_record_water_entry_rejects_invalid_result(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    log_type_id = await _log_type_id(db_session, "water")

    with pytest.raises(event_entry_service.InvalidEventPayloadError):
        await event_entry_service.record_event_entry(
            db_session,
            organization_id=org_id,
            event_log_type_id=log_type_id,
            entry_date=date(2026, 7, 5),
            responsible_user_id=user_id,
            payload={"params": [], "result": "maybe"},
        )


async def test_record_pests_entry_deviation_follows_detected(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    log_type_id = await _log_type_id(db_session, "pests")

    clean_entry = await event_entry_service.record_event_entry(
        db_session,
        organization_id=org_id,
        event_log_type_id=log_type_id,
        entry_date=date(2026, 7, 8),
        responsible_user_id=user_id,
        payload={"detected": "no", "actions": ""},
    )
    assert clean_entry.has_deviation is False

    infested_entry = await event_entry_service.record_event_entry(
        db_session,
        organization_id=org_id,
        event_log_type_id=log_type_id,
        entry_date=date(2026, 6, 20),
        responsible_user_id=user_id,
        payload={"detected": "yes", "actions": "Викликано службу дератизації"},
    )
    assert infested_entry.has_deviation is True


async def test_record_pests_entry_rejects_invalid_detected_value(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    log_type_id = await _log_type_id(db_session, "pests")

    with pytest.raises(event_entry_service.InvalidEventPayloadError):
        await event_entry_service.record_event_entry(
            db_session,
            organization_id=org_id,
            event_log_type_id=log_type_id,
            entry_date=date(2026, 7, 8),
            responsible_user_id=user_id,
            payload={"detected": "maybe", "actions": ""},
        )


async def test_record_entry_rejects_unknown_log_type(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)

    with pytest.raises(event_entry_service.EventLogTypeNotFoundError):
        await event_entry_service.record_event_entry(
            db_session,
            organization_id=org_id,
            event_log_type_id=uuid.uuid4(),
            entry_date=date(2026, 7, 8),
            responsible_user_id=user_id,
            payload={},
        )


async def test_list_event_entries_orders_newest_first_and_excludes_deleted(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    log_type_id = await _log_type_id(db_session, "glass")
    older = await event_entry_service.record_event_entry(
        db_session,
        organization_id=org_id,
        event_log_type_id=log_type_id,
        entry_date=date(2026, 6, 1),
        responsible_user_id=user_id,
        payload={"details": "Old"},
    )
    newer = await event_entry_service.record_event_entry(
        db_session,
        organization_id=org_id,
        event_log_type_id=log_type_id,
        entry_date=date(2026, 6, 28),
        responsible_user_id=user_id,
        payload={"details": "New"},
    )
    removed = await event_entry_service.record_event_entry(
        db_session,
        organization_id=org_id,
        event_log_type_id=log_type_id,
        entry_date=date(2026, 7, 1),
        responsible_user_id=user_id,
        payload={"details": "Removed"},
    )
    await event_entry_service.soft_delete_event_entry(
        db_session, organization_id=org_id, entry_id=removed.id
    )

    entries = await event_entry_service.list_event_entries(
        db_session, organization_id=org_id, event_log_type_id=log_type_id
    )

    assert [e.id for e in entries] == [newer.id, older.id]


async def test_get_event_entry_not_found_for_other_org(db_session: AsyncSession) -> None:
    org_a, user_id = await _signup_owner(db_session)
    org_b, _ = await _signup_owner(db_session)
    log_type_id = await _log_type_id(db_session, "glass")
    entry = await event_entry_service.record_event_entry(
        db_session,
        organization_id=org_a,
        event_log_type_id=log_type_id,
        entry_date=date(2026, 6, 1),
        responsible_user_id=user_id,
        payload={"details": "X"},
    )

    with pytest.raises(event_entry_service.EventEntryNotFoundError):
        await event_entry_service.get_event_entry(
            db_session, organization_id=org_b, entry_id=entry.id
        )


async def test_soft_delete_event_entry_then_get_raises(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    log_type_id = await _log_type_id(db_session, "glass")
    entry = await event_entry_service.record_event_entry(
        db_session,
        organization_id=org_id,
        event_log_type_id=log_type_id,
        entry_date=date(2026, 6, 1),
        responsible_user_id=user_id,
        payload={"details": "X"},
    )

    await event_entry_service.soft_delete_event_entry(
        db_session, organization_id=org_id, entry_id=entry.id
    )

    with pytest.raises(event_entry_service.EventEntryNotFoundError):
        await event_entry_service.get_event_entry(
            db_session, organization_id=org_id, entry_id=entry.id
        )
