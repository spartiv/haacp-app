import uuid
from zoneinfo import available_timezones

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    organization_name: str = Field(min_length=1, max_length=200)
    timezone: str = Field(
        default="UTC",
        max_length=64,
        description="IANA timezone of the venue, e.g. `Europe/Kyiv`. Decides when its "
        "day (and daily control sheet) starts.",
    )

    @field_validator("full_name", "organization_name")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, value: str) -> str:
        # An unknown zone would be stored and then break every daily sheet.
        if value not in available_timezones():
            raise ValueError("unknown timezone, expected an IANA name such as Europe/Kyiv")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse
    # Set for signup and invite-accept, where there's exactly one relevant org.
    # Left unset for login/refresh: a user may belong to several organizations,
    # and picking one isn't this endpoint's job — see GET /me/organizations.
    organization_id: uuid.UUID | None = None
