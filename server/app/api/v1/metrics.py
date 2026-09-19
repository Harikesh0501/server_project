import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db, async_session_maker
from app.models.deployment import Deployment
from app.models.autoscale import AutoscaleEvent
from app.services.autoscaler import autoscaler_daemon
from app.services.docker_service import docker_service

router = APIRouter(prefix="/deployments", tags=["Metrics & Autoscaling"])

@router.get("/{deployment_id}/metrics")
async def get_deployment_metrics(deployment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns immediate real-time metrics for a deployment's replicas (CPU, RAM, IPs).
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
            detail=f"Deployment {deployment_id} not found."
        )

    # Check cached metrics first
    cached = autoscaler_daemon.get_cached_metrics(deployment_id)
    if cached:
        return cached

    # Fallback on-demand calculation if daemon has not sampled yet
    replica_stats = []
    total_cpu = 0.0
    total_mem_mb = 0.0

    for rep in (deployment.replicas or []):
        try:
            stats = await docker_service.get_container_stats(rep.container_id)
            total_cpu += stats["cpu_percent"]
            total_mem_mb += stats["memory_usage_mb"]
            replica_stats.append({
                "container_id": rep.container_id[:12],
                "container_name": rep.container_name,
                "private_ip": rep.private_ip,
                "port": rep.port,
                "cpu_percent": stats["cpu_percent"],
                "memory_mb": stats["memory_usage_mb"],
                "memory_percent": stats["memory_percent"],
                "status": rep.status
            })
        except Exception:
            replica_stats.append({
                "container_id": rep.container_id[:12] if rep.container_id else "unknown",
                "container_name": rep.container_name,
                "private_ip": rep.private_ip,
                "port": rep.port,
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "memory_percent": 0.0,
                "status": "UNREACHABLE"
            })

    count = len(replica_stats) or 1
    project = deployment.project
    return {
        "deployment_id": deployment.id,
        "project_name": project.name if project else "Unknown",
        "subdomain": project.subdomain if project else "unknown",
        "active_replicas": len(deployment.replicas or []),
        "min_replicas": project.min_replicas if project else 3,
        "max_replicas": project.max_replicas if project else 10,
        "average_cpu_percent": round(total_cpu / count, 2),
        "average_memory_mb": round(total_mem_mb / count, 2),
        "replicas": replica_stats
    }

async def metrics_event_generator(deployment_id: str):
    """
    SSE stream generating real-time CPU & RAM metrics every 2 seconds for CLI / Dashboard.
    """
    heartbeat = 0
    while True:
        try:
            metrics = autoscaler_daemon.get_cached_metrics(deployment_id)
            if metrics:
                yield f"data: {json.dumps(metrics)}\n\n"
            else:
                yield f"data: {json.dumps({'deployment_id': deployment_id, 'status': 'sampling'})}\n\n"

            await asyncio.sleep(2.0)
            heartbeat += 2
            if heartbeat >= 16:
                yield ": ping\n\n"
                heartbeat = 0
        except asyncio.CancelledError:
            break
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            await asyncio.sleep(2.0)

@router.get("/{deployment_id}/metrics/stream")
async def stream_deployment_metrics(deployment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Streams live container telemetry via Server-Sent Events (SSE) (Mini-Task 9.5.1).
    Powers real-time charts in the Web Console and CLI `deploy top` TUI.
    """
    res = await db.execute(select(Deployment.id).where(Deployment.id == deployment_id))
    if not res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found."
        )

    return StreamingResponse(
        metrics_event_generator(deployment_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/{deployment_id}/autoscale/events")
async def list_autoscale_events(deployment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns historical scale-up and scale-down audit events for a deployment (Mini-Task 9.2.7 & 9.3.7).
    """
    query = (
        select(AutoscaleEvent)
        .where(AutoscaleEvent.deployment_id == deployment_id)
        .order_by(AutoscaleEvent.created_at.desc())
    )
    result = await db.execute(query)
    events = result.scalars().all()

    return [
        {
            "id": ev.id,
            "project_id": ev.project_id,
            "deployment_id": ev.deployment_id,
            "action": ev.action,
            "old_replicas": ev.old_replicas,
            "new_replicas": ev.new_replicas,
            "trigger_reason": ev.trigger_reason,
            "cpu_percent": ev.cpu_percent,
            "timestamp": ev.created_at.isoformat() if ev.created_at else None
        }
        for ev in events
    ]
