import uuid
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user, require_membership
from app.db.session import get_db_session
from app.models import Membership, User
from app.schemas.attachment import AttachmentResponse
from app.services import attachment_service
from app.services.storage import StorageBackend, get_storage_backend

router = APIRouter(prefix="/organizations/{organization_id}/attachments", tags=["attachments"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AnyMember = Annotated[Membership, Depends(require_membership())]
CurrentUser = Annotated[User, Depends(get_current_user)]
Storage = Annotated[StorageBackend, Depends(get_storage_backend)]

_UPLOAD_READ_CHUNK_SIZE = 1024 * 1024


async def _read_bounded(file: UploadFile, *, max_size: int) -> bytes:
    """Reads the upload in chunks and aborts as soon as the configured size
    limit is exceeded, instead of buffering the whole body first and only
    checking its size afterward."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_UPLOAD_READ_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_size:
            raise attachment_service.AttachmentTooLargeError
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    organization_id: uuid.UUID,
    file: UploadFile,
    db: DbSession,
    current_user: CurrentUser,
    storage: Storage,
    _: AnyMember,
) -> AttachmentResponse:
    data = await _read_bounded(file, max_size=get_settings().attachment_max_size_bytes)
    attachment = await attachment_service.upload_attachment(
        db,
        organization_id=organization_id,
        uploaded_by_user_id=current_user.id,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        data=data,
        storage=storage,
    )
    return AttachmentResponse.model_validate(attachment)


@router.get("/{attachment_id}")
async def download_attachment(
    organization_id: uuid.UUID,
    attachment_id: uuid.UUID,
    db: DbSession,
    storage: Storage,
    _: AnyMember,
) -> StreamingResponse:
    attachment = await attachment_service.get_attachment(
        db, organization_id=organization_id, attachment_id=attachment_id
    )
    return StreamingResponse(
        storage.stream(key=attachment.storage_key),
        media_type=attachment.content_type,
        headers={"Content-Disposition": _content_disposition(attachment.filename)},
    )


def _content_disposition(filename: str) -> str:
    """HTTP headers are Latin-1 only, so a Ukrainian filename would crash the
    response. Send an ASCII fallback plus the exact UTF-8 name (RFC 6266 / 5987),
    which every current browser prefers."""
    fallback = filename.encode("ascii", "replace").decode("ascii")
    fallback = "".join("_" if ch in '"\\\r\n?' else ch for ch in fallback) or "download"
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(filename, safe='')}"
