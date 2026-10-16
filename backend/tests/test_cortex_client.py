"""Tests for the Cortex XDR client (mocked HTTP, no real credentials required)."""
import pytest
import responses

from app.services.cortex_client import (
    CortexXDRClient,
    CortexXDRAuthenticationError,
    CortexXDRRateLimitError,
    CortexXDRClientError,
)


def _client(**kw):
    return CortexXDRClient(
        tenant_fqdn="https://tenant.api.cortexdata.panw.io",
        api_key_id="key-id",
        api_key="secret-key",
        max_retries=2,
        base_backoff=0.1,
        **kw,
    )


@responses.activate
def test_get_alerts_pagination():
    responses.add(
        responses.POST,
        "https://tenant.api.cortexdata.panw.io/public_api/v1/alerts/get_alerts",
        json={"reply": {"total_count": 2, "alerts": [{"alert_id": "a1"}, {"alert_id": "a2"}]}},
        status=200,
    )
    c = _client()
    data = c.get_alerts(search_from=0, search_to=99)
    assert data["total_count"] == 2
    assert len(data["alerts"]) == 2
    # verify auth headers sent
    req = responses.calls[0].request
    assert req.headers["x-xdr-auth-key-id"] == "key-id"
    assert req.headers["x-xdr-auth-key"] == "secret-key"
    body = __import__("json").loads(req.body)
    assert "request_data" in body


@responses.activate
def test_auth_error_not_retried():
    responses.add(
        responses.POST,
        "https://tenant.api.cortexdata.panw.io/public_api/v1/alerts/get_alerts",
        json={"error": {"code": "INVALID_API_KEY", "message": "bad key"}},
        status=401,
    )
    c = _client()
    with pytest.raises(CortexXDRAuthenticationError):
        c.get_alerts()


@responses.activate
def test_rate_limit_error():
    responses.add(
        responses.POST,
        "https://tenant.api.cortexdata.panw.io/public_api/v1/alerts/get_alerts",
        json={"error": {"code": "RATE_LIMIT", "message": "too many"}},
        status=429,
        headers={"retry-after": "1"},
    )
    c = _client()
    with pytest.raises(CortexXDRRateLimitError) as exc:
        c.get_alerts()
    assert exc.value.retry_after == 1.0


@responses.activate
def test_server_error_retries_then_fails():
    responses.add(
        responses.POST,
        "https://tenant.api.cortexdata.panw.io/public_api/v1/alerts/get_alerts",
        json={"error": {"code": "INTERNAL", "message": "boom"}},
        status=500,
    )
    c = _client()
    with pytest.raises(CortexXDRClientError):
        c.get_alerts()
    assert len(responses.calls) == 2  # max_retries


@responses.activate
def test_unwrap_error_payload():
    responses.add(
        responses.POST,
        "https://tenant.api.cortexdata.panw.io/public_api/v1/alerts/get_alerts",
        json={"error": {"message": "plain error"}},
        status=200,
    )
    c = _client()
    with pytest.raises(CortexXDRClientError):
        c.get_alerts()


def test_not_configured():
    c = CortexXDRClient(tenant_fqdn=None, api_key_id=None, api_key=None)
    assert not c.is_configured
    with pytest.raises(CortexXDRAuthenticationError):
        c.get_alerts()