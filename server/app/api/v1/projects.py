from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.domain_service import DomainService, sanitize_slug

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new project and reserves its unique subdomain."""
    target_slug = payload.subdomain or payload.name
    slug = sanitize_slug(target_slug)

    # Verify subdomain availability
    domain_check = await DomainService.check_availability(slug, db)
    if not domain_check.available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": domain_check.message,
                "domain": domain_check.full_domain,
                "suggestions": domain_check.suggestions
            }
        )

    # Create new project record
    project = Project(
        name=payload.name,
        subdomain=slug,
        custom_domain=payload.custom_domain,
        framework=payload.framework,
        runtime_type=payload.runtime_type,
        git_url=payload.git_url,
        git_branch=payload.git_branch,
        port=payload.port
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        subdomain=project.subdomain,
        custom_domain=project.custom_domain,
        full_url=f"https://{project.subdomain}.{settings.ROOT_DOMAIN}",
        framework=project.framework,
        runtime_type=project.runtime_type,
        git_url=project.git_url,
        git_branch=project.git_branch,
        port=project.port,
        min_replicas=project.min_replicas,
        max_replicas=project.max_replicas,
        created_at=project.created_at
    )

@router.get("", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """Lists all registered projects on the platform."""
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()

    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            subdomain=p.subdomain,
            custom_domain=p.custom_domain,
            full_url=f"https://{p.subdomain}.{settings.ROOT_DOMAIN}",
            framework=p.framework,
            runtime_type=p.runtime_type,
            git_url=p.git_url,
            git_branch=p.git_branch,
            port=p.port,
            min_replicas=p.min_replicas,
            max_replicas=p.max_replicas,
            created_at=p.created_at
        )
        for p in projects
    ]

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Fetches details for a specific project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return ProjectResponse(
        id=project.id,
        name=project.name,
        subdomain=project.subdomain,
        custom_domain=project.custom_domain,
        full_url=f"https://{project.subdomain}.{settings.ROOT_DOMAIN}",
        framework=project.framework,
        runtime_type=project.runtime_type,
        git_url=project.git_url,
        git_branch=project.git_branch,
        port=project.port,
        min_replicas=project.min_replicas,
        max_replicas=project.max_replicas,
        created_at=project.created_at
    )
