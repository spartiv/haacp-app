import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Membership, MembershipRole, RefreshToken
from app.services import auth_service


async def _signup(db_session: AsyncSession, **overrides: str) -> auth_service.AuthResult:
    defaults = {
        "email": "owner@polton.ua",
        "password": "supersecret123",
        "full_name": "Olena Polishchuk",
        "organization_name": "Polton",
    }
    defaults.update(overrides)
    return await auth_service.signup(db_session, **defaults)  # type: ignore[arg-type]


async def test_signup_creates_org_owner_membership_and_tokens(db_session: AsyncSession) -> None:
    result = await _signup(db_session)

    assert result.user.email == "owner@polton.ua"
    assert result.access_token
    assert result.refresh_token

    memberships = (
        (await db_session.execute(select(Membership).where(Membership.user_id == result.user.id)))
        .scalars()
        .all()
    )
    assert len(memberships) == 1
    assert memberships[0].role == MembershipRole.OWNER


async def test_signup_normalizes_email_case_and_rejects_duplicates(
    db_session: AsyncSession,
) -> None:
    await _signup(db_session, email="Owner@Polton.ua")

    with pytest.raises(auth_service.EmailAlreadyRegisteredError):
        await _signup(db_session, email="owner@polton.ua")


async def test_login_succeeds_with_correct_credentials(db_session: AsyncSession) -> None:
    await _signup(db_session, email="owner@polton.ua", password="supersecret123")

    result = await auth_service.login(
        db_session, email="OWNER@polton.ua", password="supersecret123"
    )

    assert result.user.email == "owner@polton.ua"


async def test_login_fails_with_wrong_password(db_session: AsyncSession) -> None:
    await _signup(db_session, email="owner@polton.ua", password="supersecret123")

    with pytest.raises(auth_service.InvalidCredentialsError):
        await auth_service.login(db_session, email="owner@polton.ua", password="wrong-password")


async def test_login_fails_for_unknown_email(db_session: AsyncSession) -> None:
    with pytest.raises(auth_service.InvalidCredentialsError):
        await auth_service.login(db_session, email="nobody@polton.ua", password="whatever123")


async def test_login_fails_for_inactive_user(db_session: AsyncSession) -> None:
    result = await _signup(db_session, email="owner@polton.ua", password="supersecret123")
    result.user.is_active = False
    await db_session.commit()

    with pytest.raises(auth_service.InvalidCredentialsError):
        await auth_service.login(db_session, email="owner@polton.ua", password="supersecret123")


async def test_refresh_issues_new_pair_and_revokes_the_old_token(db_session: AsyncSession) -> None:
    signup_result = await _signup(db_session)
    old_refresh_token = signup_result.refresh_token

    refreshed = await auth_service.refresh(db_session, refresh_token=old_refresh_token)

    assert refreshed.refresh_token != old_refresh_token
    assert refreshed.access_token != signup_result.access_token

    with pytest.raises(auth_service.InvalidRefreshTokenError):
        await auth_service.refresh(db_session, refresh_token=old_refresh_token)


async def test_refresh_rejects_garbage_token(db_session: AsyncSession) -> None:
    with pytest.raises(auth_service.InvalidRefreshTokenError):
        await auth_service.refresh(db_session, refresh_token="not-a-real-token")


async def test_refresh_rejects_expired_token(db_session: AsyncSession) -> None:
    signup_result = await _signup(db_session)
    stored = await db_session.get(RefreshToken, uuid.UUID(_jti_from(signup_result.refresh_token)))
    assert stored is not None
    stored.expires_at = datetime.now(UTC) - timedelta(days=1)
    await db_session.commit()

    with pytest.raises(auth_service.InvalidRefreshTokenError):
        await auth_service.refresh(db_session, refresh_token=signup_result.refresh_token)


async def test_refresh_rejects_token_for_now_inactive_user(db_session: AsyncSession) -> None:
    signup_result = await _signup(db_session)
    signup_result.user.is_active = False
    await db_session.commit()

    with pytest.raises(auth_service.InvalidRefreshTokenError):
        await auth_service.refresh(db_session, refresh_token=signup_result.refresh_token)


async def test_logout_revokes_the_refresh_token(db_session: AsyncSession) -> None:
    signup_result = await _signup(db_session)

    await auth_service.logout(db_session, refresh_token=signup_result.refresh_token)

    with pytest.raises(auth_service.InvalidRefreshTokenError):
        await auth_service.refresh(db_session, refresh_token=signup_result.refresh_token)


async def test_logout_is_a_no_op_for_an_already_invalid_token(db_session: AsyncSession) -> None:
    await auth_service.logout(db_session, refresh_token="not-a-real-token")


def _jti_from(raw_token: str) -> str:
    import jwt as pyjwt

    from app.core.config import get_settings

    settings = get_settings()
    payload = pyjwt.decode(raw_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    return str(payload["jti"])
