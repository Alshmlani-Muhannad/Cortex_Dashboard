"""AI analysis schemas (structured output contract)."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EvidenceReference(BaseModel):
    alert_id: Optional[str] = None
    field: Optional[str] = None
    value: Optional[str] = None


class AIAnalysisResult(BaseModel):
    summary: str
    severity_assessment: str
    confidence: float = Field(ge=0.0, le=1.0)
    observed_evidence: List[str] = Field(default_factory=list)
    potential_techniques: List[Dict[str, Any]] = Field(default_factory=list)
    false_positive_considerations: List[str] = Field(default_factory=list)
    recommended_investigations: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    evidence_references: List[EvidenceReference] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    hypothesis_flags: List[str] = Field(default_factory=list, description="Statements that are hypotheses, not verified observations")


class AnalyzeRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    force_refresh: bool = False


class AnalyzeResponse(BaseModel):
    analysis_id: str
    vendor_alert_id: Optional[str] = None
    vendor_incident_id: Optional[str] = None
    model_name: str
    prompt_version: str
    analysis_timestamp: datetime
    result: AIAnalysisResult
    is_demo: bool
    cached: bool


class AnalysisOut(BaseModel):
    id: str
    vendor_alert_id: Optional[str]
    vendor_incident_id: Optional[str]
    model_name: str
    prompt_version: str
    analysis_timestamp: datetime
    result: AIAnalysisResult
    evidence_references: Optional[Dict[str, Any]]
    is_demo: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)