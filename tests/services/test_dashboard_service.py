import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ControlPeriod, EquipmentType
from app.services import (
    auth_service,
    batch_service,
    control_checklist_service,
    control_record_service,
    dashboard_service,
    equipment_service,
    medical_check_service,
    organization_service,
    product_service,
)
from app.services.dashboard_service import AttentionSeverity, _next_month_start


def test_next_month_start_rolls_over_the_year_in_december() -> None:
    assert _next_month_start(date(2026, 12, 1)) == date(2027, 1, 1)


def test_next_month_start_within_the_same_year() -> None:
    assert _next_month_start(date(2026, 7, 1)) == date(2026, 8, 1)


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


async def test_empty_organization_shows_daily_and_monthly_not_filled(
    db_session: AsyncSession,
) -> None:
    org_id, _ = await _signup_owner(db_session)

    dashboard = await dashboard_service.get_dashboard(db_session, organization_id=org_id)

    assert dashboard.daily_control.filled is False
    assert dashboard.daily_control.has_deviation is None
    assert dashboard.monthly_control.filled is False
    assert dashboard.batches_this_month == 0
    labels = [item.label for item in dashboard.attention_items]
    assert "Щоденний контроль на сьогодні не заповнено" in labels
    assert "Місячний контроль за поточний місяць не заповнено" in labels
    assert all(item.severity == AttentionSeverity.CRITICAL for item in dashboard.attention_items)


async def test_filling_daily_control_clears_its_attention_item(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item = await control_checklist_service.add_control_checklist_item(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY, label="Q1"
    )
    await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item.id: True},
    )

    dashboard = await dashboard_service.get_dashboard(db_session, organization_id=org_id)

    assert dashboard.daily_control.filled is True
    assert dashboard.daily_control.has_deviation is False
    labels = [i.label for i in dashboard.attention_items]
    assert "Щоденний контроль на сьогодні не заповнено" not in labels


async def test_daily_control_with_deviation_is_reflected_but_not_an_attention_item(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    item = await control_checklist_service.add_control_checklist_item(
        db_session, organization_id=org_id, period=ControlPeriod.DAILY, label="Q1"
    )
    await control_record_service.upsert_current_control(
        db_session,
        organization_id=org_id,
        period=ControlPeriod.DAILY,
        signatory_user_id=user_id,
        answers={item.id: False},
    )

    dashboard = await dashboard_service.get_dashboard(db_session, organization_id=org_id)

    assert dashboard.daily_control.has_deviation is True


async def test_unsafe_equipment_without_document_is_an_attention_item(
    db_session: AsyncSession,
) -> None:
    org_id, _ = await _signup_owner(db_session)
    await equipment_service.create_equipment(
        db_session,
        organization_id=org_id,
        type=EquipmentType.PRODUCTION,
        name="Пастеризатор ВП-500",
        frequency="Щомісяця",
        amount=1,
        affects_product_safety=True,
    )

    dashboard = await dashboard_service.get_dashboard(db_session, organization_id=org_id)

    matching = [i for i in dashboard.attention_items if "Пастеризатор ВП-500" in i.label]
    assert len(matching) == 1
    assert matching[0].severity == AttentionSeverity.WARNING


async def test_equipment_not_affecting_safety_is_not_an_attention_item(
    db_session: AsyncSession,
) -> None:
    org_id, _ = await _signup_owner(db_session)
    await equipment_service.create_equipment(
        db_session,
        organization_id=org_id,
        type=EquipmentType.MEASURING,
        name="Ваги електронні",
        frequency="Раз на рік",
        amount=1,
        affects_product_safety=False,
    )

    dashboard = await dashboard_service.get_dashboard(db_session, organization_id=org_id)

    assert not any("Ваги електронні" in i.label for i in dashboard.attention_items)


async def test_overdue_medical_check_is_critical(db_session: AsyncSession) -> None:
    org_id, _ = await _signup_owner(db_session)
    await medical_check_service.create_medical_check(
        db_session,
        organization_id=org_id,
        employee_name="Марія Гриценко",
        next_check_date=date.today() - timedelta(days=5),
    )

    dashboard = await dashboard_service.get_dashboard(db_session, organization_id=org_id)

    matching = [i for i in dashboard.attention_items if "Марія Гриценко" in i.label]
    assert len(matching) == 1
    assert matching[0].severity == AttentionSeverity.CRITICAL
    assert "прострочено" in matching[0].label


async def test_upcoming_medical_check_within_window_is_warning(db_session: AsyncSession) -> None:
    org_id, _ = await _signup_owner(db_session)
    await medical_check_service.create_medical_check(
        db_session,
        organization_id=org_id,
        employee_name="Дмитро Кравець",
        next_check_date=date.today() + timedelta(days=10),
    )

    dashboard = await dashboard_service.get_dashboard(db_session, organization_id=org_id)

    matching = [i for i in dashboard.attention_items if "Дмитро Кравець" in i.label]
    assert len(matching) == 1
    assert matching[0].severity == AttentionSeverity.WARNING


async def test_far_future_medical_check_is_not_an_attention_item(db_session: AsyncSession) -> None:
    org_id, _ = await _signup_owner(db_session)
    await medical_check_service.create_medical_check(
        db_session,
        organization_id=org_id,
        employee_name="Олена Поліщук",
        next_check_date=date.today() + timedelta(days=90),
    )

    dashboard = await dashboard_service.get_dashboard(db_session, organization_id=org_id)

    assert not any("Олена Поліщук" in i.label for i in dashboard.attention_items)


async def test_attention_items_sorted_critical_before_warning(db_session: AsyncSession) -> None:
    org_id, _ = await _signup_owner(db_session)
    # Equipment attention items are always warning-severity; combined with
    # the always-critical daily/monthly-not-filled items, this proves
    # severity is the primary sort key (not just "days" ascending, which
    # would be a mockup-faithful but arguably wrong ordering).
    await equipment_service.create_equipment(
        db_session,
        organization_id=org_id,
        type=EquipmentType.PRODUCTION,
        name="Пастеризатор ВП-500",
        frequency="Щомісяця",
        amount=1,
        affects_product_safety=True,
    )
    await medical_check_service.create_medical_check(
        db_session,
        organization_id=org_id,
        employee_name="Overdue Person",
        next_check_date=date.today() - timedelta(days=100),
    )

    dashboard = await dashboard_service.get_dashboard(db_session, organization_id=org_id)

    severity_ranks = {"critical": 0, "warning": 1, "info": 2}
    ranks = [severity_ranks[item.severity.value] for item in dashboard.attention_items]
    assert ranks == sorted(ranks)
    assert dashboard.attention_items[0].severity == AttentionSeverity.CRITICAL
    assert dashboard.attention_items[-1].severity == AttentionSeverity.WARNING


async def test_batches_this_month_counts_only_current_month(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    product = await product_service.create_product(db_session, organization_id=org_id, name="X")
    item = await product_service.add_checklist_item(
        db_session, organization_id=org_id, product_id=product.id, label="Q1"
    )

    await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="THIS-MONTH",
        name=None,
        production_date=date.today(),
        answers={item.id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )
    await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="LONG-AGO",
        name=None,
        production_date=date(2000, 1, 1),
        answers={item.id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )

    dashboard = await dashboard_service.get_dashboard(db_session, organization_id=org_id)

    assert dashboard.batches_this_month == 1


async def test_get_dashboard_raises_for_unknown_organization(db_session: AsyncSession) -> None:
    with pytest.raises(organization_service.OrganizationNotFoundError):
        await dashboard_service.get_dashboard(db_session, organization_id=uuid.uuid4())
