import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from app.core.config import get_settings
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


async def test_hash_password_produces_a_verifiable_but_distinct_hash() -> None:
    password_hash = await hash_password("supersecret123")

    assert password_hash != "supersecret123"
    assert await verify_password("supersecret123", password_hash)
    assert not await verify_password("wrong-password", password_hash)


def test_hash_token_is_deterministic() -> None:
    assert hash_token("same-value") == hash_token("same-value")
    assert hash_token("a") != hash_token("b")


def test_decode_token_round_trips_access_token() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id)

    decoded = decode_token(token, expected_type=TokenType.ACCESS)

    assert decoded.user_id == user_id
    assert decoded.token_type == TokenType.ACCESS


def test_decode_token_rejects_wrong_token_type() -> None:
    token = create_access_token(uuid.uuid4())

    with pytest.raises(InvalidTokenError):
        decode_token(token, expected_type=TokenType.REFRESH)


def test_decode_token_rejects_expired_token() -> None:
    settings = get_settings()
    now = datetime.now(UTC)
    expired_payload = {
        "sub": str(uuid.uuid4()),
        "type": TokenType.ACCESS.value,
        "jti": str(uuid.uuid4()),
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
    }
    expired_token = pyjwt.encode(
        expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )

    with pytest.raises(InvalidTokenError):
        decode_token(expired_token, expected_type=TokenType.ACCESS)


def test_decode_token_rejects_bad_signature() -> None:
    token = create_refresh_token(uuid.uuid4(), uuid.uuid4())
    header, payload, signature = token.split(".")
    tampered = f"{header}.{payload}.{signature[::-1]}"

    with pytest.raises(InvalidTokenError):
        decode_token(tampered, expected_type=TokenType.REFRESH)


def test_decode_token_rejects_malformed_payload() -> None:
    settings = get_settings()
    bad_payload = {"type": TokenType.ACCESS.value, "sub": "not-a-uuid", "jti": str(uuid.uuid4())}
    token = pyjwt.encode(bad_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(InvalidTokenError):
        decode_token(token, expected_type=TokenType.ACCESS)
