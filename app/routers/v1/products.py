import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_membership
from app.core.errors import AppError
from app.db.session import get_db_session
from app.models import Batch, BatchAnswer, Membership, MembershipRole, User
from app.schemas.product import (
    BatchAnswerResponse,
    BatchCreateRequest,
    BatchHistoryResponse,
    BatchResponse,
    BatchUpdateRequest,
    ChecklistItemCreateRequest,
    ChecklistItemResponse,
    ChecklistItemUpdateRequest,
    ProductCreateRequest,
    ProductResponse,
)
from app.services import batch_service, product_service

router = APIRouter(prefix="/organizations/{organization_id}", tags=["products"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AnyMember = Annotated[Membership, Depends(require_membership())]
ManagerOrOwner = Annotated[
    Membership, Depends(require_membership(MembershipRole.OWNER, MembershipRole.MANAGER))
]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _batch_response(batch: Batch, answers: list[BatchAnswer]) -> BatchResponse:
    return BatchResponse(
        id=batch.id,
        product_id=batch.product_id,
        number=batch.number,
        name=batch.name,
        production_date=batch.production_date,
        has_deviation=batch.has_deviation,
        deviation_note=batch.deviation_note,
        corrective_action=batch.corrective_action,
        signatory_user_id=batch.signatory_user_id,
        answers=[
            BatchAnswerResponse(checklist_item_id=a.checklist_item_id, answer=a.answer)
            for a in answers
        ],
    )


# ---- Products ----


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    organization_id: uuid.UUID, payload: ProductCreateRequest, db: DbSession, _: ManagerOrOwner
) -> ProductResponse:
    product = await product_service.create_product(
        db, organization_id=organization_id, name=payload.name
    )
    return ProductResponse.model_validate(product)


@router.get("/products", response_model=list[ProductResponse])
async def list_products(
    organization_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[ProductResponse]:
    products = await product_service.list_products(db, organization_id=organization_id)
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    organization_id: uuid.UUID, product_id: uuid.UUID, db: DbSession, _: AnyMember
) -> ProductResponse:
    product = await product_service.get_product(
        db, organization_id=organization_id, product_id=product_id
    )
    return ProductResponse.model_validate(product)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    organization_id: uuid.UUID, product_id: uuid.UUID, db: DbSession, _: ManagerOrOwner
) -> None:
    await product_service.soft_delete_product(
        db, organization_id=organization_id, product_id=product_id
    )


# ---- Checklist items ----


@router.get("/products/{product_id}/checklist-items", response_model=list[ChecklistItemResponse])
async def list_checklist_items(
    organization_id: uuid.UUID, product_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[ChecklistItemResponse]:
    items = await product_service.list_checklist_items(
        db, organization_id=organization_id, product_id=product_id
    )
    return [ChecklistItemResponse.model_validate(i) for i in items]


@router.post(
    "/products/{product_id}/checklist-items",
    response_model=ChecklistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_checklist_item(
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: ChecklistItemCreateRequest,
    db: DbSession,
    _: ManagerOrOwner,
) -> ChecklistItemResponse:
    item = await product_service.add_checklist_item(
        db, organization_id=organization_id, product_id=product_id, label=payload.label
    )
    return ChecklistItemResponse.model_validate(item)


@router.patch(
    "/products/{product_id}/checklist-items/{item_id}", response_model=ChecklistItemResponse
)
async def update_checklist_item(
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: ChecklistItemUpdateRequest,
    db: DbSession,
    _: ManagerOrOwner,
) -> ChecklistItemResponse:
    item = await product_service.update_checklist_item(
        db,
        organization_id=organization_id,
        product_id=product_id,
        item_id=item_id,
        label=payload.label,
    )
    return ChecklistItemResponse.model_validate(item)


@router.delete(
    "/products/{product_id}/checklist-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_checklist_item(
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    item_id: uuid.UUID,
    db: DbSession,
    _: ManagerOrOwner,
) -> None:
    await product_service.remove_checklist_item(
        db, organization_id=organization_id, product_id=product_id, item_id=item_id
    )


# ---- Batches ----


@router.post(
    "/products/{product_id}/batches",
    response_model=BatchResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_batch(
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: BatchCreateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: AnyMember,
) -> BatchResponse:
    try:
        batch = await batch_service.record_batch(
            db,
            organization_id=organization_id,
            product_id=product_id,
            number=payload.number,
            name=payload.name,
            production_date=payload.production_date,
            answers={a.checklist_item_id: a.answer for a in payload.answers},
            deviation_note=payload.deviation_note,
            corrective_action=payload.corrective_action,
            signatory_user_id=current_user.id,
        )
    except batch_service.ChecklistMismatchError as exc:
        raise AppError(
            422,
            "checklist_mismatch",
            "Answers must cover exactly the product's current checklist items",
        ) from exc

    answers = await batch_service.list_batch_answers(db, batch_id=batch.id)
    return _batch_response(batch, answers)


@router.get("/products/{product_id}/batches", response_model=list[BatchResponse])
async def list_product_batches(
    organization_id: uuid.UUID, product_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[BatchResponse]:
    batches = await batch_service.list_batches(
        db, organization_id=organization_id, product_id=product_id
    )
    answers_by_batch_id = await batch_service.list_batch_answers_by_batch_ids(
        db, batch_ids=[batch.id for batch in batches]
    )
    return [_batch_response(batch, answers_by_batch_id[batch.id]) for batch in batches]


@router.get("/batches/{batch_id}", response_model=BatchResponse)
async def get_batch(
    organization_id: uuid.UUID, batch_id: uuid.UUID, db: DbSession, _: AnyMember
) -> BatchResponse:
    batch = await batch_service.get_batch(db, organization_id=organization_id, batch_id=batch_id)
    answers = await batch_service.list_batch_answers(db, batch_id=batch.id)
    return _batch_response(batch, answers)


@router.patch("/batches/{batch_id}", response_model=BatchResponse)
async def edit_batch(
    organization_id: uuid.UUID,
    batch_id: uuid.UUID,
    payload: BatchUpdateRequest,
    db: DbSession,
    current_user: CurrentUser,
    _: AnyMember,
) -> BatchResponse:
    try:
        batch = await batch_service.edit_batch(
            db,
            organization_id=organization_id,
            batch_id=batch_id,
            edited_by_user_id=current_user.id,
            number=payload.number,
            name=payload.name,
            production_date=payload.production_date,
            answers=(
                {a.checklist_item_id: a.answer for a in payload.answers}
                if payload.answers is not None
                else None
            ),
            deviation_note=payload.deviation_note,
            corrective_action=payload.corrective_action,
        )
    except batch_service.ChecklistMismatchError as exc:
        raise AppError(
            422,
            "checklist_mismatch",
            "Answers must cover exactly the product's current checklist items",
        ) from exc

    answers = await batch_service.list_batch_answers(db, batch_id=batch.id)
    return _batch_response(batch, answers)


@router.delete("/batches/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_batch(
    organization_id: uuid.UUID, batch_id: uuid.UUID, db: DbSession, _: AnyMember
) -> None:
    await batch_service.soft_delete_batch(db, organization_id=organization_id, batch_id=batch_id)


@router.get("/batches/{batch_id}/history", response_model=list[BatchHistoryResponse])
async def get_batch_history(
    organization_id: uuid.UUID, batch_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[BatchHistoryResponse]:
    history = await batch_service.get_batch_history(
        db, organization_id=organization_id, batch_id=batch_id
    )
    return [BatchHistoryResponse.model_validate(h) for h in history]
