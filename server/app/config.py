import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Platform Metadata
    APP_NAME: str = "Sovereign Deploy Cloud Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Server Bindings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Base Domains
    ROOT_DOMAIN: str = "deploy.local"
    API_SUBDOMAIN: str = "api"
    REGISTRY_SUBDOMAIN: str = "registry"

    # Storage & Vault Paths
    DATA_DIR: Path = Path("/var/lib/deploy") if os.name != "nt" else BASE_DIR / "data"
    BUILD_WORKSPACE_DIR: Path = Path("/tmp/deploy_builds") if os.name != "nt" else BASE_DIR / "data" / "builds"
    MASTER_KEY_FILE: Path = Path("/etc/deploy/master.key") if os.name != "nt" else BASE_DIR / "data" / "master.key"

    # Database Configuration (Defaults to SQLite for instant dev, PostgreSQL for production)
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./deploy_platform.db",
        description="Async SQLAlchemy database URL"
    )

    # Redis Configuration
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # Security & Auth
    JWT_SECRET: str = "sovereign-super-secret-jwt-signing-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    WEBHOOK_SECRET: str = "sovereign-github-webhook-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # OAuth 2.0 Client Credentials
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""


    # Docker Engine API Socket
    DOCKER_SOCKET: str = "/var/run/docker.sock" if os.name != "nt" else "npipe:////./pipe/docker_engine"
    DOCKER_PRIVATE_NETWORK: str = "deploy-private-net"

    # Caddy Admin API
    CADDY_ADMIN_URL: str = "http://127.0.0.1:2019"

    # Ollama Local AI Engine
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_DEFAULT_MODEL: str = "mistral:7b-instruct"

    # CORS Allowed Origins
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://deploy.local",
        "https://deploy.local",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
