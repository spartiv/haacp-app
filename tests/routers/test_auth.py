from httpx import AsyncClient


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
