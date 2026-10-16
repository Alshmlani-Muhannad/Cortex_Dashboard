"""Settings schemas (secrets excluded)."""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AISettingsOut(BaseModel):
    provider: str
    model: str
    base_url: Optional[str] = None
    enabled: bool
    demo_mode: bool
    prompt_version: str
    temperature: float
    max_tokens: int


class IntegrationSettingsOut(BaseModel):
    cortex_configured: bool
    demo_mode: bool
    sync_interval_seconds: int
    page_size: int
    last_sync_time: Optional[str] = None


class SettingsOut(BaseModel):
    ai: AISettingsOut
    integration: IntegrationSettingsOut