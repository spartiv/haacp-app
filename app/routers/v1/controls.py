import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_membership
from app.core.errors import AppError
from app.db.session import get_db_session
from app.models import ControlAnswer, ControlPeriod, ControlRecord, Membership, MembershipRole, User
from app.schemas.control import (
    ControlAnswerResponse,
    ControlChecklistItemCreateRequest,
    ControlChecklistItemResponse,
    ControlChecklistItemUpdateRequest,
    ControlRecordHistoryResponse,
    ControlRecordResponse,
    ControlRecordUpsertRequest,
)
from app.services import control_checklist_service, control_record_service

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
                control_checklist_item_id=a.control_checklist_item_id, answer=a.answer
            )
            for a in answers
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
        db, organization_id=organization_id, period=period, label=payload.label
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
    item = await control_checklist_service.update_control_checklist_item(
        db, organization_id=organization_id, item_id=item_id, label=payload.label
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
    try:
        record = await control_record_service.upsert_current_control(
            db,
            organization_id=organization_id,
            period=period,
            signatory_user_id=current_user.id,
            answers={a.control_checklist_item_id: a.answer for a in payload.answers},
            period_date=payload.period_date,
            note=payload.note,
        )
    except control_record_service.ChecklistMismatchError as exc:
        raise AppError(
            422,
            "checklist_mismatch",
            "Answers must cover exactly the organization's current checklist items",
        ) from exc
    except control_record_service.FuturePeriodDateError as exc:
        raise AppError(
            422, "future_period_date", "Cannot record a control for a future date"
        ) from exc
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
    try:
        record = await control_record_service.edit_control_record(
            db,
            organization_id=organization_id,
            record_id=record_id,
            edited_by_user_id=current_user.id,
            answers={a.control_checklist_item_id: a.answer for a in payload.answers},
            note=payload.note,
        )
    except control_record_service.ChecklistMismatchError as exc:
        raise AppError(
            422,
            "checklist_mismatch",
            "Answers must cover exactly the organization's current checklist items",
        ) from exc
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
