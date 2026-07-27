import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import Organization


class OrganizationNotFoundError(NotFoundError):
    code = "organization_not_found"
    message = "Organization not found"


async def get_organization_timezone(db: AsyncSession, organization_id: uuid.UUID) -> str:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise OrganizationNotFoundError
    return organization.timezone
