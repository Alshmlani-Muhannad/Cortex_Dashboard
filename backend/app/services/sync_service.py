"""Synchronization service: incremental fetch, dedupe, persist."""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import alert as alert_model
from app.models import incident as incident_model
from app.models.sync_checkpoint import SyncCheckpoint
from app.models.sync_job import SyncJob
from app.services.cortex_client import (
    CortexXDRClient,
    CortexXDRClientError,
    CortexXDRAuthenticationError,
    CortexXDRRateLimitError,
)
from app.services.normalization import (
    extract_events,
    extract_incident_alert_links,
    normalize_alert,
    normalize_incident,
)

logger = logging.getLogger("app.sync")


class SyncResult:
    def __init__(self) -> None:
        self.alerts_fetched = 0
        self.alerts_inserted = 0
        self.alerts_updated = 0
        self.incidents_fetched = 0
        self.incidents_inserted = 0
        self.incidents_updated = 0
        self.events_inserted = 0
        self.errors: List[str] = []
        self.last_sync_time: Optional[datetime] = None


def _upsert_alert(db: Session, data: Dict[str, Any]) -> Tuple[str, bool]:
    from app.models.alert import Alert
    vendor_id = data["vendor_alert_id"]
    existing = db.query(Alert).filter(Alert.vendor_alert_id == vendor_id).first()
    now = datetime.now(timezone.utc)
    if existing:
        for field in [
            "alert_name", "description", "severity", "detection_category",
            "alert_type", "status", "creation_time", "detection_time",
            "analysis_time", "host_name", "host_id", "user_name",
            "incident_id", "analysis_vendor", "raw_response", "tenant_id",
        ]:
            if field in data:
                setattr(existing, field, data[field])
        existing.updated_at = now
        db.add(existing)
        return vendor_id, False
    obj = Alert(**{k: v for k, v in data.items() if k in Alert.__mapper__.columns})
    db.add(obj)
    return vendor_id, True


def _upsert_incident(db: Session, data: Dict[str, Any]) -> Tuple[str, bool]:
    from app.models.incident import Incident
    vendor_id = data["vendor_incident_id"]
    existing = db.query(Incident).filter(Incident.vendor_incident_id == vendor_id).first()
    now = datetime.now(timezone.utc)
    if existing:
        for field in [
            "incident_name", "description", "severity", "status",
            "creation_time", "detection_time", "last_update_time",
            "host_name", "user_name", "raw_response", "tenant_id",
        ]:
            if field in data:
                setattr(existing, field, data[field])
        existing.updated_at = now
        db.add(existing)
        return vendor_id, False
    obj = Incident(**{k: v for k, v in data.items() if k in Incident.__mapper__.columns})
    db.add(obj)
    return vendor_id, True


def _get_checkpoint(db: Session, tenant_id: Optional[str], entity_type: str) -> Optional[SyncCheckpoint]:
    return (
        db.query(SyncCheckpoint)
        .filter(SyncCheckpoint.tenant_id == tenant_id)
        .filter(SyncCheckpoint.entity_type == entity_type)
        .first()
    )


def _set_checkpoint(
    db: Session,
    tenant_id: Optional[str],
    entity_type: str,
    last_sync_time: datetime,
    last_vendor_id: Optional[str],
    records_seen: int,
) -> None:
    cp = _get_checkpoint(db, tenant_id, entity_type)
    if cp:
        cp.last_sync_time = last_sync_time
        cp.last_vendor_id = last_vendor_id
        cp.records_seen = records_seen
        cp.updated_at = last_sync_time
    else:
        cp = SyncCheckpoint(
            tenant_id=tenant_id,
            entity_type=entity_type,
            last_sync_time=last_sync_time,
            last_vendor_id=last_vendor_id,
            records_seen=records_seen,
        )
    db.add(cp)


def sync_alerts(client: CortexXDRClient, db: Session, tenant_id: Optional[str]) -> SyncResult:
    result = SyncResult()
    page_size = settings.CORTEX_SYNC_PAGE_SIZE
    offset = 0
    cp = _get_checkpoint(db, tenant_id, "alerts")
    newest = cp.last_vendor_id if cp else None

    while True:
        try:
            data = client.get_alerts(search_from=offset, search_to=offset + page_size - 1)
        except CortexXDRRateLimitError as exc:
            result.errors.append(f"Rate limited syncing alerts: {exc.message}")
            break
        except CortexXDRClientError as exc:
            result.errors.append(f"Error syncing alerts: {exc.message}")
            break

        alerts = data.get("alerts") or []
        total = int(data.get("total_count") or 0)
        result.alerts_fetched += len(alerts)

        for raw in alerts:
            norm = normalize_alert(raw, tenant_id=tenant_id)
            _, inserted = _upsert_alert(db, norm)
            if inserted:
                result.alerts_inserted += 1
            else:
                result.alerts_updated += 1
            aid = norm["vendor_alert_id"]
            if newest is None or aid > newest:
                newest = aid

        db.commit()

        offset += len(alerts)
        if offset >= total or not alerts:
            break

    _set_checkpoint(
        db, tenant_id, "alerts", datetime.now(timezone.utc), newest,
        result.alerts_fetched,
    )
    db.commit()
    result.last_sync_time = datetime.now(timezone.utc)
    return result


