import uuid

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_membership
from app.core.errors import AppError
from app.core.security import create_access_token
from app.models import Membership, MembershipRole, MembershipStatus, Organization
from app.services import auth_service


def _bearer(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


async def _membership_for(db_session: AsyncSession, user_id: uuid.UUID) -> Membership:
    result = await db_session.execute(select(Membership).where(Membership.user_id == user_id))
    return result.scalar_one()


async def test_get_current_user_rejects_missing_credentials(db_session: AsyncSession) -> None:
    with pytest.raises(AppError) as exc_info:
        await get_current_user(credentials=None, db=db_session)
    assert exc_info.value.status_code == 401


async def test_get_current_user_rejects_invalid_token(db_session: AsyncSession) -> None:
    with pytest.raises(AppError) as exc_info:
        await get_current_user(credentials=_bearer("garbage"), db=db_session)
    assert exc_info.value.status_code == 401


async def test_get_current_user_returns_user_for_valid_token(db_session: AsyncSession) -> None:
    signup_result = await auth_service.signup(
        db_session,
        email="owner@polton.ua",
        password="supersecret123",
        full_name="Olena Polishchuk",
        organization_name="Polton",
    )

    user = await get_current_user(credentials=_bearer(signup_result.access_token), db=db_session)

    assert user.id == signup_result.user.id


async def test_get_current_user_rejects_inactive_user(db_session: AsyncSession) -> None:
    signup_result = await auth_service.signup(
        db_session,
        email="owner@polton.ua",
        password="supersecret123",
        full_name="Olena Polishchuk",
        organization_name="Polton",
    )
    signup_result.user.is_active = False
    await db_session.commit()

    with pytest.raises(AppError) as exc_info:
        await get_current_user(credentials=_bearer(signup_result.access_token), db=db_session)
    assert exc_info.value.status_code == 401


async def test_get_current_user_rejects_token_with_no_matching_user(
    db_session: AsyncSession,
) -> None:
    token = create_access_token(uuid.uuid4())

    with pytest.raises(AppError) as exc_info:
        await get_current_user(credentials=_bearer(token), db=db_session)
    assert exc_info.value.status_code == 401


async def test_require_membership_rejects_non_member(db_session: AsyncSession) -> None:
    signup_result = await auth_service.signup(
        db_session,
        email="owner@polton.ua",
        password="supersecret123",
        full_name="Olena Polishchuk",
        organization_name="Polton",
    )
    other_org = Organization(name="Other Business")
    db_session.add(other_org)
    await db_session.flush()

    dependency = require_membership()
    with pytest.raises(AppError) as exc_info:
        await dependency(
            organization_id=other_org.id, current_user=signup_result.user, db=db_session
        )
    assert exc_info.value.status_code == 403


async def test_require_membership_enforces_allowed_roles(db_session: AsyncSession) -> None:
    signup_result = await auth_service.signup(
        db_session,
        email="owner@polton.ua",
        password="supersecret123",
        full_name="Olena Polishchuk",
        organization_name="Polton",
    )
    membership_row = await _membership_for(db_session, signup_result.user.id)

    dependency = require_membership(MembershipRole.STAFF)
    with pytest.raises(AppError) as exc_info:
        await dependency(
            organization_id=membership_row.organization_id,
            current_user=signup_result.user,
            db=db_session,
        )
    assert exc_info.value.status_code == 403


async def test_require_membership_allows_matching_role(db_session: AsyncSession) -> None:
    signup_result = await auth_service.signup(
        db_session,
        email="owner@polton.ua",
        password="supersecret123",
        full_name="Olena Polishchuk",
        organization_name="Polton",
    )
    membership_row = await _membership_for(db_session, signup_result.user.id)

    dependency = require_membership(MembershipRole.OWNER, MembershipRole.MANAGER)
    membership = await dependency(
        organization_id=membership_row.organization_id,
        current_user=signup_result.user,
        db=db_session,
    )

    assert membership.role == MembershipRole.OWNER
    assert membership.status == MembershipStatus.ACTIVE


async def test_require_membership_rejects_removed_membership(db_session: AsyncSession) -> None:
    signup_result = await auth_service.signup(
        db_session,
        email="owner@polton.ua",
        password="supersecret123",
        full_name="Olena Polishchuk",
        organization_name="Polton",
    )
    membership = await _membership_for(db_session, signup_result.user.id)
    organization_id = membership.organization_id
    membership.status = MembershipStatus.REMOVED
    await db_session.commit()

    dependency = require_membership()
    with pytest.raises(AppError) as exc_info:
        await dependency(
            organization_id=organization_id,
            current_user=signup_result.user,
            db=db_session,
        )
    assert exc_info.value.status_code == 403
