import hmac
import hashlib
from fastapi import APIRouter, Request, Header, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.project import Project
from app.models.deployment import Deployment

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

def verify_github_signature(payload_body: bytes, signature_header: str | None, secret: str) -> bool:
    """Verifies HMAC SHA-256 signature sent by GitHub Webhook."""
    if not signature_header:
        return False
    if not signature_header.startswith("sha256="):
        return False
    
    expected_hash = signature_header.split("sha256=", 1)[1]
    mac = hmac.new(secret.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), expected_hash)

@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default="push"),
    x_hub_signature_256: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    GitHub Continuous Deployment (CD) Webhook Handler.
    Receives push notifications, verifies HMAC signature, identifies target project,
    and automatically triggers a production deployment pipeline.
    """
    body = await request.body()

    # If secret is configured and not default mock, verify signature
    if settings.WEBHOOK_SECRET and settings.WEBHOOK_SECRET != "sovereign-github-webhook-secret":
        if not verify_github_signature(body, x_hub_signature_256, settings.WEBHOOK_SECRET):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid GitHub webhook HMAC SHA-256 signature."
            )

    # Ping event from GitHub Webhook settings test
    if x_github_event == "ping":
        return {"status": "pong", "message": "GitHub Webhook successfully connected to Sovereign Cloud Engine."}

    if x_github_event != "push":
        return {"status": "ignored", "event": x_github_event, "message": "Only 'push' events trigger deployments."}

    data = await request.json()
    ref = data.get("ref", "")
    branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref

    repo_data = data.get("repository", {})
    clone_url = repo_data.get("clone_url") or repo_data.get("html_url") or ""
    repo_name = repo_data.get("name", "")

    head_commit = data.get("head_commit", {})
    commit_hash = head_commit.get("id")
    commit_message = head_commit.get("message") or f"Auto CD triggered from GitHub push to {branch}"

    # Match project by git_url or name
    stmt = select(Project).where(
        (Project.git_url.ilike(f"%{repo_name}%")) | (Project.name.ilike(repo_name))
    )
    result = await db.execute(stmt)
    projects = result.scalars().all()

    if not projects:
        return {
            "status": "skipped",
            "message": f"No active platform project found associated with repository '{repo_name}' ({clone_url})."
        }

    triggered = []
    for project in projects:
        # Check branch match
        if project.git_branch and project.git_branch != branch:
            continue

        deployment = Deployment(
            project_id=project.id,
            branch=branch,
            commit_hash=commit_hash,
            commit_message=commit_message,
            status="PENDING",
            active_replicas=0
        )
        db.add(deployment)
        await db.flush()
        await db.refresh(deployment)
        triggered.append({"project_id": project.id, "deployment_id": deployment.id})

    await db.commit()

    return {
        "status": "triggered",
        "repository": repo_name,
        "branch": branch,
        "commit": commit_hash[:7] if commit_hash else None,
        "deployments": triggered
    }