def sync_incidents(client: CortexXDRClient, db: Session, tenant_id: Optional[str]) -> SyncResult:
    result = SyncResult()
    page_size = settings.CORTEX_SYNC_PAGE_SIZE
    offset = 0
    cp = _get_checkpoint(db, tenant_id, "incidents")
    newest = cp.last_vendor_id if cp else None

    while True:
        try:
            data = client.get_incidents(search_from=offset, search_to=offset + page_size - 1)
        except CortexXDRRateLimitError as exc:
            result.errors.append(f"Rate limited syncing incidents: {exc.message}")
            break
        except CortexXDRClientError as exc:
            result.errors.append(f"Error syncing incidents: {exc.message}")
            break

        incidents = data.get("incidents") or []
        total = int(data.get("total_count") or 0)
        result.incidents_fetched += len(incidents)

        for raw in incidents:
            norm = normalize_incident(raw, tenant_id=tenant_id)
            _, inserted = _upsert_incident(db, norm)
            if inserted:
                result.incidents_inserted += 1
            else:
                result.incidents_updated += 1
            iid = norm["vendor_incident_id"]
            if newest is None or iid > newest:
                newest = iid

        db.commit()

        offset += len(incidents)
        if offset >= total or not incidents:
            break

    # Best-effort: fetch extra data and link incidents to alerts.
    try:
        from app.models.incident_alert import IncidentAlert
        all_incidents = (
            db.query(incident_model.Incident)
            .filter(incident_model.Incident.tenant_id == tenant_id)
            .all()
        )
        incident_ids = [inc.vendor_incident_id for inc in all_incidents[:50]]
        if incident_ids:
            extra = client.get_incident_extra_data(incident_ids)
            links = extract_incident_alert_links(extra)
            for link in links:
                exists = (
                    db.query(IncidentAlert)
                    .filter(IncidentAlert.vendor_incident_id == link["vendor_incident_id"])
                    .filter(IncidentAlert.vendor_alert_id == link["vendor_alert_id"])
                    .first()
                )
                if not exists:
                    db.add(IncidentAlert(**link))
            db.commit()
    except CortexXDRClientError as exc:
        logger.warning("Could not fetch incident extra data: %s", exc.message)
        result.errors.append(f"Incident extra data unavailable: {exc.message}")

    _set_checkpoint(
        db, tenant_id, "incidents", datetime.now(timezone.utc), newest,
        result.incidents_fetched,
    )
    db.commit()
    result.last_sync_time = datetime.now(timezone.utc)
    return result
    result.last_sync_time = datetime.now(timezone.utc)
    return result


def run_full_sync(client: CortexXDRClient, db: Session, job_type: str = "manual") -> SyncJob:
    """Run a full sync (alerts + incidents) and record a SyncJob."""
    job = SyncJob(job_type=job_type, status="running", started_at=datetime.now(timezone.utc))
    db.add(job)
    db.commit()
    db.refresh(job)

    result = SyncResult()
    try:
        if not client.is_configured:
            raise CortexXDRClientError("Cortex XDR credentials are not configured")

        a = sync_alerts(client, db, tenant_id=None)
        i = sync_incidents(client, db, tenant_id=None)
        result.alerts_fetched += a.alerts_fetched
        result.alerts_inserted += a.alerts_inserted
        result.alerts_updated += a.alerts_updated
        result.incidents_fetched += i.incidents_fetched
        result.incidents_inserted += i.incidents_inserted
        result.incidents_updated += i.incidents_updated
        result.errors.extend(a.errors)
        result.errors.extend(i.errors)

        job.status = "completed" if not result.errors else "completed_with_warnings"
        job.records_fetched = result.alerts_fetched + result.incidents_fetched
        job.records_inserted = result.alerts_inserted + result.incidents_inserted
        job.error_message = "; ".join(result.errors) if result.errors else None
    except Exception as exc:  # noqa: BLE001
        logger.exception("Sync job failed")
        job.status = "failed"
        job.error_message = str(exc)
    finally:
        job.completed_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()
        db.refresh(job)
    return job