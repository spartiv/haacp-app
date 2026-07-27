import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachDocumentRequest(BaseModel):
    attachment_id: uuid.UUID


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    uploaded_by_user_id: uuid.UUID
    created_at: datetime
