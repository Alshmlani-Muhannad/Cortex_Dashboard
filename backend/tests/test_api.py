"""Tests for FastAPI routes (no real Cortex credentials required)."""
from fastapi.testclient import TestClient


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "degraded")
    assert "database" in body


def test_dashboard_summary(client, auth_headers):
    r = client.get("/api/dashboard/summary", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    for key in ["total_alerts", "open_incidents", "critical_high_alerts", "severity_distribution", "sync_status", "demo_mode"]:
        assert key in body


def test_sync_status(client, auth_headers):
    r = client.get("/api/sync/status", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "configured" in body
    assert "connection_status" in body


def test_settings_ai(client, auth_headers):
    r = client.get("/api/settings/ai", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "provider" in body
    assert "model" in body


def test_alerts_list_pagination(client, auth_headers):
    r = client.get("/api/alerts?page=1&page_size=10", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body and "page" in body


def test_incidents_list(client, auth_headers):
    r = client.get("/api/incidents", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body


def test_auth_required(client):
    r = client.get("/api/dashboard/summary")
    assert r.status_code in (401, 403)


def test_no_secrets_in_responses(client, auth_headers):
    """Ensure API keys never leak in responses."""
    for path in ["/api/health", "/api/settings/ai", "/api/sync/status", "/api/dashboard/summary"]:
        r = client.get(path, headers=auth_headers)
        text = r.text.lower()
        assert "secret" not in text
        assert "api_key" not in text
        assert "x-xdr-auth-key" not in text


def test_sync_now_without_credentials(client, auth_headers):
    r = client.post("/api/sync", headers=auth_headers)
    # demo mode true in conftest but no credentials -> should still attempt demo or error gracefully
    assert r.status_code in (200, 400)