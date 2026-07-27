import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_optional_current_user, require_membership
from app.core.errors import AppError
from app.db.session import get_db_session
from app.models import Membership, MembershipRole, User
from app.schemas.auth import AuthResponse, TokenResponse, UserResponse
from app.schemas.invite import (
    InviteAcceptRequest,
    InviteCreateRequest,
    InvitePreviewResponse,
    InviteResponse,
)
from app.services import invite_service
from app.services.email_sender import EmailSender, get_email_sender

router = APIRouter(tags=["invites"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post(
    "/organizations/{organization_id}/invites",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invite(
    organization_id: uuid.UUID,
    payload: InviteCreateRequest,
    db: DbSession,
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
    membership: Annotated[
        Membership, Depends(require_membership(MembershipRole.OWNER, MembershipRole.MANAGER))
    ],
) -> InviteResponse:
    try:
        invite = await invite_service.create_invite(
            db,
            organization_id=organization_id,
            invited_by_user_id=membership.user_id,
            email=payload.email,
            role=payload.role,
            email_sender=email_sender,
        )
    except invite_service.AlreadyMemberError as exc:
        raise AppError(
            409, "already_member", "This email already belongs to the organization"
        ) from exc
    except invite_service.InviteAlreadyPendingError as exc:
        raise AppError(
            409, "invite_already_pending", "An invite is already pending for this email"
        ) from exc

    return InviteResponse.model_validate(invite)


@router.get("/invites/{token}", response_model=InvitePreviewResponse)
async def preview_invite(token: str, db: DbSession) -> InvitePreviewResponse:
    try:
        invite, organization = await invite_service.get_invite_preview(db, token=token)
    except invite_service.InviteExpiredError as exc:
        raise AppError(410, "invite_expired", "This invite has expired") from exc
    except invite_service.InviteAlreadyAcceptedError as exc:
        raise AppError(410, "invite_already_accepted", "This invite was already used") from exc

    return InvitePreviewResponse(
        organization_name=organization.name,
        email=invite.email,
        role=invite.role,
        expires_at=invite.expires_at,
    )


@router.post("/invites/{token}/accept", response_model=AuthResponse)
async def accept_invite(
    token: str,
    payload: InviteAcceptRequest,
    db: DbSession,
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> AuthResponse:
    try:
        result = await invite_service.accept_invite(
            db,
            token=token,
            current_user=current_user,
            password=payload.password,
            full_name=payload.full_name,
        )
    except invite_service.InviteExpiredError as exc:
        raise AppError(410, "invite_expired", "This invite has expired") from exc
    except invite_service.InviteAlreadyAcceptedError as exc:
        raise AppError(410, "invite_already_accepted", "This invite was already used") from exc
    except invite_service.AccountExistsRequiresLoginError as exc:
        raise AppError(
            409,
            "account_exists_requires_login",
            "An account with this email already exists; log in and retry",
        ) from exc
    except invite_service.SignupFieldsRequiredError as exc:
        raise AppError(
            422, "signup_fields_required", "password and full_name are required for a new account"
        ) from exc
    except invite_service.AlreadyMemberError as exc:
        raise AppError(
            409, "already_member", "This account is already a member of the organization"
        ) from exc

    return AuthResponse(
        user=UserResponse.model_validate(result.user),
        tokens=TokenResponse(access_token=result.access_token, refresh_token=result.refresh_token),
        organization_id=result.organization_id,
    )
