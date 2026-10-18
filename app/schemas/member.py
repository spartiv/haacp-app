import uuid

from pydantic import BaseModel

from app.models import MembershipRole, MembershipStatus


class MemberResponse(BaseModel):
    user_id: uuid.UUID
    full_name: str
    role: MembershipRole
    title: str | None
    status: MembershipStatus
