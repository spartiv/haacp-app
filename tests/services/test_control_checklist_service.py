import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ControlPeriod
from app.services import auth_service, control_checklist_service


async def _signup_owner(db_session: AsyncSession) -> uuid.UUID:
    result = await auth_service.signup(
        db_session,
        email=f"owner-{uuid.uuid4().hex}@polton.ua",
        password="supersecret123",
        full_name="Olena Polishchuk",
        organization_name="Polton",
    )
    assert result.organization_id is not None
    return result.organization_id


async def test_add_and_list_checklist_items_scoped_by_period(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)

    daily_item = await control_checklist_service.add_control_checklist_item(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY, label="Якість води в нормі"
    )
    await control_checklist_service.add_control_checklist_item(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.MONTHLY,
        label="Дератизація проведена",
    )

    daily_items = await control_checklist_service.list_control_checklist_items(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY
    )
    monthly_items = await control_checklist_service.list_control_checklist_items(
        db_session, organization_id=org_id, period=ControlPeriod.MONTHLY
    )

    assert [i.id for i in daily_items] == [daily_item.id]
    assert len(monthly_items) == 1


async def test_add_checklist_items_increments_position_per_period(
    db_session: AsyncSession,
) -> None:
    org_id = await _signup_owner(db_session)

    first = await control_checklist_service.add_control_checklist_item(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY, label="Q1"
    )
    second = await control_checklist_service.add_control_checklist_item(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY, label="Q2"
    )
    monthly_first = await control_checklist_service.add_control_checklist_item(
        db_session, organization_id=org_id, period=ControlPeriod.MONTHLY, label="M1"
    )

    assert first.position == 0
    assert second.position == 1
    assert monthly_first.position == 0


async def test_update_and_remove_checklist_item(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)
    item = await control_checklist_service.add_control_checklist_item(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY, label="Old"
    )

    updated = await control_checklist_service.update_control_checklist_item(
        db_session, organization_id=org_id, item_id=item.id, label="New"
    )
    assert updated.label == "New"

    await control_checklist_service.remove_control_checklist_item(
        db_session, organization_id=org_id, item_id=item.id
    )

    items = await control_checklist_service.list_control_checklist_items(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY
    )
    assert items == []


async def test_update_unknown_checklist_item_raises(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)

    with pytest.raises(control_checklist_service.ControlChecklistItemNotFoundError):
        await control_checklist_service.update_control_checklist_item(
            db_session, organization_id=org_id, item_id=uuid.uuid4(), label="X"
        )
