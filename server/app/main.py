import time
import uuid
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api.v1.router import api_v1_router
from app.exceptions import rfc7807_exception_handler
from app.services.autoscaler import autoscaler_daemon


# Configure structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20), # INFO level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Platform startup and shutdown lifespan management."""
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    await init_db()
    autoscaler_daemon.start()
    logger.info("platform_started", app=settings.APP_NAME, version=settings.APP_VERSION, host=settings.HOST, port=settings.PORT)
    yield
    await autoscaler_daemon.stop()
    logger.info("platform_shutdown", app=settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="100% Self-Hosted Sovereign Cloud Deployment Platform Control Plane (Vercel + Render Private Cloud Engine)",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structured Request Logging Middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown"
    )

    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info("http_request", status_code=response.status_code, duration_ms=duration_ms)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error("http_request_failed", error=str(exc), duration_ms=duration_ms)
        raise exc

# Global RFC 7807 Exception Handlers
app.add_exception_handler(HTTPException, rfc7807_exception_handler)
app.add_exception_handler(Exception, rfc7807_exception_handler)

# Custom OpenAPI Schema with Bearer Auth Specification
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "### 100% Self-Hosted Universal Cloud Deployment Platform Control Plane (Vercel + Render Sovereign Cloud Engine)\n\n"
            "**Core Capabilities:**\n"
            "- Direct Docker Engine API containerization with cgroups v2 resource limits\n"
            "- Dynamic subdomain allocation & RFC-1123 collision detection\n"
            "- Server-Sent Events (SSE) real-time streaming logs\n"
            "- Automated 3-Tier Polyglot runtime detection & Git continuous deployment\n"
            "- GitHub Webhook receiver with HMAC SHA-256 validation\n"
            "- Zero-trust AES-256-GCM encrypted secrets vault"
        ),
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token or CLI API key: Bearer <token>"
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Register API Routes
app.include_router(api_v1_router)

@app.get("/")

async def root():
    return {
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "api_v1": "/api/v1"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
