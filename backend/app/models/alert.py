"""Alert model synchronized from Cortex XDR."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, utcnow


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    # Stable vendor identifier used for deduplication.
    vendor_alert_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    raw_response: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Normalized fields (evidence retained in raw_response).
    alert_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(40), index=True, nullable=True)
    detection_category: Mapped[Optional[str]] = mapped_column(String(200), index=True, nullable=True)
    alert_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(80), index=True, nullable=True)

    creation_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    detection_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    analysis_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    host_name: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    host_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    incident_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    analysis_vendor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_alerts_severity_detection_time", "severity", "detection_time"),
        Index("ix_alerts_host_severity", "host_name", "severity"),
    )