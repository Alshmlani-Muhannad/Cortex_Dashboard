"""FastAPI application entry point."""
import logging

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine, SessionLocal, init_db
from app.models.user import User
from app.core.security import hash_password

from app.api.endpoints import health, auth, dashboard, alerts, incidents, sync, settings as settings_ep, analysis
from app.api.endpoints.analysis import alert_router

logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger("app")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"error": "Rate limit exceeded", "detail": str(exc)})


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
API_PREFIX = "/api"
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(alerts.router, prefix=API_PREFIX)
app.include_router(incidents.router, prefix=API_PREFIX)
app.include_router(alert_router, prefix=API_PREFIX)  # alert analysis
app.include_router(analysis.router, prefix=API_PREFIX)  # incident analyze + chat
app.include_router(sync.router, prefix=API_PREFIX)
app.include_router(settings_ep.router, prefix=API_PREFIX)


@app.on_event("startup")
def on_startup():
    # Bootstrap default admin in dev when no users exist.
    db = SessionLocal()
    try:
        if not db.query(User).first():
            admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                role="admin",
            )
            db.add(admin)
            db.commit()
            logger.info("Bootstrapped default admin user")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not bootstrap admin: %s", exc)
    finally:
        db.close()


@app.get("/api", tags=["root"])
def root():
    return {"service": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs"}