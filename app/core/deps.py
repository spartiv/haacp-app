import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import InvalidTokenError, TokenType, decode_token
from app.db.session import get_db_session
from app.models import Membership, MembershipRole, MembershipStatus, User

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    if credentials is None:
        raise AppError(401, "unauthenticated", "Missing bearer token")

    try:
        decoded = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
    except InvalidTokenError as exc:
        raise AppError(401, "invalid_token", "Access token is invalid or expired") from exc

    user = await db.get(User, decoded.user_id)
    if user is None or not user.is_active:
        raise AppError(401, "invalid_token", "Access token is invalid or expired")

    return user


async def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User | None:
    """Like get_current_user, but a missing Authorization header means
    "anonymous" instead of raising. A present-but-invalid token still raises,
    since a client that supplied a bearer token presumably intended to
    authenticate."""
    if credentials is None:
        return None
    return await get_current_user(credentials=credentials, db=db)


def require_membership(
    *allowed_roles: MembershipRole,
) -> Callable[..., Coroutine[Any, Any, Membership]]:
    """Dependency factory: verifies the caller has an active membership in the
    `organization_id` path parameter, optionally restricted to specific roles."""

    async def _dependency(
        organization_id: uuid.UUID,
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> Membership:
        result = await db.execute(
            select(Membership).where(
                Membership.user_id == current_user.id,
                Membership.organization_id == organization_id,
                Membership.status == MembershipStatus.ACTIVE,
            )
        )
        membership = result.scalar_one_or_none()
        if membership is None:
            raise AppError(403, "forbidden", "You are not a member of this organization")
        if allowed_roles and membership.role not in allowed_roles:
            raise AppError(403, "forbidden", "Your role does not permit this action")
        return membership

    return _dependency
