import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import auth_service, waste_type_service


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


async def test_create_list_update_and_delete_waste_type(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)
    waste_type = await waste_type_service.create_waste_type(
        db_session,
        organization_id=org_id,
        name="Пакувальні відходи (пластик)",
        disposal_method="Сортування, вивіз ліцензованим перевізником",
    )

    updated = await waste_type_service.update_waste_type(
        db_session,
        organization_id=org_id,
        waste_type_id=waste_type.id,
        disposal_method="Компостування",
    )
    assert updated.disposal_method == "Компостування"

    renamed = await waste_type_service.update_waste_type(
        db_session, organization_id=org_id, waste_type_id=waste_type.id, name="Органічні відходи"
    )
    assert renamed.name == "Органічні відходи"
    assert renamed.disposal_method == "Компостування"

    waste_types = await waste_type_service.list_waste_types(db_session, organization_id=org_id)
    assert [w.id for w in waste_types] == [waste_type.id]

    await waste_type_service.soft_delete_waste_type(
        db_session, organization_id=org_id, waste_type_id=waste_type.id
    )
    with pytest.raises(waste_type_service.WasteTypeNotFoundError):
        await waste_type_service.get_waste_type(
            db_session, organization_id=org_id, waste_type_id=waste_type.id
        )


async def test_get_waste_type_not_found_in_other_org(db_session: AsyncSession) -> None:
    org_a = await _signup_owner(db_session)
    org_b = await _signup_owner(db_session)
    waste_type = await waste_type_service.create_waste_type(
        db_session, organization_id=org_a, name="X", disposal_method="Y"
    )

    with pytest.raises(waste_type_service.WasteTypeNotFoundError):
        await waste_type_service.get_waste_type(
            db_session, organization_id=org_b, waste_type_id=waste_type.id
        )
