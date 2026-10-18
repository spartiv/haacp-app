import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models import EventLogSchema
from app.schemas.common import JSONValue


class EventLogTypeResponse(BaseModel):
    # Built explicitly in the router rather than via model_validate: the ORM
    # attribute is named `schema`, which Pydantic's BaseModel warns about
    # shadowing, so the API field is named `log_schema` instead.
    id: uuid.UUID
    key: str
    name: str
    log_schema: EventLogSchema
    icon_label: str
    position: int


class EventEntryCreateRequest(BaseModel):
    entry_date: date
    payload: dict[str, JSONValue]
    performed_by_user_id: uuid.UUID | None = Field(
        default=None,
        description="Who physically did it, on a shared device. Must be an active member. "
        "Defaults to the signed-in user (always recorded as `responsible_user_id`).",
    )


class EventEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_log_type_id: uuid.UUID
    entry_date: date
    responsible_user_id: uuid.UUID = Field(description="The signed-in account that saved it.")
    performed_by_user_id: uuid.UUID = Field(description="Who physically did it.")
    payload: dict[str, JSONValue]
    has_deviation: bool
