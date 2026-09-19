from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class DatabaseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Database instance identifier (e.g. 'primary-db')")
    engine: Literal["postgres", "redis"] = Field(..., description="Database engine type ('postgres' or 'redis')")
    project_id: str = Field(..., description="UUID of associated project for secret auto-injection")
    version: str = Field(default="16", description="Database engine version (default: '16' for PG, '7' for Redis)")

class DatabaseResponse(BaseModel):
    id: str
    project_id: str
    name: str
    engine: str
    version: str
    port: int
    database_name: str
    username: str
    status: str
    connection_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

class DatabaseBackupResponse(BaseModel):
    database_id: str
    backup_filename: str
    backup_path: str
    size_bytes: int
    created_at: str
