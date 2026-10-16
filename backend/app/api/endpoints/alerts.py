"""Alerts explorer endpoints."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, asc, or_

from app.api.deps import require_user, get_db
from app.models.alert import Alert
from app.models.event import Event
from app.models.incident_alert import IncidentAlert
from app.models.ai_analysis import AIAnalysis
from app.schemas.alert import AlertOut, AlertFilterParams
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _apply_filters(q, f: AlertFilterParams):
    if f.severity:
        q = q.filter(Alert.severity == f.severity)
    if f.status:
        q = q.filter(Alert.status == f.status)
    if f.detection_category:
        q = q.filter(Alert.detection_category == f.detection_category)
    if f.endpoint:
        q = q.filter(Alert.host_name.ilike(f"%{f.endpoint}%"))
    if f.incident_id:
        q = q.filter(Alert.incident_id == f.incident_id)
    if f.start_time:
        q = q.filter(Alert.detection_time >= f.start_time)
    if f.end_time:
        q = q.filter(Alert.detection_time <= f.end_time)
    if f.time_range:
        now = datetime.now(timezone.utc)
        if f.time_range == "24h":
            q = q.filter(Alert.detection_time >= now - timedelta(hours=24))
        elif f.time_range == "7d":
            q = q.filter(Alert.detection_time >= now - timedelta(days=7))
        elif f.time_range == "30d":
            q = q.filter(Alert.detection_time >= now - timedelta(days=30))
    if f.search:
        q = q.filter(
            or_(
                Alert.alert_name.ilike(f"%{f.search}%"),
                Alert.description.ilike(f"%{f.search}%"),
                Alert.host_name.ilike(f"%{f.search}%"),
                Alert.vendor_alert_id.ilike(f"%{f.search}%"),
            )
        )
    return q


@router.get("", response_model=PaginatedResponse)
def list_alerts(
    severity: Optional[str] = Query(None),
    time_range: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    endpoint: Optional[str] = Query(None),
    detection_category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db=Depends(get_db),
    user=Depends(require_user),
):
    f = AlertFilterParams(
        severity=severity,
        time_range=time_range,
        start_time=start_time,
        end_time=end_time,
        endpoint=endpoint,
        detection_category=detection_category,
        status=status,
        incident_id=incident_id,
        search=search,
        sort_field=sort_field,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    q = _apply_filters(db.query(Alert), f)
    total = q.count()
    order_col = getattr(Alert, f.sort_field, Alert.detection_time)
    q = q.order_by(desc(order_col) if f.sort_order == "desc" else asc(order_col))
    q = q.offset((f.page - 1) * f.page_size).limit(f.page_size)
    items = q.all()
    return PaginatedResponse(
        items=[AlertOut.model_validate(i) for i in items],
        total=total,
        page=f.page,
        page_size=f.page_size,
        total_pages=(total + f.page_size - 1) // f.page_size,
    )


@router.get("/{alert_id}", response_model=Dict[str, Any])
def get_alert(
    alert_id: str,
    db=Depends(get_db),
    user=Depends(require_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        alert = db.query(Alert).filter(Alert.vendor_alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    events = (
        db.query(Event).filter(Event.vendor_alert_id == alert.vendor_alert_id)
        .order_by(Event.event_time.desc().nullslast())
        .limit(100)
        .all()
    )
    links = (
        db.query(IncidentAlert).filter(IncidentAlert.vendor_alert_id == alert.vendor_alert_id)
        .all()
    )
    latest_analysis = (
        db.query(AIAnalysis).filter(AIAnalysis.vendor_alert_id == alert.vendor_alert_id)
        .order_by(AIAnalysis.analysis_timestamp.desc())
        .first()
    )

    return {
        "id": str(alert.id),
        "vendor_alert_id": alert.vendor_alert_id,
        "tenant_id": alert.tenant_id,
        "alert_name": alert.alert_name,
        "description": alert.description,
        "severity": alert.severity,
        "detection_category": alert.detection_category,
        "alert_type": alert.alert_type,
        "status": alert.status,
        "creation_time": alert.creation_time.isoformat() if alert.creation_time else None,
        "detection_time": alert.detection_time.isoformat() if alert.detection_time else None,
        "analysis_time": alert.analysis_time.isoformat() if alert.analysis_time else None,
        "host_name": alert.host_name,
        "host_id": alert.host_id,
        "user_name": alert.user_name,
        "incident_id": alert.incident_id,
        "analysis_vendor": alert.analysis_vendor,
        "raw_response": alert.raw_response,
        "linked_incident_ids": [l.vendor_incident_id for l in links],
        "events": [
            {
                "id": str(e.id),
                "vendor_event_id": e.vendor_event_id,
                "event_type": e.event_type,
                "event_time": e.event_time.isoformat() if e.event_time else None,
                "description": e.description,
                "raw_response": e.raw_response,
            }
            for e in events
        ],
        "ai_analysis": (
            {
                "id": str(latest_analysis.id),
                "model_name": latest_analysis.model_name,
                "prompt_version": latest_analysis.prompt_version,
                "analysis_timestamp": latest_analysis.analysis_timestamp.isoformat() if latest_analysis.analysis_timestamp else None,
                "result": latest_analysis.result,
                "is_demo": latest_analysis.is_demo,
            }
            if latest_analysis else None
        ),
    }