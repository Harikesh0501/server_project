from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.project import Project
from app.models.deployment import Deployment
from app.schemas.deployment import DeploymentCreate, DeploymentResponse, ReplicaResponse
from app.services.docker_service import docker_service

router = APIRouter(prefix="/deployments", tags=["Deployments"])

def _format_deployment_response(deployment: Deployment, project: Project) -> DeploymentResponse:
    subdomain = project.subdomain if project else "app"
    public_url = f"https://{subdomain}.{settings.ROOT_DOMAIN}"
    
    replicas_data = [
        ReplicaResponse(
            id=r.id,
            container_id=r.container_id,
            container_name=r.container_name,
            replica_index=r.replica_index,
            private_ip=r.private_ip,
            port=r.port,
            status=r.status
        )
        for r in (deployment.replicas or [])
    ]

    return DeploymentResponse(
        id=deployment.id,
        project_id=deployment.project_id,
        project_name=project.name if project else None,
        subdomain=subdomain,
        public_url=public_url,
        status=deployment.status,
        branch=deployment.branch,
        commit_hash=deployment.commit_hash,
        commit_message=deployment.commit_message,
        image_tag=deployment.image_tag,
        active_replicas=deployment.active_replicas,
        build_duration_seconds=deployment.build_duration_seconds,
        error_message=deployment.error_message,
        replicas=replicas_data,
        created_at=deployment.created_at,
        updated_at=deployment.updated_at
    )

@router.post("", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(payload: DeploymentCreate, db: AsyncSession = Depends(get_db)):
    """
    Enqueues a new deployment for a project.
    Validates project existence, sets status to PENDING, and triggers pipeline.
    """
    result = await db.execute(select(Project).where(Project.id == payload.project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {payload.project_id} not found."
        )

    deployment = Deployment(
        project_id=payload.project_id,
        branch=payload.branch or project.git_branch or "main",
        commit_hash=payload.commit_hash,
        commit_message=payload.commit_message or f"Manual deployment via CLI/API ({payload.branch})",
        status="PENDING",
        active_replicas=0
    )

    db.add(deployment)
    await db.commit()
    await db.refresh(deployment)

    return _format_deployment_response(deployment, project)

@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(deployment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetches detailed state of a deployment, including container replicas and public URL.
    """
    query = (
        select(Deployment)
        .where(Deployment.id == deployment_id)
        .options(selectinload(Deployment.project), selectinload(Deployment.replicas))
    )
    result = await db.execute(query)
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID {deployment_id} not found."
        )

    return _format_deployment_response(deployment, deployment.project)

@router.post("/{deployment_id}/cancel", response_model=DeploymentResponse)
async def cancel_deployment(deployment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Terminates a pending, building, or rolling deployment and cleans up starting replicas.
    """
    query = (
        select(Deployment)
        .where(Deployment.id == deployment_id)
        .options(selectinload(Deployment.project), selectinload(Deployment.replicas))
    )
    result = await db.execute(query)
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID {deployment_id} not found."
        )

    if deployment.status in ["ACTIVE", "SUPERSEDED", "FAILED", "CANCELLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel deployment in '{deployment.status}' state."
        )

    # Stop and clean up any containers already created for this deployment
    for replica in deployment.replicas:
        if replica.container_id:
            try:
                await docker_service.stop_container(replica.container_id, timeout=5)
                await docker_service.remove_container(replica.container_id, force=True)
                replica.status = "TERMINATED"
            except Exception:
                pass

    deployment.status = "CANCELLED"
    deployment.error_message = "Deployment cancelled by user request."
    await db.commit()
    await db.refresh(deployment)

    return _format_deployment_response(deployment, deployment.project)

@router.get("", response_model=list[DeploymentResponse])
async def list_deployments(project_id: str | None = None, db: AsyncSession = Depends(get_db)):
    """
    Lists recent deployments, optionally filtered by project_id.
    """
    query = select(Deployment).options(selectinload(Deployment.project), selectinload(Deployment.replicas))
    if project_id:
        query = query.where(Deployment.project_id == project_id)
    query = query.order_by(Deployment.created_at.desc()).limit(50)

    result = await db.execute(query)
    deployments = result.scalars().all()

    return [_format_deployment_response(d, d.project) for d in deployments]
