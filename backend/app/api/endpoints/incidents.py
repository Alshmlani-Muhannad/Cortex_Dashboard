"""Incident endpoints."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, asc, or_

from app.api.deps import require_user, get_db
from app.models.incident import Incident
from app.models.incident_alert import IncidentAlert
from app.models.alert import Alert
from app.models.ai_analysis import AIAnalysis
from app.schemas.incident import IncidentOut
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=PaginatedResponse)
def list_incidents(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    endpoint: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query("detection_time"),
    sort_order: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db=Depends(get_db),
    user=Depends(require_user),
):
    q = db.query(Incident)
    if severity:
        q = q.filter(Incident.severity == severity)
    if status:
        q = q.filter(Incident.status == status)
    if endpoint:
        q = q.filter(Incident.host_name.ilike(f"%{endpoint}%"))
    if search:
        q = q.filter(
            or_(
                Incident.incident_name.ilike(f"%{search}%"),
                Incident.description.ilike(f"%{search}%"),
                Incident.vendor_incident_id.ilike(f"%{search}%"),
                Incident.host_name.ilike(f"%{search}%"),
            )
        )
    total = q.count()
    order_col = getattr(Incident, sort_field, Incident.detection_time)
    q = q.order_by(desc(order_col) if sort_order == "desc" else asc(order_col))
    q = q.offset((page - 1) * page_size).limit(page_size)
    items = q.all()
    out = []
    for inc in items:
        links = (
            db.query(IncidentAlert).filter(IncidentAlert.vendor_incident_id == inc.vendor_incident_id)
            .all()
        )
        out.append(
            {
                **IncidentOut.model_validate(inc).model_dump(),
                "alert_ids": [l.vendor_alert_id for l in links],
            }
        )
    return PaginatedResponse(
        items=out,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{incident_id}", response_model=Dict[str, Any])
def get_incident(
    incident_id: str,
    db=Depends(get_db),
    user=Depends(require_user),
):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        inc = db.query(Incident).filter(Incident.vendor_incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    links = (
        db.query(IncidentAlert).filter(IncidentAlert.vendor_incident_id == inc.vendor_incident_id)
        .all()
    )
    alert_ids = [l.vendor_alert_id for l in links]
    alerts = (
        db.query(Alert).filter(Alert.vendor_alert_id.in_(alert_ids)).all()
        if alert_ids else []
    )
    latest_analysis = (
        db.query(AIAnalysis).filter(AIAnalysis.vendor_incident_id == inc.vendor_incident_id)
        .order_by(AIAnalysis.analysis_timestamp.desc())
        .first()
    )

    return {
        "id": str(inc.id),
        "vendor_incident_id": inc.vendor_incident_id,
        "tenant_id": inc.tenant_id,
        "incident_name": inc.incident_name,
        "description": inc.description,
        "severity": inc.severity,
        "status": inc.status,
        "creation_time": inc.creation_time.isoformat() if inc.creation_time else None,
        "detection_time": inc.detection_time.isoformat() if inc.detection_time else None,
        "last_update_time": inc.last_update_time.isoformat() if inc.last_update_time else None,
        "host_name": inc.host_name,
        "user_name": inc.user_name,
        "raw_response": inc.raw_response,
        "alerts": [
            {
                "vendor_alert_id": a.vendor_alert_id,
                "alert_name": a.alert_name,
                "severity": a.severity,
                "detection_category": a.detection_category,
                "status": a.status,
                "host_name": a.host_name,
            }
            for a in alerts
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


@router.get("/{incident_id}/timeline", response_model=Dict[str, Any])
def get_incident_timeline(
    incident_id: str,
    db=Depends(get_db),
    user=Depends(require_user),
):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        inc = db.query(Incident).filter(Incident.vendor_incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    links = (
        db.query(IncidentAlert).filter(IncidentAlert.vendor_incident_id == inc.vendor_incident_id)
        .all()
    )
    alert_ids = [l.vendor_alert_id for l in links]

    from app.models.event import Event
    events = []
    if alert_ids:
        events = (
            db.query(Event).filter(Event.vendor_alert_id.in_(alert_ids))
            .order_by(Event.event_time.desc().nullslast())
            .limit(200)
            .all()
        )

    timeline = []
    for e in events:
        timeline.append(
            {
                "time": e.event_time.isoformat() if e.event_time else None,
                "event_type": e.event_type,
                "description": e.description,
                "vendor_alert_id": e.vendor_alert_id,
                "vendor_event_id": e.vendor_event_id,
            }
        )
    timeline.insert(0, {
        "time": inc.detection_time.isoformat() if inc.detection_time else inc.creation_time.isoformat() if inc.creation_time else None,
        "event_type": "incident_detected",
        "description": f"Incident {inc.vendor_incident_id} detected",
        "vendor_incident_id": inc.vendor_incident_id,
    })
    timeline.sort(key=lambda x: (x["time"] is None, x["time"] or ""), reverse=True)
    return {"incident_id": inc.vendor_incident_id, "timeline": timeline}
    q = q.offset((page - 1) * page_size).limit(page_size)
    items = q.all()
    out = []
    for inc in items:
        links = (
            db.query(IncidentAlert).filter(IncidentAlert.vendor_incident_id == inc.vendor_incident_id)
            .all()
        )
        out.append(
            {
                **IncidentOut.model_validate(inc).model_dump(),
                "alert_ids": [l.vendor_alert_id for l in links],
            }
        )
    return PaginatedResponse(
        items=out,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )