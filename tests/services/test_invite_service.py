import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Invite, InviteStatus, Membership, MembershipRole, MembershipStatus
from app.services import auth_service, invite_service
from tests.fakes import FakeEmailSender


async def _signup_owner(db_session: AsyncSession, **overrides: str) -> auth_service.AuthResult:
    defaults = {
        "email": "owner@polton.ua",
        "password": "supersecret123",
        "full_name": "Olena Polishchuk",
        "organization_name": "Polton",
    }
    defaults.update(overrides)
    return await auth_service.signup(db_session, **defaults)  # type: ignore[arg-type]


async def _org_id_for(db_session: AsyncSession, user_id: uuid.UUID) -> uuid.UUID:
    result = await db_session.execute(select(Membership).where(Membership.user_id == user_id))
    return result.scalar_one().organization_id


async def test_create_invite_persists_and_sends_email(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    owner = (await _signup_owner(db_session)).user
    org_id = await _org_id_for(db_session, owner.id)

    invite = await invite_service.create_invite(
        db_session,
        organization_id=org_id,
        invited_by_user_id=owner.id,
        email="Staffer@Polton.ua",
        role=MembershipRole.STAFF,
        email_sender=fake_email_sender,
    )

    assert invite.email == "staffer@polton.ua"
    assert invite.status == InviteStatus.PENDING
    assert len(fake_email_sender.sent) == 1
    assert fake_email_sender.sent[0]["to_email"] == "staffer@polton.ua"
    assert fake_email_sender.sent[0]["role"] == "staff"
    assert fake_email_sender.sent[0]["token"]


async def test_create_invite_rejects_unknown_organization(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    owner = (await _signup_owner(db_session)).user

    with pytest.raises(invite_service.OrganizationNotFoundError):
        await invite_service.create_invite(
            db_session,
            organization_id=uuid.uuid4(),
            invited_by_user_id=owner.id,
            email="staffer@polton.ua",
            role=MembershipRole.STAFF,
            email_sender=fake_email_sender,
        )


async def test_create_invite_rejects_existing_active_member(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    owner = (await _signup_owner(db_session)).user
    org_id = await _org_id_for(db_session, owner.id)

    with pytest.raises(invite_service.AlreadyMemberError):
        await invite_service.create_invite(
            db_session,
            organization_id=org_id,
            invited_by_user_id=owner.id,
            email="owner@polton.ua",
            role=MembershipRole.STAFF,
            email_sender=fake_email_sender,
        )


async def test_create_invite_rejects_duplicate_pending_invite(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    owner = (await _signup_owner(db_session)).user
    org_id = await _org_id_for(db_session, owner.id)
    await invite_service.create_invite(
        db_session,
        organization_id=org_id,
        invited_by_user_id=owner.id,
        email="staffer@polton.ua",
        role=MembershipRole.STAFF,
        email_sender=fake_email_sender,
    )

    with pytest.raises(invite_service.InviteAlreadyPendingError):
        await invite_service.create_invite(
            db_session,
            organization_id=org_id,
            invited_by_user_id=owner.id,
            email="staffer@polton.ua",
            role=MembershipRole.MANAGER,
            email_sender=fake_email_sender,
        )


async def _create_invite(
    db_session: AsyncSession,
    fake_email_sender: FakeEmailSender,
    *,
    email: str = "staffer@polton.ua",
    role: MembershipRole = MembershipRole.STAFF,
    owner_email: str | None = None,
) -> tuple[Invite, str]:
    owner = (
        await _signup_owner(db_session, email=owner_email or f"owner-{uuid.uuid4().hex}@polton.ua")
    ).user
    org_id = await _org_id_for(db_session, owner.id)
    invite = await invite_service.create_invite(
        db_session,
        organization_id=org_id,
        invited_by_user_id=owner.id,
        email=email,
        role=role,
        email_sender=fake_email_sender,
    )
    raw_token = fake_email_sender.sent[-1]["token"]
    return invite, raw_token


async def test_get_invite_preview_returns_invite_and_org(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    invite, raw_token = await _create_invite(db_session, fake_email_sender)

    previewed_invite, organization = await invite_service.get_invite_preview(
        db_session, token=raw_token
    )

    assert previewed_invite.id == invite.id
    assert organization.name == "Polton"


async def test_get_invite_preview_rejects_unknown_token(db_session: AsyncSession) -> None:
    with pytest.raises(invite_service.InviteNotFoundError):
        await invite_service.get_invite_preview(db_session, token="not-a-real-token")


async def test_get_invite_preview_rejects_expired_invite(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    invite, raw_token = await _create_invite(db_session, fake_email_sender)
    invite.expires_at = datetime.now(UTC) - timedelta(days=1)
    await db_session.commit()

    with pytest.raises(invite_service.InviteExpiredError):
        await invite_service.get_invite_preview(db_session, token=raw_token)


async def test_accept_invite_creates_new_account(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    invite, raw_token = await _create_invite(db_session, fake_email_sender)

    result = await invite_service.accept_invite(
        db_session,
        token=raw_token,
        current_user=None,
        password="brandnewpass123",
        full_name="New Staffer",
    )

    assert result.user.email == "staffer@polton.ua"
    membership_result = await db_session.execute(
        select(Membership).where(Membership.user_id == result.user.id)
    )
    membership = membership_result.scalar_one()
    assert membership.role == MembershipRole.STAFF
    assert membership.status == MembershipStatus.ACTIVE

    await db_session.refresh(invite)
    assert invite.status == InviteStatus.ACCEPTED
    assert invite.accepted_by_user_id == result.user.id


async def test_accept_invite_requires_password_and_name_for_new_account(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    _, raw_token = await _create_invite(db_session, fake_email_sender)

    with pytest.raises(invite_service.SignupFieldsRequiredError):
        await invite_service.accept_invite(
            db_session, token=raw_token, current_user=None, password=None, full_name=None
        )


async def test_accept_invite_for_existing_email_requires_login(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    await _signup_owner(db_session, email="staffer@polton.ua", organization_name="Other Co")
    _, raw_token = await _create_invite(db_session, fake_email_sender)

    with pytest.raises(invite_service.AccountExistsRequiresLoginError):
        await invite_service.accept_invite(
            db_session, token=raw_token, current_user=None, password=None, full_name=None
        )


async def test_accept_invite_rejects_mismatched_logged_in_user(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    other_user = (
        await _signup_owner(db_session, email="staffer@polton.ua", organization_name="Other Co")
    ).user
    someone_else = (
        await _signup_owner(
            db_session, email="someone-else@polton.ua", organization_name="Yet Another Co"
        )
    ).user
    _, raw_token = await _create_invite(db_session, fake_email_sender)
    assert other_user.email == "staffer@polton.ua"

    with pytest.raises(invite_service.AccountExistsRequiresLoginError):
        await invite_service.accept_invite(
            db_session, token=raw_token, current_user=someone_else, password=None, full_name=None
        )


async def test_accept_invite_for_existing_logged_in_matching_user_adds_membership(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    existing_user = (
        await _signup_owner(db_session, email="staffer@polton.ua", organization_name="Other Co")
    ).user
    invite, raw_token = await _create_invite(db_session, fake_email_sender)

    result = await invite_service.accept_invite(
        db_session,
        token=raw_token,
        current_user=existing_user,
        password=None,
        full_name=None,
    )

    assert result.user.id == existing_user.id
    membership_result = await db_session.execute(
        select(Membership).where(
            Membership.user_id == existing_user.id,
            Membership.organization_id == invite.organization_id,
        )
    )
    membership = membership_result.scalar_one()
    assert membership.status == MembershipStatus.ACTIVE
    assert membership.role == MembershipRole.STAFF


async def test_accept_invite_rejects_already_accepted_invite(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    _, raw_token = await _create_invite(db_session, fake_email_sender)
    await invite_service.accept_invite(
        db_session,
        token=raw_token,
        current_user=None,
        password="brandnewpass123",
        full_name="New Staffer",
    )

    with pytest.raises(invite_service.InviteAlreadyAcceptedError):
        await invite_service.accept_invite(
            db_session,
            token=raw_token,
            current_user=None,
            password="brandnewpass123",
            full_name="New Staffer",
        )


async def test_accept_invite_rejects_when_already_active_member(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    invite, raw_token = await _create_invite(db_session, fake_email_sender)
    await invite_service.accept_invite(
        db_session,
        token=raw_token,
        current_user=None,
        password="brandnewpass123",
        full_name="New Staffer",
    )
    membership_result = await db_session.execute(
        select(Membership).where(Membership.organization_id == invite.organization_id)
    )
    staffer_membership = next(
        m for m in membership_result.scalars().all() if m.role == MembershipRole.STAFF
    )
    staffer_user_id = staffer_membership.user_id

    second_invite, second_token = await _create_invite(
        db_session, fake_email_sender, email="second-invite-same-org@polton.ua"
    )
    # Force the second invite to target the same org/user as the first to hit the guard.
    second_invite.email = "staffer@polton.ua"
    second_invite.organization_id = invite.organization_id
    await db_session.commit()

    from app.models import User

    staffer_user = await db_session.get(User, staffer_user_id)
    assert staffer_user is not None

    with pytest.raises(invite_service.AlreadyMemberError):
        await invite_service.accept_invite(
            db_session,
            token=second_token,
            current_user=staffer_user,
            password=None,
            full_name=None,
        )


async def test_accept_invite_reactivates_removed_membership(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> None:
    invite, raw_token = await _create_invite(db_session, fake_email_sender)
    result = await invite_service.accept_invite(
        db_session,
        token=raw_token,
        current_user=None,
        password="brandnewpass123",
        full_name="New Staffer",
    )
    membership_result = await db_session.execute(
        select(Membership).where(Membership.user_id == result.user.id)
    )
    membership = membership_result.scalar_one()
    membership.status = MembershipStatus.REMOVED
    await db_session.commit()

    second_invite, second_token = await _create_invite(
        db_session,
        fake_email_sender,
        email="reinvite-placeholder@polton.ua",
        role=MembershipRole.MANAGER,
    )
    second_invite.email = "staffer@polton.ua"
    second_invite.organization_id = invite.organization_id
    await db_session.commit()

    reactivated = await invite_service.accept_invite(
        db_session,
        token=second_token,
        current_user=result.user,
        password=None,
        full_name=None,
    )

    assert reactivated.user.id == result.user.id
    await db_session.refresh(membership)
    assert membership.status == MembershipStatus.ACTIVE
    assert membership.role == MembershipRole.MANAGER
