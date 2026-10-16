"""Tests for normalization of Cortex responses."""
from app.services.normalization import normalize_alert, normalize_incident


def test_normalize_alert_keeps_raw():
    raw = {
        "alert_id": "ALERT-123",
        "alert_name": "Suspicious process",
        "severity": "high",
        "detection_category": "Malware",
        "host_name": "WS-01",
        "user_name": "jsmith",
        "incident_id": "INC-9",
        "extra_field": "preserved",
    }
    n = normalize_alert(raw, tenant_id="t1")
    assert n["vendor_alert_id"] == "ALERT-123"
    assert n["severity"] == "high"
    assert n["raw_response"]["extra_field"] == "preserved"
    assert n["raw_response"]["alert_id"] == "ALERT-123"


def test_normalize_alert_missing_vendor_id_defaults_empty():
    n = normalize_alert({"alert_name": "x"})
    assert n["vendor_alert_id"] == ""


def test_normalize_incident():
    raw = {"incident_id": "INC-9", "incident_name": "Malware campaign", "status": "open", "severity": "critical"}
    n = normalize_incident(raw)
    assert n["vendor_incident_id"] == "INC-9"
    assert n["status"] == "open"