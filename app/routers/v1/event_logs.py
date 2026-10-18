import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_membership
from app.db.session import get_db_session
from app.models import EventEntry, Membership, User
from app.schemas.event_entry import (
    EventEntryCreateRequest,
    EventEntryResponse,
    EventLogTypeResponse,
)
from app.services import event_entry_service

router = APIRouter(prefix="/organizations/{organization_id}", tags=["event-logs"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AnyMember = Annotated[Membership, Depends(require_membership())]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _entry_response(entry: EventEntry) -> EventEntryResponse:
    return EventEntryResponse(
        id=entry.id,
        event_log_type_id=entry.event_log_type_id,
        entry_date=entry.entry_date,
        responsible_user_id=entry.responsible_user_id,
        performed_by_user_id=entry.performed_by_user_id or entry.responsible_user_id,
        payload=entry.payload,
        has_deviation=entry.has_deviation,
    )


@router.get("/event-log-types", response_model=list[EventLogTypeResponse])
async def list_event_log_types(
    organization_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[EventLogTypeResponse]:
    log_types = await event_entry_service.list_event_log_types(db)
    return [
        EventLogTypeResponse(
            id=t.id,
            key=t.key,
            name=t.name,
            log_schema=t.schema,
            icon_label=t.icon_label,
            position=t.position,
        )
        for t in log_types
    ]


@router.post(
    "/event-log-types/{event_log_type_id}/entries",
    response_model=EventEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_event_entry(
    organization_id: uuid.UUID,
    event_log_type_id: uuid.UUID,
    payload: EventEntryCreateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: AnyMember,
) -> EventEntryResponse:
    entry = await event_entry_service.record_event_entry(
        db,
        organization_id=organization_id,
        event_log_type_id=event_log_type_id,
        entry_date=payload.entry_date,
        responsible_user_id=current_user.id,
        payload=payload.payload,
        performed_by_user_id=payload.performed_by_user_id,
    )
    return _entry_response(entry)


@router.get("/event-log-types/{event_log_type_id}/entries", response_model=list[EventEntryResponse])
async def list_event_entries(
    organization_id: uuid.UUID, event_log_type_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[EventEntryResponse]:
    entries = await event_entry_service.list_event_entries(
        db, organization_id=organization_id, event_log_type_id=event_log_type_id
    )
    return [_entry_response(e) for e in entries]


@router.delete("/event-entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_entry(
    organization_id: uuid.UUID, entry_id: uuid.UUID, db: DbSession, _: AnyMember
) -> None:
    await event_entry_service.soft_delete_event_entry(
        db, organization_id=organization_id, entry_id=entry_id
    )
