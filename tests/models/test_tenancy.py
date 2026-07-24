import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Membership, MembershipRole, MembershipStatus, Organization, User


async def _make_user(db_session: AsyncSession, email: str = "owner@polton.ua") -> User:
    user = User(email=email, password_hash="hashed", full_name="Olena Polishchuk")
    db_session.add(user)
    await db_session.flush()
    return user


async def _make_org(db_session: AsyncSession, name: str = "Polton") -> Organization:
    org = Organization(name=name)
    db_session.add(org)
    await db_session.flush()
    return org


async def test_organization_defaults_timezone_to_utc(db_session: AsyncSession) -> None:
    org = await _make_org(db_session)
    assert org.timezone == "UTC"


async def test_user_defaults_to_active(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    assert user.is_active is True


async def test_membership_links_user_and_org_with_role(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    org = await _make_org(db_session)
    membership = Membership(
        user_id=user.id,
        organization_id=org.id,
        role=MembershipRole.OWNER,
        title="Власниця",
    )
    db_session.add(membership)
    await db_session.flush()

    assert membership.status == MembershipStatus.ACTIVE
    assert membership.role == MembershipRole.OWNER

    await db_session.refresh(org, attribute_names=["memberships"])
    assert org.memberships == [membership]


async def test_user_email_must_be_unique(db_session: AsyncSession) -> None:
    await _make_user(db_session, email="dup@polton.ua")
    db_session.add(User(email="dup@polton.ua", password_hash="x", full_name="Someone Else"))

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_membership_is_unique_per_user_and_org(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    org = await _make_org(db_session)
    db_session.add(Membership(user_id=user.id, organization_id=org.id, role=MembershipRole.OWNER))
    await db_session.flush()

    db_session.add(Membership(user_id=user.id, organization_id=org.id, role=MembershipRole.STAFF))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_deleting_organization_cascades_to_memberships(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    org = await _make_org(db_session)
    membership = Membership(user_id=user.id, organization_id=org.id, role=MembershipRole.OWNER)
    db_session.add(membership)
    await db_session.flush()
    membership_id = membership.id

    await db_session.delete(org)
    await db_session.flush()

    result = await db_session.execute(select(Membership).where(Membership.id == membership_id))
    assert result.scalar_one_or_none() is None


async def test_same_user_can_belong_to_multiple_organizations(db_session: AsyncSession) -> None:
    user = await _make_user(db_session)
    org_a = await _make_org(db_session, name="Polton")
    org_b = await _make_org(db_session, name="Consulting Co")
    db_session.add(Membership(user_id=user.id, organization_id=org_a.id, role=MembershipRole.OWNER))
    db_session.add(Membership(user_id=user.id, organization_id=org_b.id, role=MembershipRole.STAFF))
    await db_session.flush()

    await db_session.refresh(user, attribute_names=["memberships"])
    assert {m.organization_id for m in user.memberships} == {org_a.id, org_b.id}
