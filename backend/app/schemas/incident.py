"""Incident schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class IncidentBase(BaseModel):
    vendor_incident_id: str
    tenant_id: Optional[str] = None
    incident_name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    creation_time: Optional[datetime] = None
    detection_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None
    host_name: Optional[str] = None
    user_name: Optional[str] = None
    raw_response: Dict[str, Any] = Field(default_factory=dict)
    alert_ids: List[str] = Field(default_factory=list)


class IncidentOut(IncidentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentFilterParams(BaseModel):
    severity: Optional[str] = None
    status: Optional[str] = None
    time_range: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    endpoint: Optional[str] = None
    search: Optional[str] = None
    sort_field: Optional[str] = "detection_time"
    sort_order: Optional[str] = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)