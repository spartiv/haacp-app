import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_membership
from app.db.session import get_db_session
from app.models import Membership, MembershipRole
from app.schemas.allergen import AllergenPresenceUpdateRequest, AllergenStatusResponse
from app.schemas.attachment import AttachDocumentRequest
from app.schemas.chemical import ChemicalCreateRequest, ChemicalResponse, ChemicalUpdateRequest
from app.schemas.medical_check import (
    MedicalCheckCreateRequest,
    MedicalCheckResponse,
    MedicalCheckUpdateRequest,
)
from app.schemas.waste_type import WasteTypeCreateRequest, WasteTypeResponse, WasteTypeUpdateRequest
from app.services import (
    allergen_service,
    chemical_service,
    medical_check_service,
    waste_type_service,
)
from app.services.storage import StorageBackend, get_storage_backend

router = APIRouter(prefix="/organizations/{organization_id}", tags=["directories"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AnyMember = Annotated[Membership, Depends(require_membership())]
ManagerOrOwner = Annotated[
    Membership, Depends(require_membership(MembershipRole.OWNER, MembershipRole.MANAGER))
]
Storage = Annotated[StorageBackend, Depends(get_storage_backend)]


# ---- Chemicals ----


@router.post("/chemicals", response_model=ChemicalResponse, status_code=status.HTTP_201_CREATED)
async def create_chemical(
    organization_id: uuid.UUID, payload: ChemicalCreateRequest, db: DbSession, _: ManagerOrOwner
) -> ChemicalResponse:
    chemical = await chemical_service.create_chemical(
        db, organization_id=organization_id, name=payload.name, category=payload.category
    )
    return ChemicalResponse.model_validate(chemical)


@router.get("/chemicals", response_model=list[ChemicalResponse])
async def list_chemicals(
    organization_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[ChemicalResponse]:
    chemicals = await chemical_service.list_chemicals(db, organization_id=organization_id)
    return [ChemicalResponse.model_validate(c) for c in chemicals]


@router.patch("/chemicals/{chemical_id}", response_model=ChemicalResponse)
async def update_chemical(
    organization_id: uuid.UUID,
    chemical_id: uuid.UUID,
    payload: ChemicalUpdateRequest,
    db: DbSession,
    _: ManagerOrOwner,
) -> ChemicalResponse:
    chemical = await chemical_service.update_chemical(
        db,
        organization_id=organization_id,
        chemical_id=chemical_id,
        name=payload.name,
        category=payload.category,
    )
    return ChemicalResponse.model_validate(chemical)


@router.delete("/chemicals/{chemical_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chemical(
    organization_id: uuid.UUID, chemical_id: uuid.UUID, db: DbSession, _: ManagerOrOwner
) -> None:
    await chemical_service.soft_delete_chemical(
        db, organization_id=organization_id, chemical_id=chemical_id
    )


@router.post("/chemicals/{chemical_id}/attachment", response_model=ChemicalResponse)
async def attach_chemical_document(
    organization_id: uuid.UUID,
    chemical_id: uuid.UUID,
    payload: AttachDocumentRequest,
    db: DbSession,
    storage: Storage,
    _: ManagerOrOwner,
) -> ChemicalResponse:
    chemical = await chemical_service.attach_document(
        db,
        organization_id=organization_id,
        chemical_id=chemical_id,
        attachment_id=payload.attachment_id,
        storage=storage,
    )
    return ChemicalResponse.model_validate(chemical)


@router.delete("/chemicals/{chemical_id}/attachment", response_model=ChemicalResponse)
async def detach_chemical_document(
    organization_id: uuid.UUID,
    chemical_id: uuid.UUID,
    db: DbSession,
    storage: Storage,
    _: ManagerOrOwner,
) -> ChemicalResponse:
    chemical = await chemical_service.detach_document(
        db, organization_id=organization_id, chemical_id=chemical_id, storage=storage
    )
    return ChemicalResponse.model_validate(chemical)


# ---- Waste types ----


@router.post("/waste-types", response_model=WasteTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_waste_type(
    organization_id: uuid.UUID, payload: WasteTypeCreateRequest, db: DbSession, _: ManagerOrOwner
) -> WasteTypeResponse:
    waste_type = await waste_type_service.create_waste_type(
        db,
        organization_id=organization_id,
        name=payload.name,
        disposal_method=payload.disposal_method,
    )
    return WasteTypeResponse.model_validate(waste_type)


@router.get("/waste-types", response_model=list[WasteTypeResponse])
async def list_waste_types(
    organization_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[WasteTypeResponse]:
    waste_types = await waste_type_service.list_waste_types(db, organization_id=organization_id)
    return [WasteTypeResponse.model_validate(w) for w in waste_types]


@router.patch("/waste-types/{waste_type_id}", response_model=WasteTypeResponse)
async def update_waste_type(
    organization_id: uuid.UUID,
    waste_type_id: uuid.UUID,
    payload: WasteTypeUpdateRequest,
    db: DbSession,
    _: ManagerOrOwner,
) -> WasteTypeResponse:
    waste_type = await waste_type_service.update_waste_type(
        db,
        organization_id=organization_id,
        waste_type_id=waste_type_id,
        name=payload.name,
        disposal_method=payload.disposal_method,
    )
    return WasteTypeResponse.model_validate(waste_type)


@router.delete("/waste-types/{waste_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_waste_type(
    organization_id: uuid.UUID, waste_type_id: uuid.UUID, db: DbSession, _: ManagerOrOwner
) -> None:
    await waste_type_service.soft_delete_waste_type(
        db, organization_id=organization_id, waste_type_id=waste_type_id
    )


# ---- Medical checks ----


@router.post(
    "/medical-checks", response_model=MedicalCheckResponse, status_code=status.HTTP_201_CREATED
)
async def create_medical_check(
    organization_id: uuid.UUID,
    payload: MedicalCheckCreateRequest,
    db: DbSession,
    _: ManagerOrOwner,
) -> MedicalCheckResponse:
    medical_check = await medical_check_service.create_medical_check(
        db,
        organization_id=organization_id,
        employee_name=payload.employee_name,
        next_check_date=payload.next_check_date,
    )
    return MedicalCheckResponse.model_validate(medical_check)


@router.get("/medical-checks", response_model=list[MedicalCheckResponse])
async def list_medical_checks(
    organization_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[MedicalCheckResponse]:
    medical_checks = await medical_check_service.list_medical_checks(
        db, organization_id=organization_id
    )
    return [MedicalCheckResponse.model_validate(m) for m in medical_checks]


@router.patch("/medical-checks/{medical_check_id}", response_model=MedicalCheckResponse)
async def update_medical_check(
    organization_id: uuid.UUID,
    medical_check_id: uuid.UUID,
    payload: MedicalCheckUpdateRequest,
    db: DbSession,
    _: ManagerOrOwner,
) -> MedicalCheckResponse:
    medical_check = await medical_check_service.update_medical_check(
        db,
        organization_id=organization_id,
        medical_check_id=medical_check_id,
        employee_name=payload.employee_name,
        next_check_date=payload.next_check_date,
    )
    return MedicalCheckResponse.model_validate(medical_check)


@router.delete("/medical-checks/{medical_check_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medical_check(
    organization_id: uuid.UUID, medical_check_id: uuid.UUID, db: DbSession, _: ManagerOrOwner
) -> None:
    await medical_check_service.soft_delete_medical_check(
        db, organization_id=organization_id, medical_check_id=medical_check_id
    )


# ---- Allergens ----


@router.get("/allergens", response_model=list[AllergenStatusResponse])
async def list_allergens(
    organization_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[AllergenStatusResponse]:
    rows = await allergen_service.list_allergen_statuses(db, organization_id=organization_id)
    return [
        AllergenStatusResponse(
            allergen_id=allergen.id,
            name=allergen.name,
            position=allergen.position,
            present=allergen_status.present,
        )
        for allergen, allergen_status in rows
    ]


@router.patch("/allergens/{allergen_id}", response_model=AllergenStatusResponse)
async def update_allergen_presence(
    organization_id: uuid.UUID,
    allergen_id: uuid.UUID,
    payload: AllergenPresenceUpdateRequest,
    db: DbSession,
    _: ManagerOrOwner,
) -> AllergenStatusResponse:
    allergen, status_row = await allergen_service.set_allergen_presence(
        db, organization_id=organization_id, allergen_id=allergen_id, present=payload.present
    )
    return AllergenStatusResponse(
        allergen_id=allergen.id,
        name=allergen.name,
        position=allergen.position,
        present=status_row.present,
    )
