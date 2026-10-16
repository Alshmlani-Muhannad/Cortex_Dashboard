"""Event / evidence records extracted from Cortex XDR alert extra data."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Event(Base, TimestampMixin):
    """A normalized event/evidence record (process, network, file, etc.)."""
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_alert_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    vendor_event_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    raw_response: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    event_type: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    event_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_events_alert_time", "vendor_alert_id", "event_time"),
    )