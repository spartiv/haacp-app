import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import DomainError, NotFoundError
from app.core.security import hash_password, hash_token
from app.models import (
    Invite,
    InviteStatus,
    Membership,
    MembershipRole,
    MembershipStatus,
    Organization,
    User,
)
from app.services.auth_service import AuthResult, issue_token_pair, normalize_email
from app.services.email_sender import EmailSender
from app.services.organization_service import OrganizationNotFoundError

logger = logging.getLogger(__name__)


class AlreadyMemberError(DomainError):
    status_code = 409
    code = "already_member"
    message = "This account is already a member of the organization"


class InviteAlreadyPendingError(DomainError):
    status_code = 409
    code = "invite_already_pending"
    message = "An invite is already pending for this email"


class InviteNotFoundError(NotFoundError):
    code = "invite_not_found"
    message = "Invite not found"


class InviteExpiredError(DomainError):
    status_code = 410
    code = "invite_expired"
    message = "This invite has expired"


class InviteAlreadyAcceptedError(DomainError):
    status_code = 410
    code = "invite_already_accepted"
    message = "This invite was already used"


class AccountExistsRequiresLoginError(DomainError):
    status_code = 409
    code = "account_exists_requires_login"
    message = "An account with this email already exists; log in and retry"


class SignupFieldsRequiredError(DomainError):
    status_code = 422
    code = "signup_fields_required"
    message = "password and full_name are required for a new account"


async def create_invite(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    invited_by_user_id: uuid.UUID,
    email: str,
    role: MembershipRole,
    email_sender: EmailSender,
) -> Invite:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise OrganizationNotFoundError

    normalized_email = normalize_email(email)

    already_member = await db.execute(
        select(Membership)
        .join(User, User.id == Membership.user_id)
        .where(
            User.email == normalized_email,
            Membership.organization_id == organization_id,
            Membership.status == MembershipStatus.ACTIVE,
        )
    )
    if already_member.scalar_one_or_none() is not None:
        raise AlreadyMemberError("This email already belongs to the organization")

    pending_invite = await db.execute(
        select(Invite).where(
            Invite.organization_id == organization_id,
            Invite.email == normalized_email,
            Invite.status == InviteStatus.PENDING,
            Invite.expires_at > datetime.now(UTC),
        )
    )
    if pending_invite.scalar_one_or_none() is not None:
        raise InviteAlreadyPendingError

    settings = get_settings()
    raw_token = secrets.token_urlsafe(32)
    invite = Invite(
        organization_id=organization_id,
        email=normalized_email,
        role=role,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.invite_token_expire_days),
        invited_by_user_id=invited_by_user_id,
    )
    db.add(invite)
    await db.flush()

    await email_sender.send_invite(
        to_email=normalized_email, organization_name=organization.name, role=role, token=raw_token
    )
    await db.commit()
    logger.info(
        "Invite created: organization_id=%s role=%s invited_by_user_id=%s",
        organization_id,
        role.value,
        invited_by_user_id,
    )
    return invite


async def _load_pending_invite(db: AsyncSession, token: str) -> Invite:
    result = await db.execute(select(Invite).where(Invite.token_hash == hash_token(token)))
    invite = result.scalar_one_or_none()
    if invite is None:
        raise InviteNotFoundError
    if invite.status == InviteStatus.ACCEPTED:
        raise InviteAlreadyAcceptedError
    if invite.expires_at < datetime.now(UTC):
        raise InviteExpiredError
    return invite


async def get_invite_preview(db: AsyncSession, *, token: str) -> tuple[Invite, Organization]:
    invite = await _load_pending_invite(db, token)
    organization = await db.get(Organization, invite.organization_id)
    if organization is None:
        raise OrganizationNotFoundError
    return invite, organization


async def accept_invite(
    db: AsyncSession,
    *,
    token: str,
    current_user: User | None,
    password: str | None,
    full_name: str | None,
) -> AuthResult:
    invite = await _load_pending_invite(db, token)

    existing_user_result = await db.execute(select(User).where(User.email == invite.email))
    existing_user = existing_user_result.scalar_one_or_none()

    target_user: User
    if existing_user is not None:
        if current_user is None or current_user.id != existing_user.id:
            raise AccountExistsRequiresLoginError
        target_user = existing_user
    else:
        if not password or not full_name:
            raise SignupFieldsRequiredError
        target_user = User(
            email=invite.email, password_hash=await hash_password(password), full_name=full_name
        )
        db.add(target_user)
        await db.flush()

    membership_result = await db.execute(
        select(Membership).where(
            Membership.user_id == target_user.id,
            Membership.organization_id == invite.organization_id,
        )
    )
    membership = membership_result.scalar_one_or_none()
    if membership is not None and membership.status == MembershipStatus.ACTIVE:
        raise AlreadyMemberError
    if membership is not None:
        membership.status = MembershipStatus.ACTIVE
        membership.role = invite.role
    else:
        db.add(
            Membership(
                user_id=target_user.id,
                organization_id=invite.organization_id,
                role=invite.role,
                status=MembershipStatus.ACTIVE,
            )
        )

    invite.status = InviteStatus.ACCEPTED
    invite.accepted_at = datetime.now(UTC)
    invite.accepted_by_user_id = target_user.id

    access_token, refresh_token = await issue_token_pair(db, target_user)
    await db.commit()
    logger.info(
        "Invite accepted: user_id=%s organization_id=%s", target_user.id, invite.organization_id
    )
    return AuthResult(
        user=target_user,
        access_token=access_token,
        refresh_token=refresh_token,
        organization_id=invite.organization_id,
    )
