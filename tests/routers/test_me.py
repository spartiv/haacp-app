from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Membership, MembershipStatus
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


async def test_lists_single_organization_after_signup(client: AsyncClient) -> None:
    owner = await _signup(client)

    response = await client.get(
        "/api/v1/me/organizations", headers=_auth_header(owner["tokens"]["access_token"])
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "organization_id": owner["organization_id"],
            "name": "Polton",
            "role": "owner",
            "title": None,
        }
    ]


async def test_lists_every_active_membership_sorted_by_name(
    client: AsyncClient, fake_email_sender: FakeEmailSender, db_session: AsyncSession
) -> None:
    zebra = await _signup(client, email="zebra@zebra.ua", organization_name="Zebra Cafe")
    alpha = await _signup(client, email="alpha@alpha.ua", organization_name="Alpha Bakery")
    await client.post(
        f"/api/v1/organizations/{zebra['organization_id']}/invites",
        json={"email": "alpha@alpha.ua", "role": "staff"},
        headers=_auth_header(zebra["tokens"]["access_token"]),
    )
    invite_token = fake_email_sender.sent[0]["token"]
    alpha_token = alpha["tokens"]["access_token"]
    await client.post(
        f"/api/v1/invites/{invite_token}/accept", json={}, headers=_auth_header(alpha_token)
    )

    response = await client.get("/api/v1/me/organizations", headers=_auth_header(alpha_token))

    assert response.status_code == 200
    assert [(org["name"], org["role"]) for org in response.json()] == [
        ("Alpha Bakery", "owner"),
        ("Zebra Cafe", "staff"),
    ]

    # A removed membership no longer shows up.
    await db_session.execute(
        update(Membership)
        .where(Membership.organization_id == zebra["organization_id"])
        .where(Membership.role == "staff")
        .values(status=MembershipStatus.REMOVED)
    )
    response = await client.get("/api/v1/me/organizations", headers=_auth_header(alpha_token))
    assert [org["name"] for org in response.json()] == ["Alpha Bakery"]


async def test_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me/organizations")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
