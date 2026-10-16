"""Incident-alert relationship model (vendor IDs)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, utcnow


class IncidentAlert(Base, TimestampMixin):
    """Many-to-many link between incidents and alerts using vendor IDs."""
    __tablename__ = "incident_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_incident_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    vendor_alert_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_incident_alerts_unique", "vendor_incident_id", "vendor_alert_id", unique=True),
    )