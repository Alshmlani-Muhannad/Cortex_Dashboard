"""Dashboard summary endpoint."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc

from app.api.deps import require_user, require_role, get_db
from app.core.config import settings
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.sync_checkpoint import SyncCheckpoint
from app.models.sync_job import SyncJob
from app.models.ai_analysis import AIAnalysis
from app.schemas.common import SyncStatusResponse

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary")
def dashboard_summary(
    db=Depends(get_db),
    user=Depends(require_user),
):
    total_alerts = db.query(Alert).count()
    open_incidents = db.query(Incident).filter(Incident.status != "closed").count()
    critical_high = (
        db.query(Alert).filter(Alert.severity.in_(["critical", "high"])).count()
    )
    severity_rows = (
        db.query(Alert.severity, func.count(Alert.id))
        .group_by(Alert.severity)
        .all()
    )
    severity_dist = {r[0] or "unknown": r[1] for r in severity_rows}
    status_rows = (
        db.query(Incident.status, func.count(Incident.id))
        .group_by(Incident.status)
        .all()
    )
    incident_status_dist = {r[0] or "unknown": r[1] for r in status_rows}

    # Alerts over time (last 30 days, daily buckets)
    since = datetime.now(timezone.utc) - timedelta(days=30)
    over_time = (
        db.query(func.date(Alert.detection_time), func.count(Alert.id))
        .filter(Alert.detection_time >= since)
        .group_by(func.date(Alert.detection_time))
        .order_by(func.date(Alert.detection_time))
        .all()
    )
    alerts_over_time = [{"date": str(r[0]), "count": r[1]} for r in over_time]

    # Most affected endpoints
    endpoints = (
        db.query(Alert.host_name, func.count(Alert.id))
        .filter(Alert.host_name.isnot(None))
        .group_by(Alert.host_name)
        .order_by(desc(func.count(Alert.id)))
        .limit(10)
        .all()
    )
    top_endpoints = [{"endpoint": r[0], "count": r[1]} for r in endpoints]

    # Most common detection categories
    categories = (
        db.query(Alert.detection_category, func.count(Alert.id))
        .filter(Alert.detection_category.isnot(None))
        .group_by(Alert.detection_category)
        .order_by(desc(func.count(Alert.id)))
        .limit(10)
        .all()
    )
    top_categories = [{"category": r[0], "count": r[1]} for r in categories]

    # Recent alerts
    recent_alerts = (
        db.query(Alert)
        .order_by(desc(Alert.detection_time))
        .limit(10)
        .all()
    )
    recent_incidents = (
        db.query(Incident)
        .order_by(desc(Incident.detection_time))
        .limit(10)
        .all()
    )

    # Sync status
    cp_alerts = db.query(SyncCheckpoint).filter(SyncCheckpoint.entity_type == "alerts").first()
    cp_incidents = db.query(SyncCheckpoint).filter(SyncCheckpoint.entity_type == "incidents").first()
    last_job = db.query(SyncJob).order_by(desc(SyncJob.started_at)).first()

    latest_sync = None
    for cp in (cp_alerts, cp_incidents):
        if cp and (latest_sync is None or cp.last_sync_time > latest_sync):
            latest_sync = cp.last_sync_time

    connection_status = "not_configured"
    s = settings
    if s.CORTEX_TENANT_FQDN and s.CORTEX_API_KEY_ID and s.CORTEX_API_KEY:
        connection_status = "configured"
    elif s.CORTEX_DEMO_MODE:
        connection_status = "demo"

    # AI executive summary (from latest analysis)
    latest_analysis = db.query(AIAnalysis).order_by(desc(AIAnalysis.analysis_timestamp)).first()
    ai_summary = None
    if latest_analysis:
        result = latest_analysis.result or {}
        ai_summary = {
            "summary": result.get("summary"),
            "confidence": result.get("confidence"),
            "is_demo": latest_analysis.is_demo,
            "model_name": latest_analysis.model_name,
            "analysis_timestamp": latest_analysis.analysis_timestamp.isoformat() if latest_analysis.analysis_timestamp else None,
        }

    return {
        "total_alerts": total_alerts,
        "open_incidents": open_incidents,
        "critical_high_alerts": critical_high,
        "severity_distribution": severity_dist,
        "incident_status_distribution": incident_status_dist,
        "alerts_over_time": alerts_over_time,
        "top_endpoints": top_endpoints,
        "top_detection_categories": top_categories,
        "recent_alerts": [
            {
                "id": str(a.id),
                "vendor_alert_id": a.vendor_alert_id,
                "alert_name": a.alert_name,
                "severity": a.severity,
                "host_name": a.host_name,
                "detection_time": a.detection_time.isoformat() if a.detection_time else None,
                "status": a.status,
                "incident_id": a.incident_id,
            }
            for a in recent_alerts
        ],
        "recent_incidents": [
            {
                "id": str(i.id),
                "vendor_incident_id": i.vendor_incident_id,
                "incident_name": i.incident_name,
                "severity": i.severity,
                "status": i.status,
                "host_name": i.host_name,
                "detection_time": i.detection_time.isoformat() if i.detection_time else None,
            }
            for i in recent_incidents
        ],
        "ai_executive_summary": ai_summary,
        "last_sync_time": latest_sync.isoformat() if latest_sync else None,
        "sync_status": connection_status,
        "demo_mode": bool(s.CORTEX_DEMO_MODE or s.AI_DEMO_MODE),
    }