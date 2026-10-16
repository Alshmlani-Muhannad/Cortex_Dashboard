"""Common request/response schemas."""
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class SyncStatusResponse(BaseModel):
    configured: bool
    demo_mode: bool
    last_sync_time: Optional[datetime] = None
    last_sync_entity: Optional[str] = None
    last_job_status: Optional[str] = None
    last_job_error: Optional[str] = None
    connection_status: str  # configured | not_configured | error | demo


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    cortex_configured: bool
    demo_mode: bool
    database: str