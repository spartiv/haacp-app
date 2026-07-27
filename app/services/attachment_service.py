import logging
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.models import Attachment
from app.services.storage import StorageBackend

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = frozenset({"application/pdf", "image/png", "image/jpeg"})

_SAFE_EXTENSION = re.compile(r"^[A-Za-z0-9]{1,10}$")


class AttachmentNotFoundError(NotFoundError):
    code = "attachment_not_found"
    message = "Attachment not found"


class AttachmentTooLargeError(Exception):
    pass


class UnsupportedContentTypeError(Exception):
    pass


def _safe_extension(filename: str) -> str:
    """Only used to make the stored file end in something recognizable; the
    original filename (for display/download) is stored separately, so this
    never needs to round-trip exactly."""
    suffix = filename.rsplit(".", 1)[-1] if "." in filename else ""
    return f".{suffix}" if _SAFE_EXTENSION.match(suffix) else ""


async def upload_attachment(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    uploaded_by_user_id: uuid.UUID,
    filename: str,
    content_type: str,
    data: bytes,
    storage: StorageBackend,
) -> Attachment:
    settings = get_settings()
    if len(data) > settings.attachment_max_size_bytes:
        raise AttachmentTooLargeError
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedContentTypeError

    storage_key = f"{organization_id}/{uuid.uuid4().hex}{_safe_extension(filename)}"
    await storage.save(key=storage_key, data=data)

    attachment = Attachment(
        organization_id=organization_id,
        filename=filename,
        content_type=content_type,
        size_bytes=len(data),
        storage_key=storage_key,
        uploaded_by_user_id=uploaded_by_user_id,
    )
    db.add(attachment)
    await db.commit()
    logger.info(
        "Attachment uploaded: attachment_id=%s organization_id=%s size_bytes=%d",
        attachment.id,
        organization_id,
        len(data),
    )
    return attachment


async def get_attachment(
    db: AsyncSession, *, organization_id: uuid.UUID, attachment_id: uuid.UUID
) -> Attachment:
    result = await db.execute(
        select(Attachment).where(
            Attachment.id == attachment_id, Attachment.organization_id == organization_id
        )
    )
    attachment = result.scalar_one_or_none()
    if attachment is None:
        raise AttachmentNotFoundError
    return attachment


async def download_attachment(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    attachment_id: uuid.UUID,
    storage: StorageBackend,
) -> tuple[Attachment, bytes]:
    attachment = await get_attachment(
        db, organization_id=organization_id, attachment_id=attachment_id
    )
    data = await storage.load(key=attachment.storage_key)
    return attachment, data


async def delete_attachment(
    db: AsyncSession, *, attachment: Attachment, storage: StorageBackend
) -> None:
    """Internal helper for owning-entity services (Equipment, Chemical, ...)
    to call once they've cleared their own FK to this attachment. Not
    exposed as a standalone router endpoint, so an attachment can never be
    deleted out from under something that still references it.

    The DB delete is committed *before* the storage file is removed: if the
    commit fails, the file is untouched and nothing is lost; if it
    succeeds, the row is gone for good and removing the now-unreferenced
    file afterward is safe. Doing it in the other order risks deleting the
    file and then failing the commit, leaving a DB row pointing at nothing.
    """
    attachment_id = attachment.id
    storage_key = attachment.storage_key
    await db.delete(attachment)
    await db.commit()
    await storage.delete(key=storage_key)
    logger.info("Attachment deleted: attachment_id=%s", attachment_id)
