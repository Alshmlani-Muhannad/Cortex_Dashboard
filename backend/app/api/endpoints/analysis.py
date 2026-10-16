"""AI analysis endpoints."""
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_user, get_db
from app.core.config import settings
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.ai_analysis import AIAnalysis
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse, AIAnalysisResult
from app.services.ai_service import AIService, get_disclaimer

router = APIRouter(prefix="/incidents", tags=["analysis"])


def _build_evidence_from_alert(db, alert: Alert) -> Dict[str, Any]:
    return {
        "alert_id": alert.vendor_alert_id,
        "alert_name": alert.alert_name,
        "description": alert.description,
        "severity": alert.severity,
        "detection_category": alert.detection_category,
        "status": alert.status,
        "host_name": alert.host_name,
        "host_id": alert.host_id,
        "user_name": alert.user_name,
        "detection_time": alert.detection_time.isoformat() if alert.detection_time else None,
        "raw_response": alert.raw_response,
    }


def _build_evidence_from_incident(db, inc: Incident) -> Dict[str, Any]:
    return {
        "incident_id": inc.vendor_incident_id,
        "incident_name": inc.incident_name,
        "description": inc.description,
        "severity": inc.severity,
        "status": inc.status,
        "host_name": inc.host_name,
        "user_name": inc.user_name,
        "detection_time": inc.detection_time.isoformat() if inc.detection_time else None,
        "raw_response": inc.raw_response,
    }


@router.post("/{incident_id}/analyze", response_model=AnalyzeResponse)
def analyze_incident(
    incident_id: str,
    req: AnalyzeRequest = AnalyzeRequest(),
    db=Depends(get_db),
    user=Depends(require_user),
):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        inc = db.query(Incident).filter(Incident.vendor_incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    service = AIService()
    if req.provider:
        service.provider = req.provider
    if req.model:
        service.model = req.model

    evidence = _build_evidence_from_incident(db, inc)
    language = "en"
    result, analysis_id, is_demo, cached = service.analyze(
        alert_id=None, incident_id=inc.vendor_incident_id, evidence=evidence,
        language=language, force_refresh=req.force_refresh, db=db,
    )
    return AnalyzeResponse(
        analysis_id=analysis_id,
        vendor_alert_id=None,
        vendor_incident_id=inc.vendor_incident_id,
        model_name=service.model,
        prompt_version=service.prompt_version,
        analysis_timestamp=datetime.utcnow(),
        result=result,
        is_demo=is_demo,
        cached=cached,
    )


@router.post("/{incident_id}/chat")
def chat_incident(
    incident_id: str,
    body: Dict[str, Any],
    db=Depends(get_db),
    user=Depends(require_user),
):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        inc = db.query(Incident).filter(Incident.vendor_incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    message = body.get("message", "")
    service = AIService()
    evidence = _build_evidence_from_incident(db, inc)
    # Analyze-style prompt scoped to answering the analyst's question using evidence only.
    result, _analysis_id, is_demo, _cached = service.analyze(
        alert_id=None,
        incident_id=inc.vendor_incident_id,
        evidence={**evidence, "analyst_question": message},
        language="en",
        force_refresh=True,
        db=db,
    )
    return {"response": result.summary, "is_demo": is_demo, "evidence_based": True}


alert_router = APIRouter(prefix="/alerts", tags=["analysis"])


@alert_router.post("/{alert_id}/analyze", response_model=AnalyzeResponse)
def analyze_alert(
    alert_id: str,
    req: AnalyzeRequest = AnalyzeRequest(),
    db=Depends(get_db),
    user=Depends(require_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        alert = db.query(Alert).filter(Alert.vendor_alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    service = AIService()
    if req.provider:
        service.provider = req.provider
    if req.model:
        service.model = req.model

    evidence = _build_evidence_from_alert(db, alert)
    result, analysis_id, is_demo, cached = service.analyze(
        alert_id=alert.vendor_alert_id, incident_id=None, evidence=evidence,
        language="en", force_refresh=req.force_refresh, db=db,
    )
    return AnalyzeResponse(
        analysis_id=analysis_id,
        vendor_alert_id=alert.vendor_alert_id,
        vendor_incident_id=None,
        model_name=service.model,
        prompt_version=service.prompt_version,
        analysis_timestamp=datetime.utcnow(),
        result=result,
        is_demo=is_demo,
        cached=cached,
    )