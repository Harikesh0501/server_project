from datetime import datetime
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Project display name")
    subdomain: str | None = Field(None, min_length=2, max_length=63, description="Custom subdomain slug (e.g. my-shop)")
    custom_domain: str | None = Field(None, max_length=255, description="Custom vanity domain (e.g. deploy.mycompany.com)")
    git_url: str | None = Field(None, max_length=500, description="Git remote repository URL")
    git_branch: str = Field("main", max_length=100)
    framework: str = Field("unknown", max_length=50)
    runtime_type: str = Field("frontend", max_length=20)
    port: int = Field(3000, ge=1, le=65535)

class ProjectResponse(BaseModel):
    id: str
    name: str
    subdomain: str
    custom_domain: str | None = None
    full_url: str
    framework: str
    runtime_type: str
    git_url: str | None = None
    git_branch: str
    port: int
    min_replicas: int
    max_replicas: int
    created_at: datetime

    class Config:
        from_attributes = True
