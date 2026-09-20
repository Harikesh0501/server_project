from datetime import datetime
from pydantic import BaseModel, Field

class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="Valid user email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=6, description="Account password")
    full_name: str | None = Field(default=None, description="Optional full name")

class UserLoginRequest(BaseModel):
    email_or_username: str = Field(..., description="Email or username")
    password: str = Field(..., description="Account password")

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str | None = None
    avatar_url: str | None = None
    role: str
    oauth_provider: str
    is_active: bool
    is_superuser: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class DeviceCodeResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int

class DeviceTokenRequest(BaseModel):
    device_code: str

class DeviceVerifyRequest(BaseModel):
    user_code: str

class OAuthCallbackRequest(BaseModel):
    code: str
    state: str | None = None
