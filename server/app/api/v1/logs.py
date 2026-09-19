import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session_maker
from app.models.deployment import Deployment
from app.models.log import DeploymentLog
from app.services.secret_service import SecretRedactor

router = APIRouter(prefix="/deployments", tags=["Logs & Streaming"])


async def log_event_generator(deployment_id: str):
    """
    Asynchronous Server-Sent Events (SSE) generator:
    1. Replays historical logs from database.
    2. Streams new incoming logs in real-time.
    3. Sends keep-alive heartbeat comments (: ping) every 15s.
    """
    last_log_id = None

    # Step 1: Historical log playback from DB
    async with async_session_maker() as db:
        query = (
            select(DeploymentLog)
            .where(DeploymentLog.deployment_id == deployment_id)
            .order_by(DeploymentLog.created_at.asc())
        )
        result = await db.execute(query)
        historical_logs = result.scalars().all()

        for log_entry in historical_logs:
            last_log_id = log_entry.id
            payload = {
                "id": log_entry.id,
                "deployment_id": deployment_id,
                "stream": log_entry.stream,
                "message": SecretRedactor.redact(log_entry.message),
                "timestamp": log_entry.created_at.isoformat() if log_entry.created_at else None
            }
            yield f"data: {json.dumps(payload)}\n\n"

    # Step 2: Continuous live tailing with heartbeat
    heartbeat_counter = 0
    while True:
        try:
            await asyncio.sleep(1.0)
            heartbeat_counter += 1

            # Check deployment status to determine if still running
            async with async_session_maker() as db:
                # Fetch any newer logs inserted since last_log_id
                if last_log_id:
                    newer_query = (
                        select(DeploymentLog)
                        .where(
                            DeploymentLog.deployment_id == deployment_id,
                            DeploymentLog.id > last_log_id
                        )
                        .order_by(DeploymentLog.created_at.asc())
                    )
                else:
                    newer_query = (
                        select(DeploymentLog)
                        .where(DeploymentLog.deployment_id == deployment_id)
                        .order_by(DeploymentLog.created_at.asc())
                    )

                res = await db.execute(newer_query)
                new_logs = res.scalars().all()
                for entry in new_logs:
                    last_log_id = entry.id
                    payload = {
                        "id": entry.id,
                        "deployment_id": deployment_id,
                        "stream": entry.stream,
                        "message": SecretRedactor.redact(entry.message),
                        "timestamp": entry.created_at.isoformat() if entry.created_at else None
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

                # Check if deployment finished
                dep_res = await db.execute(select(Deployment.status).where(Deployment.id == deployment_id))
                dep_status = dep_res.scalar_one_or_none()

            # Heartbeat every 15 seconds to prevent browser/Caddy reverse proxy timeout
            if heartbeat_counter >= 15:
                yield ": ping\n\n"
                heartbeat_counter = 0

            # If deployment reached final state and no new logs, send completion event
            if dep_status in ["ACTIVE", "FAILED", "CANCELLED", "SUPERSEDED"] and not new_logs:
                end_payload = {
                    "event": "done",
                    "status": dep_status,
                    "message": f"Deployment log stream ended with status: {dep_status}"
                }
                yield f"event: done\ndata: {json.dumps(end_payload)}\n\n"
                break

        except asyncio.CancelledError:
            # Client disconnected
            break
        except Exception as e:
            err_payload = {"event": "error", "message": str(e)}
            yield f"event: error\ndata: {json.dumps(err_payload)}\n\n"
            await asyncio.sleep(2.0)

@router.get("/{deployment_id}/logs/stream")
async def stream_deployment_logs(deployment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Real-time Server-Sent Events (SSE) log streaming for deployments.
    Delivers historical log replay, live log frames, and periodic ping keep-alives.
    """
    res = await db.execute(select(Deployment.id).where(Deployment.id == deployment_id))
    if not res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {deployment_id} not found."
        )

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    }

    return StreamingResponse(
        log_event_generator(deployment_id),
        media_type="text/event-stream",
        headers=headers
    )

@router.get("/{deployment_id}/logs")
async def get_historical_logs(deployment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetches full static list of historical logs for a deployment.
    """
    query = (
        select(DeploymentLog)
        .where(DeploymentLog.deployment_id == deployment_id)
        .order_by(DeploymentLog.created_at.asc())
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "id": l.id,
            "stream": l.stream,
            "message": SecretRedactor.redact(l.message),
            "timestamp": l.created_at
        }
        for l in logs
    ]

