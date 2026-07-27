import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_membership
from app.db.session import get_db_session
from app.models import Membership, MembershipRole
from app.schemas.attachment import AttachDocumentRequest
from app.schemas.equipment import EquipmentCreateRequest, EquipmentResponse, EquipmentUpdateRequest
from app.services import equipment_service
from app.services.storage import StorageBackend, get_storage_backend

router = APIRouter(prefix="/organizations/{organization_id}/equipment", tags=["equipment"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AnyMember = Annotated[Membership, Depends(require_membership())]
ManagerOrOwner = Annotated[
    Membership, Depends(require_membership(MembershipRole.OWNER, MembershipRole.MANAGER))
]
Storage = Annotated[StorageBackend, Depends(get_storage_backend)]


@router.post("", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    organization_id: uuid.UUID, payload: EquipmentCreateRequest, db: DbSession, _: ManagerOrOwner
) -> EquipmentResponse:
    equipment = await equipment_service.create_equipment(
        db,
        organization_id=organization_id,
        type=payload.type,
        name=payload.name,
        frequency=payload.frequency,
        amount=payload.amount,
        affects_product_safety=payload.affects_product_safety,
    )
    return EquipmentResponse.model_validate(equipment)


@router.get("", response_model=list[EquipmentResponse])
async def list_equipment(
    organization_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[EquipmentResponse]:
    equipment = await equipment_service.list_equipment(db, organization_id=organization_id)
    return [EquipmentResponse.model_validate(e) for e in equipment]


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    organization_id: uuid.UUID, equipment_id: uuid.UUID, db: DbSession, _: AnyMember
) -> EquipmentResponse:
    equipment = await equipment_service.get_equipment(
        db, organization_id=organization_id, equipment_id=equipment_id
    )
    return EquipmentResponse.model_validate(equipment)


@router.patch("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    payload: EquipmentUpdateRequest,
    db: DbSession,
    _: ManagerOrOwner,
) -> EquipmentResponse:
    equipment = await equipment_service.update_equipment(
        db,
        organization_id=organization_id,
        equipment_id=equipment_id,
        type=payload.type,
        name=payload.name,
        frequency=payload.frequency,
        amount=payload.amount,
        affects_product_safety=payload.affects_product_safety,
    )
    return EquipmentResponse.model_validate(equipment)


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(
    organization_id: uuid.UUID, equipment_id: uuid.UUID, db: DbSession, _: ManagerOrOwner
) -> None:
    await equipment_service.soft_delete_equipment(
        db, organization_id=organization_id, equipment_id=equipment_id
    )


@router.post("/{equipment_id}/attachment", response_model=EquipmentResponse)
async def attach_document(
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    payload: AttachDocumentRequest,
    db: DbSession,
    storage: Storage,
    _: ManagerOrOwner,
) -> EquipmentResponse:
    equipment = await equipment_service.attach_document(
        db,
        organization_id=organization_id,
        equipment_id=equipment_id,
        attachment_id=payload.attachment_id,
        storage=storage,
    )
    return EquipmentResponse.model_validate(equipment)


@router.delete("/{equipment_id}/attachment", response_model=EquipmentResponse)
async def detach_document(
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    db: DbSession,
    storage: Storage,
    _: ManagerOrOwner,
) -> EquipmentResponse:
    equipment = await equipment_service.detach_document(
        db, organization_id=organization_id, equipment_id=equipment_id, storage=storage
    )
    return EquipmentResponse.model_validate(equipment)
