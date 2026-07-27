import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models import ChemicalCategory


class ChemicalCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: ChemicalCategory


class ChemicalUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: ChemicalCategory | None = None


class ChemicalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    category: ChemicalCategory
    attachment_id: uuid.UUID | None
