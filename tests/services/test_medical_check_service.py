import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import auth_service, medical_check_service


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


async def test_create_list_update_and_delete_medical_check(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)
    check = await medical_check_service.create_medical_check(
        db_session,
        organization_id=org_id,
        employee_name="Марія Гриценко",
        next_check_date=date(2026, 7, 30),
    )

    updated = await medical_check_service.update_medical_check(
        db_session,
        organization_id=org_id,
        medical_check_id=check.id,
        next_check_date=date(2026, 8, 15),
    )
    assert updated.next_check_date == date(2026, 8, 15)

    renamed = await medical_check_service.update_medical_check(
        db_session,
        organization_id=org_id,
        medical_check_id=check.id,
        employee_name="Дмитро Кравець",
    )
    assert renamed.employee_name == "Дмитро Кравець"
    assert renamed.next_check_date == date(2026, 8, 15)

    checks = await medical_check_service.list_medical_checks(db_session, organization_id=org_id)
    assert [c.id for c in checks] == [check.id]

    await medical_check_service.soft_delete_medical_check(
        db_session, organization_id=org_id, medical_check_id=check.id
    )
    with pytest.raises(medical_check_service.MedicalCheckNotFoundError):
        await medical_check_service.get_medical_check(
            db_session, organization_id=org_id, medical_check_id=check.id
        )


async def test_list_orders_by_next_check_date(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)
    later = await medical_check_service.create_medical_check(
        db_session, organization_id=org_id, employee_name="B", next_check_date=date(2026, 10, 10)
    )
    sooner = await medical_check_service.create_medical_check(
        db_session, organization_id=org_id, employee_name="A", next_check_date=date(2026, 7, 5)
    )

    checks = await medical_check_service.list_medical_checks(db_session, organization_id=org_id)

    assert [c.id for c in checks] == [sooner.id, later.id]
