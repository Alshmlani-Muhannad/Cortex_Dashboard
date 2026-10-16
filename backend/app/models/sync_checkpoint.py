"""Synchronization checkpoints for incremental sync."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, utcnow


class SyncCheckpoint(Base, TimestampMixin):
    __tablename__ = "sync_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    entity_type: Mapped[str] = mapped_column(String(40), index=True, nullable=False)  # alerts | incidents
    last_sync_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_vendor_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    records_seen: Mapped[int] = mapped_column(default=0, nullable=False)

    __table_args__ = (
        Index("ix_sync_checkpoints_tenant_entity", "tenant_id", "entity_type", unique=True),
    )