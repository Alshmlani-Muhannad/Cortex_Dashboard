"""Sync endpoints."""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import require_user, require_role, get_db
from app.core.config import settings
from app.models.sync_checkpoint import SyncCheckpoint
from app.models.sync_job import SyncJob
from app.services.cortex_client import CortexXDRClient
from app.services.sync_service import run_full_sync
from app.schemas.common import SyncStatusResponse

router = APIRouter(prefix="/sync", tags=["sync"])


def _get_client() -> CortexXDRClient:
    return CortexXDRClient()


def _run_sync_background():
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        client = _get_client()
        run_full_sync(client, db, job_type="automatic")
    finally:
        db.close()


@router.post("", response_model=Dict[str, Any])
def sync_now(
    background: BackgroundTasks,
    db=Depends(get_db),
    user=Depends(require_user),
):
    client = _get_client()
    if not client.is_configured and not settings.CORTEX_DEMO_MODE:
        raise HTTPException(status_code=400, detail="Cortex XDR is not configured")
    job = run_full_sync(client, db, job_type="manual")
    return {
        "job_id": str(job.id),
        "status": job.status,
        "records_fetched": job.records_fetched,
        "records_inserted": job.records_inserted,
        "error_message": job.error_message,
    }


@router.get("/status", response_model=SyncStatusResponse)
def sync_status(
    db=Depends(get_db),
    user=Depends(require_user),
):
    cp_alerts = db.query(SyncCheckpoint).filter(SyncCheckpoint.entity_type == "alerts").first()
    cp_incidents = db.query(SyncCheckpoint).filter(SyncCheckpoint.entity_type == "incidents").first()
    last_job = db.query(SyncJob).order_by(desc(SyncJob.started_at)).first()

    latest_sync = None
    last_entity = None
    for cp in (cp_alerts, cp_incidents):
        if cp and (latest_sync is None or cp.last_sync_time > latest_sync):
            latest_sync = cp.last_sync_time
            last_entity = cp.entity_type

    configured = bool(
        settings.CORTEX_TENANT_FQDN
        and settings.CORTEX_API_KEY_ID
        and settings.CORTEX_API_KEY
    )
    connection_status = "not_configured"
    if settings.CORTEX_DEMO_MODE:
        connection_status = "demo"
    elif configured:
        connection_status = "configured"

    return SyncStatusResponse(
        configured=configured,
        demo_mode=bool(settings.CORTEX_DEMO_MODE or settings.AI_DEMO_MODE),
        last_sync_time=latest_sync,
        last_sync_entity=last_entity,
        last_job_status=last_job.status if last_job else None,
        last_job_error=last_job.error_message if last_job else None,
        connection_status=connection_status,
    )