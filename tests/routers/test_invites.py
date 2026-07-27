from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Invite
from tests.fakes import FakeEmailSender


async def _signup(client: AsyncClient, **overrides: str) -> dict:
    payload = {
        "email": "owner@polton.ua",
        "password": "supersecret123",
        "full_name": "Olena Polishchuk",
        "organization_name": "Polton",
    }
    payload.update(overrides)
    response = await client.post("/api/v1/auth/signup", json=payload)
    return response.json()


def _auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


async def _sole_invite(db_session: AsyncSession) -> Invite:
    result = await db_session.execute(select(Invite))
    return result.scalar_one()


async def test_owner_can_invite_and_new_staffer_can_accept(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    access_token = owner["tokens"]["access_token"]

    create_response = await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "staff"},
        headers=_auth_header(access_token),
    )
    assert create_response.status_code == 201
    assert len(fake_email_sender.sent) == 1
    token = fake_email_sender.sent[0]["token"]

    preview_response = await client.get(f"/api/v1/invites/{token}")
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["organization_name"] == "Polton"
    assert preview["email"] == "staffer@polton.ua"
    assert preview["role"] == "staff"

    accept_response = await client.post(
        f"/api/v1/invites/{token}/accept",
        json={"password": "brandnewpass123", "full_name": "New Staffer"},
    )
    assert accept_response.status_code == 200
    body = accept_response.json()
    assert body["user"]["email"] == "staffer@polton.ua"
    assert body["organization_id"] == org_id
    assert body["tokens"]["access_token"]


async def test_staff_cannot_create_invites(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    owner_token = owner["tokens"]["access_token"]

    await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "staff"},
        headers=_auth_header(owner_token),
    )
    staffer_token = fake_email_sender.sent[0]["token"]
    accept_response = await client.post(
        f"/api/v1/invites/{staffer_token}/accept",
        json={"password": "brandnewpass123", "full_name": "New Staffer"},
    )
    staffer_access_token = accept_response.json()["tokens"]["access_token"]

    response = await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "another@polton.ua", "role": "staff"},
        headers=_auth_header(staffer_access_token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


async def test_create_invite_requires_authentication(client: AsyncClient) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]

    response = await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "staff"},
    )

    assert response.status_code == 401


async def test_create_invite_rejects_duplicate_pending(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    access_token = owner["tokens"]["access_token"]

    await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "staff"},
        headers=_auth_header(access_token),
    )
    response = await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "manager"},
        headers=_auth_header(access_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invite_already_pending"


async def test_preview_unknown_token_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/invites/not-a-real-token")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "invite_not_found"


async def test_accept_for_existing_account_requires_login_first(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    access_token = owner["tokens"]["access_token"]
    await _signup(client, email="staffer@polton.ua", organization_name="Staffer's Own Business")

    await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "staff"},
        headers=_auth_header(access_token),
    )
    token = fake_email_sender.sent[0]["token"]

    anonymous_accept = await client.post(f"/api/v1/invites/{token}/accept", json={})
    assert anonymous_accept.status_code == 409
    assert anonymous_accept.json()["error"]["code"] == "account_exists_requires_login"

    login_response = await client.post(
        "/api/v1/auth/login", json={"email": "staffer@polton.ua", "password": "supersecret123"}
    )
    staffer_token = login_response.json()["tokens"]["access_token"]

    authenticated_accept = await client.post(
        f"/api/v1/invites/{token}/accept", json={}, headers=_auth_header(staffer_token)
    )
    assert authenticated_accept.status_code == 200
    assert authenticated_accept.json()["organization_id"] == org_id


async def test_create_invite_rejects_already_active_member(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    access_token = owner["tokens"]["access_token"]

    response = await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "owner@polton.ua", "role": "staff"},
        headers=_auth_header(access_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "already_member"


async def test_preview_expired_invite_returns_410(
    client: AsyncClient, fake_email_sender: FakeEmailSender, db_session: AsyncSession
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    access_token = owner["tokens"]["access_token"]
    await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "staff"},
        headers=_auth_header(access_token),
    )
    token = fake_email_sender.sent[0]["token"]
    invite = await _sole_invite(db_session)
    invite.expires_at = datetime.now(UTC) - timedelta(days=1)
    await db_session.commit()

    response = await client.get(f"/api/v1/invites/{token}")

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "invite_expired"


async def test_preview_already_accepted_invite_returns_410(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    access_token = owner["tokens"]["access_token"]
    await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "staff"},
        headers=_auth_header(access_token),
    )
    token = fake_email_sender.sent[0]["token"]
    await client.post(
        f"/api/v1/invites/{token}/accept",
        json={"password": "brandnewpass123", "full_name": "New Staffer"},
    )

    response = await client.get(f"/api/v1/invites/{token}")

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "invite_already_accepted"


async def test_accept_unknown_token_returns_404(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/invites/not-a-real-token/accept",
        json={"password": "brandnewpass123", "full_name": "New Staffer"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "invite_not_found"


async def test_accept_expired_invite_returns_410(
    client: AsyncClient, fake_email_sender: FakeEmailSender, db_session: AsyncSession
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    access_token = owner["tokens"]["access_token"]
    await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "staff"},
        headers=_auth_header(access_token),
    )
    token = fake_email_sender.sent[0]["token"]
    invite = await _sole_invite(db_session)
    invite.expires_at = datetime.now(UTC) - timedelta(days=1)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/invites/{token}/accept",
        json={"password": "brandnewpass123", "full_name": "New Staffer"},
    )

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "invite_expired"


async def test_accept_already_accepted_invite_returns_410(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    access_token = owner["tokens"]["access_token"]
    await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "staff"},
        headers=_auth_header(access_token),
    )
    token = fake_email_sender.sent[0]["token"]
    accept_payload = {"password": "brandnewpass123", "full_name": "New Staffer"}
    await client.post(f"/api/v1/invites/{token}/accept", json=accept_payload)

    response = await client.post(f"/api/v1/invites/{token}/accept", json=accept_payload)

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "invite_already_accepted"


async def test_accept_new_account_requires_password_and_full_name(
    client: AsyncClient, fake_email_sender: FakeEmailSender
) -> None:
    owner = await _signup(client)
    org_id = owner["organization_id"]
    access_token = owner["tokens"]["access_token"]
    await client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "staffer@polton.ua", "role": "staff"},
        headers=_auth_header(access_token),
    )
    token = fake_email_sender.sent[0]["token"]

    response = await client.post(f"/api/v1/invites/{token}/accept", json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "signup_fields_required"
