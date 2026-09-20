from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    DeviceCodeResponse,
    DeviceTokenRequest,
    DeviceVerifyRequest,
    OAuthCallbackRequest
)
from app.services.auth_service import auth_service
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])
security_scheme = HTTPBearer(auto_error=False)

def _build_token_response(user: User) -> TokenResponse:
    access_token, expires_in = auth_service.create_access_token(user.id, user.email, user.role)
    refresh_token = auth_service.create_refresh_token(user.id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )

# --- 1. Offline Local Credentials (Task 11.3) ---

@router.post("/local/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_local_user(payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Registers a new developer or administrator account directly on the sovereign platform.
    The very first registered user is automatically promoted to platform 'admin'.
    """
    clean_email = payload.email.strip().lower()
    clean_username = payload.username.strip().lower()

    # Check existence
    existing = await db.execute(
        select(User).where((User.email == clean_email) | (User.username == clean_username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or username already exists."
        )

    # First user bootstrap to root admin
    total_users = (await db.execute(select(User))).scalars().all()
    is_first_user = len(total_users) == 0
    role = "admin" if is_first_user else "developer"

    hashed_pw = auth_service.hash_password(payload.password)

    user = User(
        email=clean_email,
        username=clean_username,
        hashed_password=hashed_pw,
        full_name=payload.full_name,
        role=role,
        oauth_provider="local",
        is_active=True,
        is_superuser=is_first_user
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return _build_token_response(user)

@router.post("/local/login", response_model=TokenResponse)
async def login_local_user(payload: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticates with email or username and password (100% offline operational).
    Returns JWT access and refresh token pair.
    """
    login_id = payload.email_or_username.strip().lower()
    result = await db.execute(
        select(User).where((User.email == login_id) | (User.username == login_id))
    )
    user = result.scalar_one_or_none()

    if not user or not auth_service.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    return _build_token_response(user)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Returns profile and roles for current authenticated session."""
    return UserResponse.model_validate(current_user)

# --- 2. Session Management & Token Revocation (Task 11.4) ---

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchanges a valid long-lived refresh token for a fresh access token."""
    if await auth_service.is_token_revoked(payload.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked. Please log in again."
        )

    try:
        decoded = auth_service.decode_token(payload.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not a valid refresh token."
        )

    user_id = decoded.get("sub")
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer active."
        )

    return _build_token_response(user)

@router.post("/logout")
async def logout(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    current_user: User = Depends(get_current_user)
):
    """
    Revokes the current access token session in Redis blacklist.
    """
    if credentials and credentials.credentials:
        await auth_service.revoke_token(credentials.credentials)

    return {"status": "success", "message": "Successfully logged out and session revoked."}

# --- 3. RFC 8628 OAuth Device Authorization Flow for CLI (Task 11.2) ---

@router.post("/device/code", response_model=DeviceCodeResponse)
async def create_device_code():
    """
    Initiates RFC 8628 Device Authorization Flow.
    Returns 8-character human-friendly user code (e.g. 'WDJB-4921') and polling interval.
    """
    data = await auth_service.generate_device_code()
    return DeviceCodeResponse(**data)

@router.post("/device/verify")
async def verify_device_code(payload: DeviceVerifyRequest, current_user: User = Depends(get_current_user)):
    """
    Web user confirms the 8-character user code shown in their terminal to approve CLI login.
    """
    success = await auth_service.verify_device_code(payload.user_code, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired user authorization code."
        )
    return {"status": "approved", "message": f"CLI login verified for {current_user.email}."}

@router.post("/device/token")
async def poll_device_token(payload: DeviceTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    CLI polls endpoint every 5 seconds until user approves in browser.
    """
    record = await auth_service.poll_device_token(payload.device_code)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="expired_token"
        )

    status_str = record.get("status")
    if status_str == "pending":
        return {"status": "authorization_pending"}

    if status_str == "approved":
        user_id = record.get("user_id")
        res = await db.execute(select(User).where(User.id == user_id))
        user = res.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Approved user account inactive."
            )
        return _build_token_response(user)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="access_denied"
    )

# --- 4. OAuth 2.0 Handlers (GitHub & Google) (Task 11.1) ---

@router.get("/github/url")
async def get_github_url():
    """Returns GitHub OAuth 2.0 authorization redirect URL."""
    try:
        url = auth_service.get_github_auth_url()
        return {"url": url}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.post("/github/callback", response_model=TokenResponse)
async def github_callback(payload: OAuthCallbackRequest, db: AsyncSession = Depends(get_db)):
    """Exchanges GitHub OAuth code, upserts user, and issues platform JWT tokens."""
    try:
        user = await auth_service.handle_github_callback(payload.code, db)
        return _build_token_response(user)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/google/url")
async def get_google_url():
    """Returns Google OAuth 2.0 authorization redirect URL."""
    try:
        url = auth_service.get_google_auth_url()
        return {"url": url}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(payload: OAuthCallbackRequest, db: AsyncSession = Depends(get_db)):
    """Exchanges Google OAuth code, upserts user, and issues platform JWT tokens."""
    try:
        user = await auth_service.handle_google_callback(payload.code, db)
        return _build_token_response(user)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
