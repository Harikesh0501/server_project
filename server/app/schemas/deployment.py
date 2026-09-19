from datetime import datetime
from pydantic import BaseModel, Field

class DeploymentCreate(BaseModel):
    project_id: str = Field(..., description="Target project UUID")
    branch: str = Field(default="main", description="Git branch to deploy")
    commit_hash: str | None = Field(default=None, description="Optional commit SHA")
    commit_message: str | None = Field(default=None, description="Commit message or trigger reason")
    env_vars: dict[str, str] = Field(default_factory=dict, description="Environment variables overrides")

class ReplicaResponse(BaseModel):
    id: str
    container_id: str
    container_name: str
    replica_index: int
    private_ip: str | None = None
    port: int
    status: str

    model_config = {"from_attributes": True}

class DeploymentResponse(BaseModel):
    id: str
    project_id: str
    project_name: str | None = None
    subdomain: str | None = None
    public_url: str | None = None
    status: str
    branch: str
    commit_hash: str | None = None
    commit_message: str | None = None
    image_tag: str | None = None
    active_replicas: int = 0
    build_duration_seconds: float | None = None
    error_message: str | None = None
    replicas: list[ReplicaResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
