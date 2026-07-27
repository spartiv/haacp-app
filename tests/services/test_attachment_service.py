import uuid
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services import attachment_service, auth_service
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


async def test_upload_then_download_roundtrips(db_session: AsyncSession, tmp_path: Path) -> None:
    org_id, user_id = await _signup_owner(db_session)
    storage = LocalDiskStorageBackend(tmp_path)

    attachment = await attachment_service.upload_attachment(
        db_session,
        organization_id=org_id,
        uploaded_by_user_id=user_id,
        filename="passport.pdf",
        content_type="application/pdf",
        data=b"%PDF-1.4 fake",
        storage=storage,
    )

    fetched, data = await attachment_service.download_attachment(
        db_session, organization_id=org_id, attachment_id=attachment.id, storage=storage
    )
    assert data == b"%PDF-1.4 fake"
    assert fetched.filename == "passport.pdf"


async def test_upload_rejects_oversized_file(db_session: AsyncSession, tmp_path: Path) -> None:
    org_id, user_id = await _signup_owner(db_session)
    storage = LocalDiskStorageBackend(tmp_path)
    oversized = b"x" * (get_settings().attachment_max_size_bytes + 1)

    with pytest.raises(attachment_service.AttachmentTooLargeError):
        await attachment_service.upload_attachment(
            db_session,
            organization_id=org_id,
            uploaded_by_user_id=user_id,
            filename="huge.pdf",
            content_type="application/pdf",
            data=oversized,
            storage=storage,
        )


async def test_upload_rejects_unsupported_content_type(
    db_session: AsyncSession, tmp_path: Path
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    storage = LocalDiskStorageBackend(tmp_path)

    with pytest.raises(attachment_service.UnsupportedContentTypeError):
        await attachment_service.upload_attachment(
            db_session,
            organization_id=org_id,
            uploaded_by_user_id=user_id,
            filename="script.exe",
            content_type="application/x-msdownload",
            data=b"MZ",
            storage=storage,
        )


async def test_get_attachment_not_found_in_other_org(
    db_session: AsyncSession, tmp_path: Path
) -> None:
    org_a, user_id = await _signup_owner(db_session)
    org_b, _ = await _signup_owner(db_session)
    storage = LocalDiskStorageBackend(tmp_path)
    attachment = await attachment_service.upload_attachment(
        db_session,
        organization_id=org_a,
        uploaded_by_user_id=user_id,
        filename="doc.pdf",
        content_type="application/pdf",
        data=b"data",
        storage=storage,
    )

    with pytest.raises(attachment_service.AttachmentNotFoundError):
        await attachment_service.get_attachment(
            db_session, organization_id=org_b, attachment_id=attachment.id
        )


async def test_delete_attachment_removes_row_and_bytes(
    db_session: AsyncSession, tmp_path: Path
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    storage = LocalDiskStorageBackend(tmp_path)
    attachment = await attachment_service.upload_attachment(
        db_session,
        organization_id=org_id,
        uploaded_by_user_id=user_id,
        filename="doc.pdf",
        content_type="application/pdf",
        data=b"data",
        storage=storage,
    )

    await attachment_service.delete_attachment(db_session, attachment=attachment, storage=storage)

    with pytest.raises(attachment_service.AttachmentNotFoundError):
        await attachment_service.get_attachment(
            db_session, organization_id=org_id, attachment_id=attachment.id
        )
    with pytest.raises(FileNotFoundError):
        await storage.load(key=attachment.storage_key)
