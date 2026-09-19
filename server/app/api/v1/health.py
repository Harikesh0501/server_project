import time
import psutil
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])

START_TIME = time.time()

@router.get("")
async def get_health_status(db: AsyncSession = Depends(get_db)):
    """System health check and runtime metrics."""
    # Test database connectivity
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Host system resource utilization
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    uptime_seconds = int(time.time() - START_TIME)

    return {
        "status": "healthy" if db_ok else "degraded",
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime_seconds,
        "database_connected": db_ok,
        "system_metrics": {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_mb": round(memory.available / (1024 * 1024), 2)
        }
    }
