"""AI analysis results (read-only, advisory)."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, utcnow


class AIAnalysis(Base, TimestampMixin):
    __tablename__ = "ai_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_alert_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    vendor_incident_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(100), nullable=False)
    analysis_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    # Structured analysis result validated against the AI schema.
    result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # Non-sensitive evidence references only (alert IDs, field names).
    evidence_references: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)

    __table_args__ = (
        Index("ix_ai_analyses_alert_ts", "vendor_alert_id", "analysis_timestamp"),
        Index("ix_ai_analyses_incident_ts", "vendor_incident_id", "analysis_timestamp"),
    )