import uuid
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EquipmentType
from app.services import attachment_service, auth_service, equipment_service
from app.services.storage import LocalDiskStorageBackend


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


async def test_create_and_get_equipment(db_session: AsyncSession) -> None:
    org_id, _ = await _signup_owner(db_session)

    equipment = await equipment_service.create_equipment(
        db_session,
        organization_id=org_id,
        type=EquipmentType.PRODUCTION,
        name="Пастеризатор ВП-500",
        frequency="Щомісяця",
        amount=1,
        affects_product_safety=True,
    )

    fetched = await equipment_service.get_equipment(
        db_session, organization_id=org_id, equipment_id=equipment.id
    )
    assert fetched.name == "Пастеризатор ВП-500"
    assert fetched.affects_product_safety is True


async def test_get_equipment_not_found_in_other_org(db_session: AsyncSession) -> None:
    org_a, _ = await _signup_owner(db_session)
    org_b, _ = await _signup_owner(db_session)
    equipment = await equipment_service.create_equipment(
        db_session,
        organization_id=org_a,
        type=EquipmentType.OTHER,
        name="X",
        frequency="Щомісяця",
        amount=1,
        affects_product_safety=False,
    )

    with pytest.raises(equipment_service.EquipmentNotFoundError):
        await equipment_service.get_equipment(
            db_session, organization_id=org_b, equipment_id=equipment.id
        )


async def test_list_equipment_excludes_soft_deleted(db_session: AsyncSession) -> None:
    org_id, _ = await _signup_owner(db_session)
    keep = await equipment_service.create_equipment(
        db_session,
        organization_id=org_id,
        type=EquipmentType.MEASURING,
        name="Keep",
        frequency="Раз на рік",
        amount=1,
        affects_product_safety=False,
    )
    remove = await equipment_service.create_equipment(
        db_session,
        organization_id=org_id,
        type=EquipmentType.MEASURING,
        name="Remove",
        frequency="Раз на рік",
        amount=1,
        affects_product_safety=False,
    )
    await equipment_service.soft_delete_equipment(
        db_session, organization_id=org_id, equipment_id=remove.id
    )

    equipment_list = await equipment_service.list_equipment(db_session, organization_id=org_id)

    assert [e.id for e in equipment_list] == [keep.id]


async def test_update_equipment_partial_fields(db_session: AsyncSession) -> None:
    org_id, _ = await _signup_owner(db_session)
    equipment = await equipment_service.create_equipment(
        db_session,
        organization_id=org_id,
        type=EquipmentType.REFRIGERATION,
        name="Холодильна камера №1",
        frequency="Раз на квартал",
        amount=2,
        affects_product_safety=True,
    )

    updated = await equipment_service.update_equipment(
        db_session, organization_id=org_id, equipment_id=equipment.id, amount=5
    )

    assert updated.amount == 5
    assert updated.name == "Холодильна камера №1"
    assert updated.frequency == "Раз на квартал"

    fully_updated = await equipment_service.update_equipment(
        db_session,
        organization_id=org_id,
        equipment_id=equipment.id,
        type=EquipmentType.OTHER,
        name="Renamed",
        frequency="Щотижня",
        affects_product_safety=False,
    )

    assert fully_updated.type == EquipmentType.OTHER
    assert fully_updated.name == "Renamed"
    assert fully_updated.frequency == "Щотижня"
    assert fully_updated.affects_product_safety is False
    assert fully_updated.amount == 5


async def test_attach_and_detach_document(db_session: AsyncSession, tmp_path: Path) -> None:
    org_id, user_id = await _signup_owner(db_session)
    storage = LocalDiskStorageBackend(tmp_path)
    equipment = await equipment_service.create_equipment(
        db_session,
        organization_id=org_id,
        type=EquipmentType.PRODUCTION,
        name="X",
        frequency="Щомісяця",
        amount=1,
        affects_product_safety=True,
    )
    attachment = await attachment_service.upload_attachment(
        db_session,
        organization_id=org_id,
        uploaded_by_user_id=user_id,
        filename="passport.pdf",
        content_type="application/pdf",
        data=b"data",
        storage=storage,
    )

    attached = await equipment_service.attach_document(
        db_session,
        organization_id=org_id,
        equipment_id=equipment.id,
        attachment_id=attachment.id,
        storage=storage,
    )
    assert attached.attachment_id == attachment.id

    detached = await equipment_service.detach_document(
        db_session, organization_id=org_id, equipment_id=equipment.id, storage=storage
    )
    assert detached.attachment_id is None
    with pytest.raises(attachment_service.AttachmentNotFoundError):
        await attachment_service.get_attachment(
            db_session, organization_id=org_id, attachment_id=attachment.id
        )


async def test_attaching_new_document_replaces_and_deletes_old_one(
    db_session: AsyncSession, tmp_path: Path
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    storage = LocalDiskStorageBackend(tmp_path)
    equipment = await equipment_service.create_equipment(
        db_session,
        organization_id=org_id,
        type=EquipmentType.PRODUCTION,
        name="X",
        frequency="Щомісяця",
        amount=1,
        affects_product_safety=True,
    )
    old_attachment = await attachment_service.upload_attachment(
        db_session,
        organization_id=org_id,
        uploaded_by_user_id=user_id,
        filename="old.pdf",
        content_type="application/pdf",
        data=b"old",
        storage=storage,
    )
    await equipment_service.attach_document(
        db_session,
        organization_id=org_id,
        equipment_id=equipment.id,
        attachment_id=old_attachment.id,
        storage=storage,
    )
    new_attachment = await attachment_service.upload_attachment(
        db_session,
        organization_id=org_id,
        uploaded_by_user_id=user_id,
        filename="new.pdf",
        content_type="application/pdf",
        data=b"new",
        storage=storage,
    )

    updated = await equipment_service.attach_document(
        db_session,
        organization_id=org_id,
        equipment_id=equipment.id,
        attachment_id=new_attachment.id,
        storage=storage,
    )

    assert updated.attachment_id == new_attachment.id
    with pytest.raises(attachment_service.AttachmentNotFoundError):
        await attachment_service.get_attachment(
            db_session, organization_id=org_id, attachment_id=old_attachment.id
        )


async def test_detach_document_when_none_attached_is_a_no_op(
    db_session: AsyncSession, tmp_path: Path
) -> None:
    org_id, _ = await _signup_owner(db_session)
    storage = LocalDiskStorageBackend(tmp_path)
    equipment = await equipment_service.create_equipment(
        db_session,
        organization_id=org_id,
        type=EquipmentType.OTHER,
        name="X",
        frequency="Щомісяця",
        amount=1,
        affects_product_safety=False,
    )

    result = await equipment_service.detach_document(
        db_session, organization_id=org_id, equipment_id=equipment.id, storage=storage
    )

    assert result.attachment_id is None
