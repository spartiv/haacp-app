import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Organization


async def _signup(client: AsyncClient, **overrides: str) -> dict:
    payload = {
        "email": "owner@polton.ua",
        "password": "supersecret123",
        "full_name": "Olena Polishchuk",
        "organization_name": "Polton",
    }
    payload.update(overrides)
    response = await client.post("/api/v1/auth/signup", json=payload)
    return response


async def test_signup_returns_user_and_tokens(client: AsyncClient) -> None:
    response = await _signup(client)

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "owner@polton.ua"
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]
    assert body["tokens"]["token_type"] == "bearer"


async def test_signup_rejects_duplicate_email(client: AsyncClient) -> None:
    await _signup(client)

    response = await _signup(client)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_already_registered"


async def test_signup_rejects_short_password(client: AsyncClient) -> None:
    response = await _signup(client, password="short")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_login_then_use_access_token(client: AsyncClient) -> None:
    await _signup(client)

    login_response = await client.post(
        "/api/v1/auth/login", json={"email": "owner@polton.ua", "password": "supersecret123"}
    )

    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == "owner@polton.ua"


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await _signup(client)

    response = await client.post(
        "/api/v1/auth/login", json={"email": "owner@polton.ua", "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


async def test_refresh_rotates_tokens(client: AsyncClient) -> None:
    signup_response = await _signup(client)
    old_refresh_token = signup_response.json()["tokens"]["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
    )

    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert new_tokens["refresh_token"] != old_refresh_token

    reuse_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
    )
    assert reuse_response.status_code == 401
    assert reuse_response.json()["error"]["code"] == "invalid_refresh_token"


async def test_logout_invalidates_refresh_token(client: AsyncClient) -> None:
    signup_response = await _signup(client)
    refresh_token = signup_response.json()["tokens"]["refresh_token"]

    logout_response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": refresh_token}
    )
    assert logout_response.status_code == 204

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 401


async def test_signup_stores_the_venue_timezone(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "kyiv@cafe.ua",
            "password": "supersecret123",
            "full_name": "  Олена Поліщук  ",
            "organization_name": "Кафе «Полтон»",
            "timezone": "Europe/Kyiv",
        },
    )

    assert response.status_code == 201
    assert response.json()["user"]["full_name"] == "Олена Поліщук"
    organization = await db_session.get(Organization, uuid.UUID(response.json()["organization_id"]))
    assert organization is not None
    assert organization.timezone == "Europe/Kyiv"


async def test_signup_rejects_unknown_timezone_and_blank_names(client: AsyncClient) -> None:
    base = {
        "email": "a@cafe.ua",
        "password": "supersecret123",
        "full_name": "A",
        "organization_name": "B",
    }

    bad_zone = await client.post("/api/v1/auth/signup", json={**base, "timezone": "Mars/Base"})
    blank_name = await client.post("/api/v1/auth/signup", json={**base, "full_name": "   "})

    assert bad_zone.status_code == 422
    assert blank_name.status_code == 422
