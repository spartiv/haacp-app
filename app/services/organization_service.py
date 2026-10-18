import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError, NotFoundError
from app.models import Membership, MembershipRole, MembershipStatus, Organization, User


class OrganizationNotFoundError(NotFoundError):
    code = "organization_not_found"
    message = "Organization not found"


class InvalidPerformerError(DomainError):
    status_code = 422
    code = "invalid_performer"
    message = "The selected performer is not an active member of this organization"


async def get_organization_timezone(db: AsyncSession, organization_id: uuid.UUID) -> str:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise OrganizationNotFoundError
    return organization.timezone


@dataclass(frozen=True)
class UserOrganization:
    organization_id: uuid.UUID
    name: str
    role: MembershipRole
    title: str | None


async def list_user_organizations(
    db: AsyncSession, *, user_id: uuid.UUID
) -> list[UserOrganization]:
    """Organizations where the user has an active membership, sorted by name."""
    result = await db.execute(
        select(Organization.id, Organization.name, Membership.role, Membership.title)
        .join(Membership, Membership.organization_id == Organization.id)
        .where(Membership.user_id == user_id, Membership.status == MembershipStatus.ACTIVE)
        .order_by(Organization.name, Organization.id)
    )
    return [
        UserOrganization(organization_id=org_id, name=name, role=role, title=title)
        for org_id, name, role, title in result.all()
    ]


@dataclass(frozen=True)
class OrganizationMember:
    user_id: uuid.UUID
    full_name: str
    role: MembershipRole
    title: str | None
    status: MembershipStatus


async def list_members(db: AsyncSession, *, organization_id: uuid.UUID) -> list[OrganizationMember]:
    """Everyone who is or was a member: active first, then by name. Removed
    members are included so past records can still show who did the work."""
    result = await db.execute(
        select(User.id, User.full_name, Membership.role, Membership.title, Membership.status)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.organization_id == organization_id)
        .order_by(Membership.status != MembershipStatus.ACTIVE, User.full_name, User.id)
    )
    return [
        OrganizationMember(user_id=uid, full_name=name, role=role, title=title, status=status)
        for uid, name, role, title, status in result.all()
    ]


async def resolve_performer(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    performer_user_id: uuid.UUID | None,
    actor_user_id: uuid.UUID,
) -> uuid.UUID:
    """Who physically did the work. Defaults to the signed-in account; a chosen
    performer must be an active member of the same organization."""
    if performer_user_id is None or performer_user_id == actor_user_id:
        return actor_user_id
    result = await db.execute(
        select(Membership.id).where(
            Membership.organization_id == organization_id,
            Membership.user_id == performer_user_id,
            Membership.status == MembershipStatus.ACTIVE,
        )
    )
    if result.scalar_one_or_none() is None:
        raise InvalidPerformerError
    return performer_user_id
