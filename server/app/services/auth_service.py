import os
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
import httpx
import structlog
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User

logger = structlog.get_logger()

# Password hashing context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """
    Sovereign Authentication & Identity Engine (EPIC-11).
    Handles offline local credentials, OAuth 2.0 flows (GitHub & Google),
    RFC 8628 device authorization for headless CLI logins, JWT token lifecycle,
    and instant Redis token revocation blacklisting.
    """

    def __init__(self):
        # In-memory revocation cache fallback if Redis is unreachable
        self._memory_blacklist: dict[str, float] = {}
        # In-memory device authorization cache fallback
        self._memory_device_codes: dict[str, dict[str, Any]] = {}
        self._memory_user_code_map: dict[str, str] = {}

    # --- Password Hashing (Task 11.3.2) ---

    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes password using bcrypt with automatic salt generation."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str | None) -> bool:
        """Verifies plain password against stored hash."""
        if not hashed_password:
            return False
        return pwd_context.verify(plain_password, hashed_password)

    # --- JWT Token Generation & Lifecycle (Task 11.1.4 & 11.4.1) ---

    @staticmethod
    def create_access_token(user_id: str, email: str, role: str) -> tuple[str, int]:
        """
        Creates short-lived platform JWT Access Token (default: 60 minutes).
        Returns (token, expires_in_seconds).
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + expires_delta
        expires_in = int(expires_delta.total_seconds())

        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": "access",
            "jti": uuid.uuid4().hex,
            "exp": expire
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return token, expires_in

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Creates long-lived platform JWT Refresh Token (default: 30 days)."""
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "jti": uuid.uuid4().hex,
            "exp": expire
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        """Decodes and cryptographically validates a platform JWT token."""
        try:
            return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except JWTError as e:
            raise ValueError(f"Invalid or expired token: {str(e)}")

    # --- Token Revocation Blacklist (Task 11.4.3) ---

    async def revoke_token(self, token: str) -> None:
        """Revokes token JTI in Redis blacklist or fallback in-memory cache."""
        try:
            payload = self.decode_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if not jti or not exp:
                return

            ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 60)

            # Try Redis first
            try:
                import redis.asyncio as aioredis
                r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                await r.setex(f"blacklist:{jti}", ttl, "revoked")
                await r.close()
                return
            except Exception:
                pass

            # Fallback in-memory
            self._memory_blacklist[jti] = datetime.now(timezone.utc).timestamp() + ttl
        except Exception as e:
            logger.warning("token_revocation_failed", error=str(e))

    async def is_token_revoked(self, token: str) -> bool:
        """Checks whether a token JTI has been revoked."""
        try:
            payload = self.decode_token(token)
            jti = payload.get("jti")
            if not jti:
                return True

            # Check Redis
            try:
                import redis.asyncio as aioredis
                r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                is_revoked = await r.exists(f"blacklist:{jti}")
                await r.close()
                if is_revoked:
                    return True
            except Exception:
                pass

            # Check in-memory fallback
            exp_time = self._memory_blacklist.get(jti)
            if exp_time:
                if datetime.now(timezone.utc).timestamp() < exp_time:
                    return True
                else:
                    self._memory_blacklist.pop(jti, None)

            return False
        except Exception:
            return True

    # --- RFC 8628 OAuth Device Authorization Flow (Task 11.2) ---

    async def generate_device_code(self) -> dict[str, Any]:
        """
        Generates RFC 8628 compliant device and user authorization codes.
        User code is a friendly 8-character string (e.g. 'WDJB-4921').
        """
        charset = "BCDFGHJKLMNPQRSTVWXYZ23456789"
        p1 = "".join(secrets.choice(charset) for _ in range(4))
        p2 = "".join(secrets.choice(charset) for _ in range(4))
        user_code = f"{p1}-{p2}"
        device_code = secrets.token_urlsafe(32)
        expires_in = 600  # 10 minutes

        verification_uri = f"http://{settings.ROOT_DOMAIN}/auth/device"

        # Cache in Redis or memory
        data = {
            "user_code": user_code,
            "status": "pending",
            "user_id": None,
            "expires_at": datetime.now(timezone.utc).timestamp() + expires_in
        }

        try:
            import redis.asyncio as aioredis
            import json
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await r.setex(f"device:{device_code}", expires_in, json.dumps(data))
            await r.setex(f"user_code:{user_code}", expires_in, device_code)
            await r.close()
        except Exception:
            self._memory_device_codes[device_code] = data
            self._memory_user_code_map[user_code] = device_code

        return {
            "device_code": device_code,
            "user_code": user_code,
            "verification_uri": verification_uri,
            "expires_in": expires_in,
            "interval": 5
        }

    async def verify_device_code(self, user_code: str, user_id: str) -> bool:
        """Approves a device authorization session using user_code."""
        clean_code = user_code.strip().upper()
        device_code = None

        # Check Redis
        try:
            import redis.asyncio as aioredis
            import json
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            device_code = await r.get(f"user_code:{clean_code}")
            if device_code:
                raw = await r.get(f"device:{device_code}")
                if raw:
                    data = json.loads(raw)
                    data["status"] = "approved"
                    data["user_id"] = user_id
                    ttl = await r.ttl(f"device:{device_code}")
                    if ttl > 0:
                        await r.setex(f"device:{device_code}", ttl, json.dumps(data))
                    await r.close()
                    return True
            await r.close()
        except Exception:
            pass

        # Check in-memory fallback
        device_code = self._memory_user_code_map.get(clean_code)
        if device_code and device_code in self._memory_device_codes:
            self._memory_device_codes[device_code]["status"] = "approved"
            self._memory_device_codes[device_code]["user_id"] = user_id
            return True

        return False

    async def poll_device_token(self, device_code: str) -> dict[str, Any] | None:
        """Polls status of a device authorization session."""
        # Try Redis
        try:
            import redis.asyncio as aioredis
            import json
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            raw = await r.get(f"device:{device_code}")
            await r.close()
            if raw:
                return json.loads(raw)
        except Exception:
            pass

        # Check in-memory fallback
        item = self._memory_device_codes.get(device_code)
        if item:
            if datetime.now(timezone.utc).timestamp() > item["expires_at"]:
                self._memory_device_codes.pop(device_code, None)
                return None
            return item

        return None

    # --- OAuth 2.0 Handlers (Task 11.1) ---

    @staticmethod
    def get_github_auth_url() -> str:
        """Builds GitHub OAuth 2.0 authorization redirect URL."""
        if not settings.GITHUB_CLIENT_ID:
            raise ValueError("GitHub OAuth is not configured (GITHUB_CLIENT_ID missing).")
        return (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&scope=user:email"
        )

    async def handle_github_callback(self, code: str, db: AsyncSession) -> User:
        """Exchanges GitHub OAuth code, fetches profile, and upserts local User."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_res = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code
                }
            )
            token_data = token_res.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError(f"GitHub OAuth failed: {token_data.get('error_description', 'No access token returned')}")

            # Fetch user info
            user_res = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}", "User-Agent": "Sovereign-Deploy-Platform"}
            )
            gh_user = user_res.json()
            gh_id = str(gh_user["id"])
            gh_username = gh_user.get("login", f"gh_{gh_id}")
            gh_name = gh_user.get("name")
            gh_avatar = gh_user.get("avatar_url")
            gh_email = gh_user.get("email")

            # Fetch primary email if private
            if not gh_email:
                emails_res = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}", "User-Agent": "Sovereign-Deploy-Platform"}
                )
                if emails_res.status_code == 200:
                    emails = emails_res.json()
                    for em in emails:
                        if em.get("primary") and em.get("verified"):
                            gh_email = em.get("email")
                            break

            if not gh_email:
                gh_email = f"{gh_username}@users.noreply.github.com"

            # Upsert User in database
            res = await db.execute(select(User).where((User.oauth_id == gh_id) | (User.email == gh_email)))
            user = res.scalar_one_or_none()

            if not user:
                # Count users to grant admin if first user
                total_users = (await db.execute(select(User))).scalars().all()
                role = "admin" if len(total_users) == 0 else "developer"

                user = User(
                    email=gh_email,
                    username=gh_username,
                    full_name=gh_name,
                    avatar_url=gh_avatar,
                    role=role,
                    oauth_provider="github",
                    oauth_id=gh_id,
                    is_active=True,
                    is_superuser=(role == "admin")
                )
                db.add(user)
            else:
                user.avatar_url = gh_avatar or user.avatar_url
                user.full_name = gh_name or user.full_name
                user.oauth_provider = "github"
                user.oauth_id = gh_id

            await db.commit()
            await db.refresh(user)
            return user

    @staticmethod
    def get_google_auth_url() -> str:
        """Builds Google OAuth 2.0 authorization redirect URL."""
        if not settings.GOOGLE_CLIENT_ID:
            raise ValueError("Google OAuth is not configured (GOOGLE_CLIENT_ID missing).")
        redirect_uri = f"http://api.{settings.ROOT_DOMAIN}/api/v1/auth/google/callback"
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope=openid%20email%20profile"
            f"&access_type=offline"
        )

    async def handle_google_callback(self, code: str, db: AsyncSession) -> User:
        """Exchanges Google OAuth code, fetches profile, and upserts local User."""
        redirect_uri = f"http://api.{settings.ROOT_DOMAIN}/api/v1/auth/google/callback"
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_res = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri
                }
            )
            token_data = token_res.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError(f"Google OAuth failed: {token_data.get('error_description', 'Token exchange failed')}")

            # Fetch user info
            user_res = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            g_user = user_res.json()
            g_id = g_user["id"]
            g_email = g_user["email"]
            g_name = g_user.get("name")
            g_avatar = g_user.get("picture")
            g_username = g_email.split("@")[0]

            res = await db.execute(select(User).where((User.oauth_id == g_id) | (User.email == g_email)))
            user = res.scalar_one_or_none()

            if not user:
                total_users = (await db.execute(select(User))).scalars().all()
                role = "admin" if len(total_users) == 0 else "developer"

                user = User(
                    email=g_email,
                    username=g_username,
                    full_name=g_name,
                    avatar_url=g_avatar,
                    role=role,
                    oauth_provider="google",
                    oauth_id=g_id,
                    is_active=True,
                    is_superuser=(role == "admin")
                )
                db.add(user)
            else:
                user.avatar_url = g_avatar or user.avatar_url
                user.full_name = g_name or user.full_name
                user.oauth_provider = "google"
                user.oauth_id = g_id

            await db.commit()
            await db.refresh(user)
            return user

auth_service = AuthService()
