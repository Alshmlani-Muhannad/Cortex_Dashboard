"""Alert schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AlertBase(BaseModel):
    vendor_alert_id: str
    tenant_id: Optional[str] = None
    alert_name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    detection_category: Optional[str] = None
    alert_type: Optional[str] = None
    status: Optional[str] = None
    creation_time: Optional[datetime] = None
    detection_time: Optional[datetime] = None
    analysis_time: Optional[datetime] = None
    host_name: Optional[str] = None
    host_id: Optional[str] = None
    user_name: Optional[str] = None
    incident_id: Optional[str] = None
    analysis_vendor: Optional[str] = None
    raw_response: Dict[str, Any] = Field(default_factory=dict)


class AlertOut(AlertBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertFilterParams(BaseModel):
    severity: Optional[str] = None
    time_range: Optional[str] = None  # e.g. "24h", "7d", "30d"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    endpoint: Optional[str] = None  # host_name
    detection_category: Optional[str] = None
    status: Optional[str] = None
    incident_id: Optional[str] = None
    search: Optional[str] = None
    sort_field: Optional[str] = "detection_time"
    sort_order: Optional[str] = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)