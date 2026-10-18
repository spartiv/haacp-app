import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import DomainError
from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import (
    Membership,
    MembershipRole,
    MembershipStatus,
    Organization,
    RefreshToken,
    User,
)
from app.services import allergen_service

logger = logging.getLogger(__name__)


class EmailAlreadyRegisteredError(DomainError):
    status_code = 409
    code = "email_already_registered"
    message = "An account with this email already exists"


class InvalidCredentialsError(DomainError):
    status_code = 401
    code = "invalid_credentials"
    message = "Email or password is incorrect"


class InvalidRefreshTokenError(DomainError):
    status_code = 401
    code = "invalid_refresh_token"
    message = "Refresh token is invalid or expired"


@dataclass(frozen=True)
class AuthResult:
    user: User
    access_token: str
    refresh_token: str
    organization_id: uuid.UUID | None = None


def normalize_email(email: str) -> str:
    return email.strip().lower()


# Computed once (lazily, since hashing is now async) so login() can run a
# real password verification even when the email isn't registered, keeping
# response timing from leaking whether an account exists.
_dummy_password_hash: str | None = None


async def _get_dummy_password_hash() -> str:
    global _dummy_password_hash
    if _dummy_password_hash is None:
        _dummy_password_hash = await hash_password("dummy-password-for-constant-time-comparison")
    return _dummy_password_hash


async def issue_token_pair(db: AsyncSession, user: User) -> tuple[str, str]:
    settings = get_settings()
    jti = uuid.uuid4()
    refresh_token_value = create_refresh_token(user.id, jti)
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    db.add(
        RefreshToken(
            id=jti,
            user_id=user.id,
            token_hash=hash_token(refresh_token_value),
            expires_at=expires_at,
        )
    )
    access_token_value = create_access_token(user.id)
    return access_token_value, refresh_token_value


async def signup(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str,
    organization_name: str,
    timezone: str = "UTC",
) -> AuthResult:
    normalized_email = normalize_email(email)
    existing = await db.execute(select(User).where(User.email == normalized_email))
    if existing.scalar_one_or_none() is not None:
        raise EmailAlreadyRegisteredError

    organization = Organization(name=organization_name, timezone=timezone)
    user = User(
        email=normalized_email, password_hash=await hash_password(password), full_name=full_name
    )
    db.add_all([organization, user])
    await db.flush()

    db.add(
        Membership(
            user_id=user.id,
            organization_id=organization.id,
            role=MembershipRole.OWNER,
            status=MembershipStatus.ACTIVE,
        )
    )
    await allergen_service.seed_default_allergen_statuses(db, organization_id=organization.id)

    access_token, refresh_token = await issue_token_pair(db, user)
    await db.commit()
    logger.info("User signed up: user_id=%s organization_id=%s", user.id, organization.id)
    return AuthResult(
        user=user,
        access_token=access_token,
        refresh_token=refresh_token,
        organization_id=organization.id,
    )


async def login(db: AsyncSession, *, email: str, password: str) -> AuthResult:
    normalized_email = normalize_email(email)
    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()

    password_hash = user.password_hash if user else await _get_dummy_password_hash()
    valid_password = await verify_password(password, password_hash)
    if user is None or not user.is_active or not valid_password:
        logger.warning("Login failed for email=%s", normalized_email)
        raise InvalidCredentialsError

    access_token, refresh_token = await issue_token_pair(db, user)
    await db.commit()
    logger.info("User logged in: user_id=%s", user.id)
    return AuthResult(user=user, access_token=access_token, refresh_token=refresh_token)


async def refresh(db: AsyncSession, *, refresh_token: str) -> AuthResult:
    try:
        decoded = decode_token(refresh_token, expected_type=TokenType.REFRESH)
    except InvalidTokenError as exc:
        logger.warning("Refresh rejected: token failed to decode")
        raise InvalidRefreshTokenError from exc

    stored = await db.get(RefreshToken, decoded.jti)
    if (
        stored is None
        or stored.revoked_at is not None
        or stored.expires_at < datetime.now(UTC)
        or stored.token_hash != hash_token(refresh_token)
    ):
        logger.warning("Refresh rejected: token unknown, revoked, expired, or mismatched")
        raise InvalidRefreshTokenError

    user = await db.get(User, decoded.user_id)
    if user is None or not user.is_active:
        logger.warning("Refresh rejected: user_id=%s not found or inactive", decoded.user_id)
        raise InvalidRefreshTokenError

    stored.revoked_at = datetime.now(UTC)
    access_token, new_refresh_token = await issue_token_pair(db, user)
    await db.commit()
    logger.debug("Access token refreshed: user_id=%s", user.id)
    return AuthResult(user=user, access_token=access_token, refresh_token=new_refresh_token)


async def logout(db: AsyncSession, *, refresh_token: str) -> None:
    try:
        decoded = decode_token(refresh_token, expected_type=TokenType.REFRESH)
    except InvalidTokenError:
        return

    stored = await db.get(RefreshToken, decoded.jti)
    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = datetime.now(UTC)
        await db.commit()
        logger.info("User logged out: user_id=%s", stored.user_id)
