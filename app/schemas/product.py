import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import JSONValue


class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str


class ChecklistItemCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=500)


class ChecklistItemUpdateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=500)


class ChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    label: str
    position: int


class BatchAnswerInput(BaseModel):
    checklist_item_id: uuid.UUID
    answer: bool


class BatchAnswerResponse(BaseModel):
    checklist_item_id: uuid.UUID
    answer: bool


class BatchCreateRequest(BaseModel):
    number: str = Field(min_length=1, max_length=100)
    name: str | None = Field(default=None, max_length=200)
    production_date: date
    answers: list[BatchAnswerInput]
    deviation_note: str | None = None
    corrective_action: str | None = None
    performed_by_user_id: uuid.UUID | None = Field(
        default=None,
        description="Who physically made / checked the batch, on a shared device. Must be "
        "an active member. Defaults to the signed-in user (always recorded as signatory).",
    )


class BatchUpdateRequest(BaseModel):
    number: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = None
    production_date: date | None = None
    answers: list[BatchAnswerInput] | None = None
    deviation_note: str | None = None
    corrective_action: str | None = None


class BatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    number: str
    name: str | None
    production_date: date
    has_deviation: bool
    deviation_note: str | None
    corrective_action: str | None
    signatory_user_id: uuid.UUID = Field(description="The signed-in account that saved it.")
    performed_by_user_id: uuid.UUID = Field(description="Who physically did it.")
    answers: list[BatchAnswerResponse]


class BatchHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    snapshot: dict[str, JSONValue]
    edited_by_user_id: uuid.UUID
    created_at: datetime
