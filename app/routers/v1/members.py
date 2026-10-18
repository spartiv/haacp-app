import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_membership
from app.db.session import get_db_session
from app.models import Membership
from app.schemas.member import MemberResponse
from app.services import organization_service

router = APIRouter(prefix="/organizations/{organization_id}", tags=["members"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AnyMember = Annotated[Membership, Depends(require_membership())]


@router.get("/members", response_model=list[MemberResponse])
async def list_members(
    organization_id: uuid.UUID, db: DbSession, _: AnyMember
) -> list[MemberResponse]:
    """The team: active members first, then removed ones (kept so past records
    can still show who did the work). Use the active ones for "performed by"
    pickers on shared devices."""
    members = await organization_service.list_members(db, organization_id=organization_id)
    return [
        MemberResponse(
            user_id=m.user_id, full_name=m.full_name, role=m.role, title=m.title, status=m.status
        )
        for m in members
    ]
