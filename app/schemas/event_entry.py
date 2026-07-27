import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

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


class EventEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_log_type_id: uuid.UUID
    entry_date: date
    responsible_user_id: uuid.UUID
    payload: dict[str, JSONValue]
    has_deviation: bool
