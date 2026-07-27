import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models import EquipmentType


class EquipmentCreateRequest(BaseModel):
    type: EquipmentType
    name: str = Field(min_length=1, max_length=200)
    frequency: str = Field(min_length=1, max_length=200)
    amount: int = Field(default=1, ge=1)
    affects_product_safety: bool = False


class EquipmentUpdateRequest(BaseModel):
    type: EquipmentType | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    frequency: str | None = Field(default=None, min_length=1, max_length=200)
    amount: int | None = Field(default=None, ge=1)
    affects_product_safety: bool | None = None


class EquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    type: EquipmentType
    name: str
    frequency: str
    amount: int
    affects_product_safety: bool
    attachment_id: uuid.UUID | None
