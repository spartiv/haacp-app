import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class MedicalCheckCreateRequest(BaseModel):
    employee_name: str = Field(min_length=1, max_length=200)
    next_check_date: date


class MedicalCheckUpdateRequest(BaseModel):
    employee_name: str | None = Field(default=None, min_length=1, max_length=200)
    next_check_date: date | None = None


class MedicalCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    employee_name: str
    next_check_date: date
