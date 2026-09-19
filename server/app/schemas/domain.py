from pydantic import BaseModel, Field

class DomainCheckResponse(BaseModel):
    name: str = Field(..., description="Requested subdomain slug")
    available: bool = Field(..., description="Whether the domain is free to use")
    full_domain: str = Field(..., description="Full FQDN domain string (e.g. my-shop.deploy.local)")
    message: str = Field(..., description="User-friendly status message in English / Gujarati")
    suggestions: list[str] = Field(default_factory=list, description="Alternative suggestions if name is already taken")
