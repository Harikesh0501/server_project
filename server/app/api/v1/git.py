import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.project import Project
from app.models.deployment import Deployment
from app.schemas.deployment import DeploymentResponse
from app.api.v1.deployments import _format_deployment_response
from app.worker.orchestrator import DeploymentOrchestrator

router = APIRouter(prefix="/git", tags=["Git Integration"])

class GitDeployRequest(BaseModel):
    project_id: str = Field(..., description="Project UUID to deploy to")
    git_url: str = Field(..., description="Git repository HTTPS or SSH clone URL")
    branch: str = Field(default="main", description="Git branch to clone and deploy")
    commit_hash: str | None = Field(default=None, description="Specific commit hash or tag")

class RepositoryInfo(BaseModel):
    name: str
    url: str
    default_branch: str
    description: str | None = None

def detect_runtime(repo_path: Path) -> dict:
    """
    Automated 3-Tier Polyglot Detection:
    Inspects project root to determine framework, language, and recommended build commands.
    """
    pkg_json = repo_path / "package.json"
    req_txt = repo_path / "requirements.txt"
    pyproject = repo_path / "pyproject.toml"
    dockerfile = repo_path / "Dockerfile"
    cargo_toml = repo_path / "Cargo.toml"
    go_mod = repo_path / "go.mod"

    if dockerfile.exists():
        return {"framework": "dockerfile", "runtime_type": "backend", "port": 8080}

    if pkg_json.exists():
        try:
            content = pkg_json.read_text(encoding="utf-8")
            if "next" in content:
                return {"framework": "nextjs", "runtime_type": "frontend", "port": 3000}
            if "vite" in content or "react-scripts" in content:
                return {"framework": "react", "runtime_type": "frontend", "port": 80}
            if "express" in content or "nest" in content or "fastify" in content:
                return {"framework": "nodejs", "runtime_type": "backend", "port": 3000}
            return {"framework": "node", "runtime_type": "frontend", "port": 3000}
        except Exception:
            return {"framework": "node", "runtime_type": "frontend", "port": 3000}

    if req_txt.exists() or pyproject.exists():
        return {"framework": "fastapi", "runtime_type": "backend", "port": 8000}

    if go_mod.exists():
        return {"framework": "go", "runtime_type": "backend", "port": 8080}

    if cargo_toml.exists():
        return {"framework": "rust", "runtime_type": "backend", "port": 8080}

    return {"framework": "generic", "runtime_type": "backend", "port": 8080}

@router.get("/repositories", response_model=list[RepositoryInfo])
async def list_repositories(db: AsyncSession = Depends(get_db)):
    """
    Lists connected repositories across all configured projects.
    """
    result = await db.execute(select(Project).where(Project.git_url.is_not(None)))
    projects = result.scalars().all()

    repos = []
    seen = set()
    for p in projects:
        if p.git_url and p.git_url not in seen:
            seen.add(p.git_url)
            repo_name = p.git_url.rstrip("/").split("/")[-1].replace(".git", "")
            repos.append(
                RepositoryInfo(
                    name=repo_name,
                    url=p.git_url,
                    default_branch=p.git_branch or "main",
                    description=f"Connected to project: {p.name}"
                )
            )
    return repos

@router.post("/deploy", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def git_deploy(payload: GitDeployRequest, db: AsyncSession = Depends(get_db)):
    """
    Clones git repository into an isolated sandbox, auto-detects framework/runtime,
    updates project metadata, and triggers a new deployment.
    """
    result = await db.execute(select(Project).where(Project.id == payload.project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {payload.project_id} not found."
        )

    # Sandbox build directory
    build_dir = Path(settings.BUILD_WORKSPACE_DIR) / f"build_{payload.project_id}"
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    # Clone git repository (depth 1 for high speed)
    clone_cmd = [
        "git", "clone",
        "--depth", "1",
        "--branch", payload.branch,
        payload.git_url,
        str(build_dir)
    ]

    commit_hash = payload.commit_hash
    commit_msg = f"Deploy branch: {payload.branch}"
    try:
        res = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=120)
        if res.returncode == 0:
            # Extract latest commit details
            log_res = subprocess.run(
                ["git", "log", "-1", "--format=%H|%s"],
                cwd=str(build_dir),
                capture_output=True,
                text=True
            )
            if log_res.returncode == 0 and "|" in log_res.stdout:
                parts = log_res.stdout.strip().split("|", 1)
                commit_hash = parts[0]
                commit_msg = parts[1]

            # Polyglot runtime detection
            detected = detect_runtime(build_dir)
            if project.framework == "unknown":
                project.framework = detected["framework"]
                project.runtime_type = detected["runtime_type"]
                project.port = detected["port"]
    except Exception as e:
        # Fallback if git binary not in PATH or shallow clone fails
        commit_msg = f"Git deploy triggered for {payload.branch}: {str(e)}"

    # Update project git references
    project.git_url = payload.git_url
    project.git_branch = payload.branch

    # Create new deployment
    deployment = Deployment(
        project_id=project.id,
        branch=payload.branch,
        commit_hash=commit_hash,
        commit_message=commit_msg,
        status="PENDING",
        active_replicas=0
    )

    db.add(deployment)
    await db.commit()
    await db.refresh(deployment)

    # Dispatch automated build & Caddy routing pipeline
    asyncio.create_task(DeploymentOrchestrator.run_pipeline(deployment.id))

    return _format_deployment_response(deployment, project)

