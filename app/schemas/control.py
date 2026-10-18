import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import (
    ControlAuditEventType,
    ControlItemStatus,
    ControlItemType,
    ControlPeriod,
    ControlRecordStatus,
)
from app.schemas.common import JSONValue

# A reading or limit: up to 5 integer digits and 2 decimals (e.g. -18.5, 123.45).
Reading = Annotated[Decimal, Field(max_digits=7, decimal_places=2)]


class ControlChecklistItemCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=500)
    item_type: ControlItemType = Field(
        default=ControlItemType.BOOL,
        description="`bool`: Так/Ні, «Ні» is the deviation. `numeric`: a measured value, "
        "outside [min_value, max_value] is the deviation. Fixed after creation.",
    )
    unit: str | None = Field(
        default=None, max_length=20, description="Numeric items only, required (e.g. `°C`)."
    )
    min_value: Reading | None = Field(
        default=None, description="Numeric items: lowest safe value (inclusive)."
    )
    max_value: Reading | None = Field(
        default=None, description="Numeric items: highest safe value (inclusive)."
    )


class ControlChecklistItemUpdateRequest(BaseModel):
    """Partial update. Send only what changes; send `null` to open a bound.
    The item type cannot change."""

    label: str | None = Field(default=None, min_length=1, max_length=500)
    unit: str | None = Field(default=None, max_length=20)
    min_value: Reading | None = Field(default=None)
    max_value: Reading | None = Field(default=None)


class ControlChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    period: ControlPeriod
    label: str
    position: int
    item_type: ControlItemType
    unit: str | None
    min_value: float | None
    max_value: float | None


class ControlAnswerInput(BaseModel):
    control_checklist_item_id: uuid.UUID
    answer: bool


class ControlAnswerResponse(BaseModel):
    control_checklist_item_id: uuid.UUID
    answer: bool
    numeric_value: float | None = None


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


# ---- Per-item sheet workflow ----


class UserRefResponse(BaseModel):
    id: uuid.UUID
    full_name: str


class ItemCheckRequest(BaseModel):
    status: Literal["pass", "deviation"] | None = Field(
        default=None,
        description="Required for Yes/No items. Ignored for numeric items: the server "
        "judges `value` against the item's range.",
    )
    value: Reading | None = Field(
        default=None,
        description="Required for numeric items (the measured reading); not allowed for "
        "Yes/No items. Outside the range = `deviation`, which needs a corrective action.",
    )
    corrective_action: str | None = Field(
        default=None,
        max_length=2000,
        description="Required (min 3 characters) when status is `deviation`; ignored for `pass`.",
    )
    amendment_reason: str | None = Field(
        default=None,
        max_length=1000,
        description="Required (min 3 characters) when the record is already submitted.",
    )
    performed_by_user_id: uuid.UUID | None = Field(
        default=None,
        description="Who physically did the check, on a shared device. Must be an active "
        "member. Defaults to the signed-in user, who is always recorded as well.",
    )
    period_date: date | None = Field(
        default=None,
        description="Day (or any day within the month) to check. Defaults to the current "
        "period in the organization's timezone. Cannot be in the future.",
    )


class SheetItemResponse(BaseModel):
    control_checklist_item_id: uuid.UUID
    label: str
    position: int
    item_type: ControlItemType
    unit: str | None
    min_value: float | None = Field(
        description="Numeric items: the limits the current value was judged against "
        "(the item's current limits until it is first measured)."
    )
    max_value: float | None
    value: float | None = Field(description="Numeric items: the recorded reading.")
    status: ControlItemStatus
    corrective_action: str | None
    checked_by: UserRefResponse | None = Field(description="The signed-in account that saved it.")
    performed_by: UserRefResponse | None = Field(description="Who physically did the check.")
    checked_at: datetime | None


class ControlSheetResponse(BaseModel):
    record_id: uuid.UUID | None = Field(description="Null until the first item is checked.")
    period: ControlPeriod
    period_date: date
    status: ControlRecordStatus | None
    has_deviation: bool
    note: str | None
    submitted_at: datetime | None
    submitted_by: UserRefResponse | None
    items: list[SheetItemResponse]


class AuditEventResponse(BaseModel):
    id: uuid.UUID
    seq: int
    event_type: ControlAuditEventType
    control_checklist_item_id: uuid.UUID | None
    item_label: str | None
    item_unit: str | None
    numeric_value: float | None = Field(description="Numeric items: the reading recorded.")
    previous_status: ControlItemStatus | None
    new_status: ControlItemStatus | None
    corrective_action: str | None
    amendment_reason: str | None
    actor: UserRefResponse
    performed_by: UserRefResponse
    created_at: datetime


class AuditEventPageResponse(BaseModel):
    items: list[AuditEventResponse]
    next_cursor: str | None = Field(
        description="Pass as `cursor` to get the next (older) page. Null on the last page."
    )
