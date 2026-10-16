"""Health endpoint."""
from fastapi import APIRouter, Depends

from app.api.deps import get_db
from app.core.config import settings, get_settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db=Depends(get_db)):
    db_status = "ok"
    try:
        db.execute("SELECT 1")
    except Exception as exc:  # noqa: BLE001
        db_status = f"error: {exc}"
    s = get_settings()
    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=s.ENVIRONMENT,
        cortex_configured=bool(s.CORTEX_TENANT_FQDN and s.CORTEX_API_KEY_ID and s.CORTEX_API_KEY),
        demo_mode=s.CORTEX_DEMO_MODE or s.AI_DEMO_MODE,
        database=db_status,
    )