import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChemicalCategory
from app.services import attachment_service, auth_service, chemical_service
from app.services.storage import S3StorageBackend


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


async def test_create_list_and_update_chemical(db_session: AsyncSession) -> None:
    org_id, _ = await _signup_owner(db_session)
    chemical = await chemical_service.create_chemical(
        db_session,
        organization_id=org_id,
        name="Деохлор (дезінфектант)",
        category=ChemicalCategory.DISINFECTING,
    )

    updated = await chemical_service.update_chemical(
        db_session,
        organization_id=org_id,
        chemical_id=chemical.id,
        category=ChemicalCategory.CLEANING,
    )
    assert updated.category == ChemicalCategory.CLEANING

    renamed = await chemical_service.update_chemical(
        db_session, organization_id=org_id, chemical_id=chemical.id, name="Мийний засіб лужний"
    )
    assert renamed.name == "Мийний засіб лужний"
    assert renamed.category == ChemicalCategory.CLEANING

    chemicals = await chemical_service.list_chemicals(db_session, organization_id=org_id)
    assert [c.id for c in chemicals] == [chemical.id]


async def test_soft_delete_chemical_then_get_raises(db_session: AsyncSession) -> None:
    org_id, _ = await _signup_owner(db_session)
    chemical = await chemical_service.create_chemical(
        db_session, organization_id=org_id, name="X", category=ChemicalCategory.CLEANING
    )

    await chemical_service.soft_delete_chemical(
        db_session, organization_id=org_id, chemical_id=chemical.id
    )

    with pytest.raises(chemical_service.ChemicalNotFoundError):
        await chemical_service.get_chemical(
            db_session, organization_id=org_id, chemical_id=chemical.id
        )


async def test_attach_and_detach_chemical_document(
    db_session: AsyncSession, s3_storage: S3StorageBackend
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    storage = s3_storage
    chemical = await chemical_service.create_chemical(
        db_session, organization_id=org_id, name="X", category=ChemicalCategory.CLEANING
    )
    attachment = await attachment_service.upload_attachment(
        db_session,
        organization_id=org_id,
        uploaded_by_user_id=user_id,
        filename="sds.pdf",
        content_type="application/pdf",
        data=b"data",
        storage=storage,
    )

    attached = await chemical_service.attach_document(
        db_session,
        organization_id=org_id,
        chemical_id=chemical.id,
        attachment_id=attachment.id,
        storage=storage,
    )
    assert attached.attachment_id == attachment.id

    detached = await chemical_service.detach_document(
        db_session, organization_id=org_id, chemical_id=chemical.id, storage=storage
    )
    assert detached.attachment_id is None


async def test_attaching_new_chemical_document_replaces_and_deletes_old_one(
    db_session: AsyncSession, s3_storage: S3StorageBackend
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    storage = s3_storage
    chemical = await chemical_service.create_chemical(
        db_session, organization_id=org_id, name="X", category=ChemicalCategory.CLEANING
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
    await chemical_service.attach_document(
        db_session,
        organization_id=org_id,
        chemical_id=chemical.id,
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

    updated = await chemical_service.attach_document(
        db_session,
        organization_id=org_id,
        chemical_id=chemical.id,
        attachment_id=new_attachment.id,
        storage=storage,
    )

    assert updated.attachment_id == new_attachment.id
    with pytest.raises(attachment_service.AttachmentNotFoundError):
        await attachment_service.get_attachment(
            db_session, organization_id=org_id, attachment_id=old_attachment.id
        )
