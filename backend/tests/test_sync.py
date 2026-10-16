"""Tests for sync: pagination, dedupe, checkpoint, error handling."""
import responses
from sqlalchemy import func

from app.services.cortex_client import CortexXDRClient
from app.services.sync_service import run_full_sync, sync_alerts, sync_incidents


def _alerts_page(page, total, ids):
    return {
        "reply": {
            "total_count": total,
            "alerts": [{"alert_id": i, "alert_name": f"Alert {i}", "severity": "high", "host_name": "H1"} for i in ids],
        }
    }


def _incidents_page(page, total, ids):
    return {
        "reply": {
            "total_count": total,
            "incidents": [{"incident_id": i, "incident_name": f"Inc {i}", "status": "open", "severity": "critical"} for i in ids],
        }
    }


@responses.activate
def test_sync_pagination_and_dedupe(db):
    c = CortexXDRClient(tenant_fqdn="https://t.api.cortexdata.panw.io", api_key_id="k", api_key="s")
    # page 1: 2 alerts, page 2: 1 alert (total 3)
    responses.add(responses.POST, "https://t.api.cortexdata.panw.io/public_api/v1/alerts/get_alerts", json=_alerts_page(0, 3, ["a1", "a2"]), status=200)
    responses.add(responses.POST, "https://t.api.cortexdata.panw.io/public_api/v1/alerts/get_alerts", json=_alerts_page(100, 3, ["a3"]), status=200)
    responses.add(responses.POST, "https://t.api.cortexdata.panw.io/public_api/v1/incidents/get_incidents", json=_incidents_page(0, 0, []), status=200)

    job = run_full_sync(c, db, job_type="manual")
    assert job.status == "completed"
    assert job.records_fetched == 3

    from app.models.alert import Alert
    assert db.query(Alert).count() == 3

    # Run again -> dedupe (no new inserts)
    job2 = run_full_sync(c, db, job_type="automatic")
    assert db.query(Alert).count() == 3
    assert job2.records_inserted == 0


@responses.activate
def test_missing_credentials(db):
    c = CortexXDRClient(tenant_fqdn=None, api_key_id=None, api_key=None)
    job = run_full_sync(c, db, job_type="manual")
    assert job.status == "failed"
    assert "configured" in job.error_message


@responses.activate
def test_timeout_retry_then_succeeds(db):
    import httpx
    responses.add(responses.POST, "https://t.api.cortexdata.panw.io/public_api/v1/alerts/get_alerts",
                  body=httpx.ConnectTimeout("timed out"))
    responses.add(responses.POST, "https://t.api.cortexdata.panw.io/public_api/v1/alerts/get_alerts",
                  json=_alerts_page(0, 1, ["a1"]), status=200)
    responses.add(responses.POST, "https://t.api.cortexdata.panw.io/public_api/v1/incidents/get_incidents", json=_incidents_page(0, 0, []), status=200)
    c = CortexXDRClient(tenant_fqdn="https://t.api.cortexdata.panw.io", api_key_id="k", api_key="s", max_retries=2, base_backoff=0.01)
    job = run_full_sync(c, db, job_type="manual")
    assert job.status == "completed"