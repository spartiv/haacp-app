from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, db: DbSession) -> AuthResponse:
    result = await auth_service.signup(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        organization_name=payload.organization_name,
        timezone=payload.timezone,
    )
    return AuthResponse(
        user=UserResponse.model_validate(result.user),
        tokens=TokenResponse(access_token=result.access_token, refresh_token=result.refresh_token),
        organization_id=result.organization_id,
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: DbSession) -> AuthResponse:
    result = await auth_service.login(db, email=payload.email, password=payload.password)
    return AuthResponse(
        user=UserResponse.model_validate(result.user),
        tokens=TokenResponse(access_token=result.access_token, refresh_token=result.refresh_token),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(payload: RefreshRequest, db: DbSession) -> TokenResponse:
    result = await auth_service.refresh(db, refresh_token=payload.refresh_token)
    return TokenResponse(access_token=result.access_token, refresh_token=result.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: LogoutRequest, db: DbSession) -> None:
    await auth_service.logout(db, refresh_token=payload.refresh_token)
