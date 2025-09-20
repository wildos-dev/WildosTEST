import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi_pagination import add_pagination
from starlette.staticfiles import StaticFiles
from uvicorn import Config, Server

from app.config.env import (
    DEBUG,
    DOCS,
    HOME_PAGE_TEMPLATE,
    UVICORN_HOST,
    UVICORN_PORT,
    UVICORN_SSL_CERTFILE,
    UVICORN_SSL_KEYFILE,
    UVICORN_UDS,
    DASHBOARD_PATH,
    TASKS_RECORD_USER_USAGES_INTERVAL,
    TASKS_REVIEW_USERS_INTERVAL,
    TASKS_EXPIRE_DAYS_REACHED_INTERVAL,
    TASKS_RESET_USER_DATA_USAGE,
    CORS_ALLOWED_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
)
from app.middleware import (
    DiskSpaceMiddleware, 
    RateLimitingMiddleware, 
    ProxyHeadersMiddleware
)
from app.routes.system_health import router as system_health_router
from app.templates import render_template
from . import __version__, setup_system_monitoring
from .routes import api_router
from .tasks import (
    nodes_startup,
    record_user_usages,
    reset_user_data_usage,
    review_users,
    expire_days_reached,
)
from .webhooks import webhooks_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize system monitoring
    setup_system_monitoring()
    
    # Start node connections
    await nodes_startup()
    
    # Start rate limiting cleanup task  
    try:
        from app.middleware.rate_limiting import start_cleanup_task
        asyncio.create_task(start_cleanup_task())
        logger.info("Rate limiting cleanup task started")
    except ImportError:
        logger.info("Rate limiting cleanup task not available")
    
    logger.info("Application startup completed with enhanced monitoring")
    yield
    
    logger.info("Application shutting down")
    scheduler.shutdown()


app = FastAPI(
    title="WildosVPN API",
    description="Unified GUI Censorship Resistant Solution Powered by Xray",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs" if DOCS else None,
    redoc_url="/redoc" if DOCS else None,
)

app.include_router(webhooks_router)

app.include_router(api_router)
app.include_router(system_health_router)
add_pagination(app)

# Add security and monitoring middleware (order matters!)
# 1. Proxy headers processing (first)
app.add_middleware(ProxyHeadersMiddleware, trusted_proxies=["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"])

# 2. Rate limiting (after proxy headers for proper IP resolution)
app.add_middleware(RateLimitingMiddleware)

# 3. Disk space monitoring
app.add_middleware(DiskSpaceMiddleware, critical_threshold=95, warning_threshold=85)


@app.get("/", response_class=HTMLResponse)
def home_page():
    return render_template(HOME_PAGE_TEMPLATE)


# SECURITY: Use environment-configured CORS origins instead of wildcard
# Ensure CORS_ALLOWED_ORIGINS is a list of strings
cors_origins = CORS_ALLOWED_ORIGINS if isinstance(CORS_ALLOWED_ORIGINS, list) else ["http://localhost:3000"]

# SECURITY: Strict guard against dangerous CORS configuration
if CORS_ALLOW_CREDENTIALS and ("*" in cors_origins or cors_origins == ["*"]):
    raise ValueError(
        "SECURITY: CORS_ALLOW_CREDENTIALS=True cannot be used with wildcard origins (*). "
        "This creates a CSRF vulnerability. Either set CORS_ALLOW_CREDENTIALS=False "
        "or specify explicit origins in CORS_ALLOWED_ORIGINS."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    expose_headers=["X-Total-Count"],
)

scheduler = AsyncIOScheduler(timezone="UTC")
scheduler.add_job(
    record_user_usages,
    "interval",
    coalesce=True,
    seconds=TASKS_RECORD_USER_USAGES_INTERVAL,
)
scheduler.add_job(
    review_users,
    "interval",
    seconds=TASKS_REVIEW_USERS_INTERVAL,
    coalesce=True,
    max_instances=1,
)
scheduler.add_job(
    expire_days_reached,
    "interval",
    seconds=TASKS_EXPIRE_DAYS_REACHED_INTERVAL,
    coalesce=True,
    max_instances=1,
)
scheduler.add_job(
    reset_user_data_usage,
    "interval",
    seconds=TASKS_RESET_USER_DATA_USAGE,
    coalesce=True,
)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    details = {}
    for error in exc.errors():
        details[error["loc"][-1]] = error.get("msg")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": details}),
    )


async def main():
    if not DEBUG and os.path.exists("dashboard/dist"):
        app.mount(
            DASHBOARD_PATH,
            StaticFiles(directory="dashboard/dist", html=True),
            name="dashboard",
        )
        if os.path.exists("dashboard/dist/static"):
            app.mount(
                "/static/",
                StaticFiles(directory="dashboard/dist/static"),
                name="static",
            )
        if os.path.exists("dashboard/dist/locales"):
            app.mount(
                "/locales/",
                StaticFiles(directory="dashboard/dist/locales"),
                name="locales",
            )
    scheduler.start()
    cfg = Config(
        app=app,
        host=UVICORN_HOST,
        port=UVICORN_PORT,
        uds=(None if DEBUG else UVICORN_UDS),
        ssl_certfile=UVICORN_SSL_CERTFILE,
        ssl_keyfile=UVICORN_SSL_KEYFILE,
        workers=1,
        reload=DEBUG,
        log_level=logging.DEBUG if DEBUG else logging.INFO,
        access_log=False,  # Отключаем access логи для health checks
    )
    server = Server(cfg)
    await server.serve()