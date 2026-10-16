"""Settings endpoints (secrets excluded)."""
from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.core.config import settings
from app.schemas.settings import SettingsOut, AISettingsOut, IntegrationSettingsOut

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/ai", response_model=AISettingsOut)
def ai_settings(user=Depends(require_user)):
    return AISettingsOut(
        provider=settings.AI_PROVIDER,
        model=settings.AI_MODEL,
        base_url=settings.AI_BASE_URL,
        enabled=settings.AI_ENABLED,
        demo_mode=settings.AI_DEMO_MODE,
        prompt_version=settings.AI_PROMPT_VERSION,
        temperature=settings.AI_TEMPERATURE,
        max_tokens=settings.AI_MAX_TOKENS,
    )


@router.get("/integration", response_model=IntegrationSettingsOut)
def integration_settings(user=Depends(require_user)):
    return IntegrationSettingsOut(
        cortex_configured=bool(
            settings.CORTEX_TENANT_FQDN and settings.CORTEX_API_KEY_ID and settings.CORTEX_API_KEY
        ),
        demo_mode=settings.CORTEX_DEMO_MODE,
        sync_interval_seconds=settings.CORTEX_SYNC_INTERVAL_SECONDS,
        page_size=settings.CORTEX_SYNC_PAGE_SIZE,
    )