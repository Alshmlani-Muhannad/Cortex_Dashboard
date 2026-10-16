"""Incident model synchronized from Cortex XDR."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, utcnow


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    vendor_incident_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    raw_response: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    incident_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(40), index=True, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(80), index=True, nullable=True)

    creation_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    detection_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_update_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    host_name: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    user_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_incidents_severity_status", "severity", "status"),
        Index("ix_incidents_detection_time", "detection_time"),
    )