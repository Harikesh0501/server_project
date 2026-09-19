import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.project import Project
from app.schemas.domain import DomainCheckResponse

RESERVED_SUBDOMAINS = {
    "api",
    "registry",
    "admin",
    "dashboard",
    "www",
    "localhost",
    "deploy",
    "status",
    "health",
    "metrics",
    "auth",
    "login",
    "setup",
    "static",
    "cdn"
}

def sanitize_slug(name: str) -> str:
    """Converts a raw string into an RFC-1123 compliant DNS subdomain slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\-]", "-", slug)
    slug = re.sub(r"\-+", "-", slug)
    slug = slug.strip("-")
    return slug[:63]

class DomainService:
    @staticmethod
    async def is_slug_taken(slug: str, db: AsyncSession) -> bool:
        """Checks if a slug is reserved or already registered in the projects table."""
        if slug in RESERVED_SUBDOMAINS:
            return True
        result = await db.execute(select(Project.id).where(Project.subdomain == slug))
        return result.scalar_one_or_none() is not None

    @classmethod
    async def check_availability(cls, raw_name: str, db: AsyncSession) -> DomainCheckResponse:
        """Validates subdomain slug availability and provides alternative suggestions if taken."""
        slug = sanitize_slug(raw_name)

        if not slug:
            return DomainCheckResponse(
                name=raw_name,
                available=False,
                full_domain=f"{raw_name}.{settings.ROOT_DOMAIN}",
                message="Domain name contains invalid characters. Use letters, numbers, and hyphens.",
                suggestions=["app-1", "my-project", "service-live"]
            )

        taken = await cls.is_slug_taken(slug, db)
        full_domain = f"{slug}.{settings.ROOT_DOMAIN}"

        if not taken:
            return DomainCheckResponse(
                name=slug,
                available=True,
                full_domain=full_domain,
                message=f"✔ Domain '{slug}' is available!",
                suggestions=[]
            )

        # Generate smart alternative suggestions
        base_candidates = [
            f"{slug}-app",
            f"{slug}-2",
            f"{slug}-live",
            f"{slug}-cloud",
            f"my-{slug}"
        ]

        free_suggestions = []
        for cand in base_candidates:
            if len(free_suggestions) >= 3:
                break
            cand_slug = sanitize_slug(cand)
            if not await cls.is_slug_taken(cand_slug, db):
                free_suggestions.append(cand_slug)

        return DomainCheckResponse(
            name=slug,
            available=False,
            full_domain=full_domain,
            message=f"❌ Domain '{slug}' already exists! Please choose another name.",
            suggestions=free_suggestions
        )
