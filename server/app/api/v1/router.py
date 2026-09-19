from fastapi import APIRouter
from app.api.v1 import health, domains, projects, deployments, git, webhooks, logs, secrets, metrics, databases

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health.router)
api_v1_router.include_router(domains.router)
api_v1_router.include_router(projects.router)
api_v1_router.include_router(deployments.router)
api_v1_router.include_router(git.router)
api_v1_router.include_router(webhooks.router)
api_v1_router.include_router(logs.router)
api_v1_router.include_router(secrets.router)
api_v1_router.include_router(metrics.router)
api_v1_router.include_router(databases.router)


