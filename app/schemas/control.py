import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import ControlPeriod
from app.schemas.common import JSONValue


class ControlChecklistItemCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=500)


class ControlChecklistItemUpdateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=500)


class ControlChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    period: ControlPeriod
    label: str
    position: int


class ControlAnswerInput(BaseModel):
    control_checklist_item_id: uuid.UUID
    answer: bool


class ControlAnswerResponse(BaseModel):
    control_checklist_item_id: uuid.UUID
    answer: bool


class ControlRecordUpsertRequest(BaseModel):
    answers: list[ControlAnswerInput]
    period_date: date | None = Field(
        default=None,
        description="Day (or, for monthly controls, any day within the month) being "
        "filled in. Defaults to today in the organization's timezone. Cannot be in "
        "the future.",
    )
    note: str | None = None


class ControlRecordResponse(BaseModel):
    id: uuid.UUID
    period: ControlPeriod
    period_date: date
    signatory_user_id: uuid.UUID
    has_deviation: bool
    note: str | None
    answers: list[ControlAnswerResponse]


class ControlRecordHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    snapshot: dict[str, JSONValue]
    edited_by_user_id: uuid.UUID
    created_at: datetime
