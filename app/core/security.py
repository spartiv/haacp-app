import asyncio
import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

_password_hasher = PasswordHasher()


async def hash_password(password: str) -> str:
    """Argon2 hashing is deliberately CPU-expensive; run it off the event
    loop thread so one auth request doesn't stall every other concurrent
    request for the duration of the hash."""
    return await asyncio.to_thread(_password_hasher.hash, password)


async def verify_password(password: str, password_hash: str) -> bool:
    try:
        return await asyncio.to_thread(_password_hasher.verify, password_hash, password)
    except VerifyMismatchError:
        return False


def hash_token(raw_token: str) -> str:
    """Opaque-token integrity check (not a password): SHA-256 is appropriate here."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class DecodedToken:
    def __init__(self, user_id: uuid.UUID, token_type: TokenType, jti: uuid.UUID) -> None:
        self.user_id = user_id
        self.token_type = token_type
        self.jti = jti


def _encode_token(
    *, user_id: uuid.UUID, token_type: TokenType, expires_delta: timedelta, jti: uuid.UUID
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type.value,
        "jti": str(jti),
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    return _encode_token(
        user_id=user_id,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        jti=uuid.uuid4(),
    )


def create_refresh_token(user_id: uuid.UUID, jti: uuid.UUID) -> str:
    settings = get_settings()
    return _encode_token(
        user_id=user_id,
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        jti=jti,
    )


class InvalidTokenError(Exception):
    pass


def decode_token(raw_token: str, *, expected_type: TokenType) -> DecodedToken:
    settings = get_settings()
    try:
        payload = jwt.decode(
            raw_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    if payload.get("type") != expected_type.value:
        raise InvalidTokenError(f"expected token type {expected_type.value!r}")

    try:
        user_id = uuid.UUID(payload["sub"])
        jti = uuid.UUID(payload["jti"])
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError("malformed token payload") from exc

    return DecodedToken(user_id=user_id, token_type=expected_type, jti=jti)
