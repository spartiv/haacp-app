from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models import User
from app.schemas.me import MyOrganizationResponse
from app.services import organization_service

router = APIRouter(prefix="/me", tags=["me"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/organizations", response_model=list[MyOrganizationResponse])
async def list_my_organizations(db: DbSession, user: CurrentUser) -> list[MyOrganizationResponse]:
    """Organizations the caller is an active member of, sorted by name.
    Clients call this after login to pick the active organization."""
    organizations = await organization_service.list_user_organizations(db, user_id=user.id)
    return [
        MyOrganizationResponse(
            organization_id=org.organization_id,
            name=org.name,
            role=org.role.value,
            title=org.title,
        )
        for org in organizations
    ]
