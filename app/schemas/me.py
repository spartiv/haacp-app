import uuid

from pydantic import BaseModel


class MyOrganizationResponse(BaseModel):
    organization_id: uuid.UUID
    name: str
    role: str
    title: str | None
