"""Application configuration loaded from environment variables.

Secrets (Cortex API keys, DB credentials, LLM keys) must never be returned
by any API route or written to logs. See .env.example for placeholders.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Application ---
    APP_NAME: str = "Cortex XDR AI-Powered SOC Dashboard"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="development | staging | production")
    DEBUG: bool = Field(default=False)
    API_V1_STR: str = "/api"
    FRONTEND_ORIGIN: str = Field(default="http://localhost:5173")
    BACKEND_CORS_ORIGINS: List[str] = Field(default=["http://localhost:5173"])

    # --- Security ---
    SECRET_KEY: str = Field(default="dev-secret-change-me", description="JWT signing secret (must be strong in prod)")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7)
    BCRYPT_ROUNDS: int = Field(default=12)
    # Default admin bootstrapped when no users exist (dev only). Change in production.
    DEFAULT_ADMIN_EMAIL: str = Field(default="admin@example.local")
    DEFAULT_ADMIN_PASSWORD: str = Field(default="admin123")
    DEFAULT_ADMIN_USERNAME: str = Field(default="admin")

    # --- Database ---
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://soc:socpassword@localhost:5432/socdb",
        description="SQLAlchemy sync database URL",
    )
    DATABASE_URL_ASYNC: Optional[str] = Field(default=None)

    # --- Cortex XDR Integration ---
    CORTEX_TENANT_FQDN: Optional[str] = Field(
        default=None,
        description="Tenant FQDN, e.g. https://<tenant>.api.cortexdata.panw.io",
    )
    CORTEX_API_KEY_ID: Optional[str] = Field(default=None)
    CORTEX_API_KEY: Optional[str] = Field(default=None, exclude=True)
    CORTEX_API_VERSION: str = Field(default="v1")
    CORTEX_REQUEST_TIMEOUT_SECONDS: int = Field(default=30)
    CORTEX_MAX_RETRIES: int = Field(default=4)
    CORTEX_BASE_BACKOFF_SECONDS: float = Field(default=1.0)
    CORTEX_SYNC_INTERVAL_SECONDS: int = Field(default=300, description="Automatic sync interval (0 disables)")
    CORTEX_SYNC_PAGE_SIZE: int = Field(default=100)
    CORTEX_DEMO_MODE: bool = Field(default=False, description="Enable unlabeled-free synthetic demo data")

    # --- AI (provider-agnostic) ---
    AI_PROVIDER: str = Field(default="openai", description="openai | anthropic | local | mock")
    AI_MODEL: str = Field(default="gpt-4o-mini")
    AI_BASE_URL: Optional[str] = Field(default=None)
    AI_API_KEY: Optional[str] = Field(default=None, exclude=True)
    AI_PROMPT_VERSION: str = Field(default="v1.0")
    AI_TEMPERATURE: float = Field(default=0.2)
    AI_MAX_TOKENS: int = Field(default=1500)
    AI_ENABLED: bool = Field(default=True)
    AI_DEMO_MODE: bool = Field(default=False, description="Return structured synthetic analysis without calling an LLM")

    # --- Rate limiting / audit ---
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60)

    @validator("CORTEX_TENANT_FQDN", pre=True, always=True)
    def _strip_trailing_slash(cls, v):
        if v:
            return v.rstrip("/")
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def redacted_settings_dict() -> dict:
    """Return a safe, loggable view of settings with secrets removed."""
    s = get_settings()
    return {
        "APP_NAME": s.APP_NAME,
        "ENVIRONMENT": s.ENVIRONMENT,
        "DEBUG": s.DEBUG,
        "CORTEX_CONFIGURED": bool(s.CORTEX_TENANT_FQDN and s.CORTEX_API_KEY_ID and s.CORTEX_API_KEY),
        "CORTEX_DEMO_MODE": s.CORTEX_DEMO_MODE,
        "AI_PROVIDER": s.AI_PROVIDER,
        "AI_MODEL": s.AI_MODEL,
        "AI_ENABLED": s.AI_ENABLED,
        "AI_DEMO_MODE": s.AI_DEMO_MODE,
        "SYNC_INTERVAL_SECONDS": s.CORTEX_SYNC_INTERVAL_SECONDS,
    }