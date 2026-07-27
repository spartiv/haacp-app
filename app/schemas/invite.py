import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import MembershipRole


class InviteCreateRequest(BaseModel):
    email: EmailStr
    role: MembershipRole


class InviteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    role: MembershipRole
    expires_at: datetime


class InvitePreviewResponse(BaseModel):
    organization_name: str
    email: str
    role: MembershipRole
    expires_at: datetime


class InviteAcceptRequest(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
