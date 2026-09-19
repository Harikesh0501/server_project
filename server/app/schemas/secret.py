from datetime import datetime
from pydantic import BaseModel, Field

class SecretCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=100, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    value: str = Field(..., min_length=0)

class SecretBulkCreate(BaseModel):
    secrets: dict[str, str] = Field(..., description="Key-value mapping of secrets to encrypt and store")

class SecretResponse(BaseModel):
    id: str
    project_id: str
    key: str
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
