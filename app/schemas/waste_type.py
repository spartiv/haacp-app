import uuid

from pydantic import BaseModel, ConfigDict, Field


class WasteTypeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    disposal_method: str = Field(min_length=1, max_length=500)


class WasteTypeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    disposal_method: str | None = Field(default=None, min_length=1, max_length=500)


class WasteTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    disposal_method: str
