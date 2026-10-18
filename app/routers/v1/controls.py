import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_membership
from app.core.errors import AppError
from app.db.session import get_db_session
from app.models import (
    ControlAnswer,
    ControlItemStatus,
    ControlPeriod,
    ControlRecord,
    Membership,
    MembershipRole,
    User,
)
from app.schemas.control import (
    AuditEventPageResponse,
    AuditEventResponse,
    ControlAnswerResponse,
    ControlChecklistItemCreateRequest,
    ControlChecklistItemResponse,
    ControlChecklistItemUpdateRequest,
    ControlRecordHistoryResponse,
    ControlRecordResponse,
    ControlRecordUpsertRequest,
    ControlSheetResponse,
    ItemCheckRequest,
    SheetItemResponse,
    UserRefResponse,
)
from app.services import control_checklist_service, control_record_service, control_sheet_service
from app.services.control_checklist_service import NumericConfig
from app.services.control_sheet_service import ControlSheet, UserRef

router = APIRouter(prefix="/organizations/{organization_id}", tags=["controls"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AnyMember = Annotated[Membership, Depends(require_membership())]
ManagerOrOwner = Annotated[
    Membership, Depends(require_membership(MembershipRole.OWNER, MembershipRole.MANAGER))
]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _record_response(record: ControlRecord, answers: list[ControlAnswer]) -> ControlRecordResponse:
    return ControlRecordResponse(
        id=record.id,
        period=record.period,
        period_date=record.period_date,
        signatory_user_id=record.signatory_user_id,
        has_deviation=record.has_deviation,
        note=record.note,
        answers=[
            ControlAnswerResponse(
                control_checklist_item_id=a.control_checklist_item_id,
                answer=a.answer,
                numeric_value=_float(a.numeric_value),
            )
            for a in answers
        ],
    )


def _float(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def _user_ref(user: UserRef | None) -> UserRefResponse | None:
    return UserRefResponse(id=user.id, full_name=user.full_name) if user is not None else None


def _sheet_response(sheet: ControlSheet) -> ControlSheetResponse:
    record = sheet.record
    return ControlSheetResponse(
        record_id=record.id if record else None,
        period=sheet.period,
        period_date=sheet.period_date,
        status=record.status if record else None,
        has_deviation=record.has_deviation if record else False,
        note=record.note if record else None,
        submitted_at=record.submitted_at if record else None,
        submitted_by=_user_ref(sheet.submitted_by),
        items=[
            SheetItemResponse(
                control_checklist_item_id=item.item_id,
                label=item.label,
                position=item.position,
                item_type=item.item_type,
                unit=item.unit,
                min_value=_float(item.min_value),
                max_value=_float(item.max_value),
                value=_float(item.value),
                status=item.status,
                corrective_action=item.corrective_action,
                checked_by=_user_ref(item.checked_by),
                performed_by=_user_ref(item.performed_by),
                checked_at=item.checked_at,
            )
            for item in sheet.items
        ],
    )


# ---- Checklist items ----


@router.get("/controls/{period}/checklist-items", response_model=list[ControlChecklistItemResponse])
async def list_control_checklist_items(
    organization_id: uuid.UUID, period: ControlPeriod, db: DbSession, _: AnyMember
) -> list[ControlChecklistItemResponse]:
    items = await control_checklist_service.list_control_checklist_items(
        db, organization_id=organization_id, period=period
    )
    return [ControlChecklistItemResponse.model_validate(i) for i in items]


@router.post(
    "/controls/{period}/checklist-items",
    response_model=ControlChecklistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_control_checklist_item(
    organization_id: uuid.UUID,
    period: ControlPeriod,
    payload: ControlChecklistItemCreateRequest,
    db: DbSession,
    _: ManagerOrOwner,
) -> ControlChecklistItemResponse:
    item = await control_checklist_service.add_control_checklist_item(
        db,
        organization_id=organization_id,
        period=period,
        label=payload.label,
        item_type=payload.item_type,
        config=NumericConfig(
            unit=payload.unit, min_value=payload.min_value, max_value=payload.max_value
        ),
    )
    return ControlChecklistItemResponse.model_validate(item)


@router.patch(
    "/controls/{period}/checklist-items/{item_id}", response_model=ControlChecklistItemResponse
)
async def update_control_checklist_item(
    organization_id: uuid.UUID,
    period: ControlPeriod,
    item_id: uuid.UUID,
    payload: ControlChecklistItemUpdateRequest,
    db: DbSession,
    _: ManagerOrOwner,
) -> ControlChecklistItemResponse:
    current = await control_checklist_service.get_control_checklist_item(
        db, organization_id=organization_id, item_id=item_id
    )
    sent = payload.model_fields_set
    config = None
    if sent & {"unit", "min_value", "max_value"}:
        # Merge the partial update onto the current range; the service validates the result.
        config = NumericConfig(
            unit=payload.unit if "unit" in sent else current.unit,
            min_value=payload.min_value if "min_value" in sent else current.min_value,
            max_value=payload.max_value if "max_value" in sent else current.max_value,
        )
    item = await control_checklist_service.update_control_checklist_item(
        db,
        organization_id=organization_id,
        item_id=item_id,
        label=payload.label if payload.label is not None else current.label,
        config=config,
    )
    return ControlChecklistItemResponse.model_validate(item)


@router.delete(
    "/controls/{period}/checklist-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_control_checklist_item(
    organization_id: uuid.UUID,
    period: ControlPeriod,
    item_id: uuid.UUID,
    db: DbSession,
    _: ManagerOrOwner,
) -> None:
    await control_checklist_service.remove_control_checklist_item(
        db, organization_id=organization_id, item_id=item_id
    )


# ---- Current period record ----


@router.get("/controls/{period}/current", response_model=ControlRecordResponse)
async def get_current_control(
    organization_id: uuid.UUID, period: ControlPeriod, db: DbSession, _: AnyMember
) -> ControlRecordResponse:
    record = await control_record_service.get_current_control(
        db, organization_id=organization_id, period=period
    )
    if record is None:
        raise AppError(
            404, "control_record_not_filled", "Current period has not been filled in yet"
        )
    answers = await control_record_service.list_control_answers(db, control_record_id=record.id)
    return _record_response(record, answers)


@router.put("/controls/{period}/current", response_model=ControlRecordResponse)
async def upsert_current_control(
    organization_id: uuid.UUID,
    period: ControlPeriod,
    payload: ControlRecordUpsertRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: AnyMember,
) -> ControlRecordResponse:
    record = await control_record_service.upsert_current_control(
        db,
        organization_id=organization_id,
        period=period,
        signatory_user_id=current_user.id,
        answers={a.control_checklist_item_id: a.answer for a in payload.answers},
        period_date=payload.period_date,
        note=payload.note,
    )
    answers = await control_record_service.list_control_answers(db, control_record_id=record.id)
    return _record_response(record, answers)


@router.get("/controls/{period}/records", response_model=list[ControlRecordResponse])
async def list_control_records(
    organization_id: uuid.UUID, period: ControlPeriod, db: DbSession, _: AnyMember
) -> list[ControlRecordResponse]:
    records = await control_record_service.list_control_records(
        db, organization_id=organization_id, period=period
    )
    answers_by_record_id = await control_record_service.list_control_answers_by_record_ids(
        db, control_record_ids=[record.id for record in records]
    )
    return [_record_response(record, answers_by_record_id[record.id]) for record in records]


# ---- Individual records (by id, regardless of period) ----


@router.get("/control-records/{record_id}", response_model=ControlRecordResponse)
async def get_control_record(
    organization_id: uuid.UUID, record_id: uuid.UUID, db: DbSession, _: AnyMember
) -> ControlRecordResponse:
    record = await control_record_service.get_control_record(
        db, organization_id=organization_id, record_id=record_id
    )
    answers = await control_record_service.list_control_answers(db, control_record_id=record.id)
    return _record_response(record, answers)


@router.patch("/control-records/{record_id}", response_model=ControlRecordResponse)
async def edit_control_record(
    organization_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: ControlRecordUpsertRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: AnyMember,
) -> ControlRecordResponse:
    record = await control_record_service.edit_control_record(
        db,
        organization_id=organization_id,
        record_id=record_id,
        edited_by_user_id=current_user.id,
        answers={a.control_checklist_item_id: a.answer for a in payload.answers},
        note=payload.note,
    )
    answers = await control_record_service.list_control_answers(db, control_record_id=record.id)
    return _record_response(record, answers)


@router.delete("/control-records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_control_record(
    organization_id: uuid.UUID, record_id: uuid.UUID, db: DbSession, _: AnyMember
) -> None:
    await control_record_service.soft_delete_control_record(
        db, organization_id=organization_id, record_id=record_id
    )


@router.get(
    "/control-records/{record_id}/history", response_model=list[ControlRecordHistoryResponse]
)
async def get_control_record_history(
    organization_id: uuid.UUID, record_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[ControlRecordHistoryResponse]:
    history = await control_record_service.get_control_record_history(
        db, organization_id=organization_id, record_id=record_id
    )
    return [ControlRecordHistoryResponse.model_validate(h) for h in history]


# ---- Per-item sheet workflow + audit log ----


@router.get("/controls/{period}/sheet", response_model=ControlSheetResponse)
async def get_control_sheet(
    organization_id: uuid.UUID,
    period: ControlPeriod,
    db: DbSession,
    _: AnyMember,
    period_date: Annotated[
        date | None,
        Query(alias="date", description="YYYY-MM-DD. Defaults to the current period."),
    ] = None,
) -> ControlSheetResponse:
    sheet = await control_sheet_service.get_sheet(
        db, organization_id=organization_id, period=period, period_date=period_date
    )
    return _sheet_response(sheet)


@router.post("/controls/{period}/items/{item_id}/check", response_model=ControlSheetResponse)
async def check_control_item(
    organization_id: uuid.UUID,
    period: ControlPeriod,
    item_id: uuid.UUID,
    payload: ItemCheckRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: AnyMember,
) -> ControlSheetResponse:
    sheet = await control_sheet_service.check_item(
        db,
        organization_id=organization_id,
        period=period,
        item_id=item_id,
        status=ControlItemStatus(payload.status) if payload.status is not None else None,
        value=payload.value,
        performed_by_user_id=payload.performed_by_user_id,
        corrective_action=payload.corrective_action,
        amendment_reason=payload.amendment_reason,
        period_date=payload.period_date,
        actor_user_id=current_user.id,
    )
    return _sheet_response(sheet)


@router.post("/control-records/{record_id}/submit", response_model=ControlSheetResponse)
async def submit_control_record(
    organization_id: uuid.UUID,
    record_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    _: AnyMember,
) -> ControlSheetResponse:
    sheet = await control_sheet_service.submit_record(
        db, organization_id=organization_id, record_id=record_id, actor_user_id=current_user.id
    )
    return _sheet_response(sheet)


@router.get("/control-records/{record_id}/audit-events", response_model=AuditEventPageResponse)
async def list_control_audit_events(
    organization_id: uuid.UUID,
    record_id: uuid.UUID,
    db: DbSession,
    _: AnyMember,
    cursor: Annotated[str | None, Query(description="`next_cursor` from the previous page")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AuditEventPageResponse:
    page = await control_sheet_service.list_audit_events(
        db, organization_id=organization_id, record_id=record_id, cursor=cursor, limit=limit
    )
    return AuditEventPageResponse(
        items=[
            AuditEventResponse(
                id=view.event.id,
                seq=view.event.seq,
                event_type=view.event.event_type,
                control_checklist_item_id=view.event.control_checklist_item_id,
                item_label=view.item_label,
                item_unit=view.item_unit,
                numeric_value=_float(view.event.numeric_value),
                previous_status=view.event.previous_status,
                new_status=view.event.new_status,
                corrective_action=view.event.corrective_action,
                amendment_reason=view.event.amendment_reason,
                actor=UserRefResponse(id=view.actor.id, full_name=view.actor.full_name),
                performed_by=UserRefResponse(
                    id=view.performed_by.id, full_name=view.performed_by.full_name
                ),
                created_at=view.event.created_at,
            )
            for view in page.events
        ],
        next_cursor=page.next_cursor,
    )
