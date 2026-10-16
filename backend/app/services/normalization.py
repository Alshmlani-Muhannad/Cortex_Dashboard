"""Normalization of Cortex XDR responses into internal models.

Preserves the full raw_response so no evidence is discarded. All vendor
fields are treated as optional because availability varies by tenant.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dateutil import parser as dateparser


def parse_dt(value: Any) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = dateparser.parse(str(value))
    except (ValueError, TypeError):
        return None
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _first(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def normalize_alert(raw: Dict[str, Any], tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """Map a Cortex alert object to internal alert fields.

    Returns a dict with normalized fields plus ``raw_response``.
    """
    vendor_id = str(
        _first(raw, "alert_id", "id", default="") or ""
    )
    return {
        "vendor_alert_id": vendor_id,
        "tenant_id": tenant_id,
        "alert_name": _first(raw, "alert_name", "name", default=None),
        "description": _first(raw, "description", default=None),
        "severity": _first(raw, "severity", default=None),
        "detection_category": _first(
            raw, "detection_category", "category", "detection_categories", default=None
        ),
        "alert_type": _first(raw, "alert_type", "type", default=None),
        "status": _first(raw, "status", default=None),
        "creation_time": parse_dt(_first(raw, "creation_time", "created_time", default=None)),
        "detection_time": parse_dt(
            _first(raw, "detection_time", "detection_timestamp", default=None)
        ),
        "analysis_time": parse_dt(_first(raw, "analysis_time", default=None)),
        "host_name": _first(raw, "host_name", "endpoint_name", "computer_name", default=None),
        "host_id": _first(raw, "host_id", "endpoint_id", default=None),
        "user_name": _first(raw, "user_name", "username", "user", default=None),
        "incident_id": _first(raw, "incident_id", default=None),
        "analysis_vendor": _first(raw, "analysis_vendor", default=None),
        "raw_response": raw,
    }


def normalize_incident(raw: Dict[str, Any], tenant_id: Optional[str] = None) -> Dict[str, Any]:
    vendor_id = str(_first(raw, "incident_id", "id", default="") or "")
    return {
        "vendor_incident_id": vendor_id,
        "tenant_id": tenant_id,
        "incident_name": _first(raw, "incident_name", "name", default=None),
        "description": _first(raw, "description", default=None),
        "severity": _first(raw, "severity", default=None),
        "status": _first(raw, "status", default=None),
        "creation_time": parse_dt(_first(raw, "creation_time", "created_time", default=None)),
        "detection_time": parse_dt(
            _first(raw, "detection_time", "detection_timestamp", default=None)
        ),
        "last_update_time": parse_dt(_first(raw, "last_update_time", "updated_time", default=None)),
        "host_name": _first(raw, "host_name", "endpoint_name", default=None),
        "user_name": _first(raw, "user_name", "username", default=None),
        "raw_response": raw,
    }


def extract_incident_alert_links(raw_extra: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract incident->alert vendor ID links from extra data when present."""
    links: List[Dict[str, str]] = []
    if not isinstance(raw_extra, dict):
        return links
    incidents = raw_extra.get("incidents") or []
    for inc in incidents:
        inc_id = str(inc.get("incident_id") or "")
        alerts = inc.get("alerts") or []
        for a in alerts:
            aid = str(a.get("alert_id") or a.get("id") or "")
            if inc_id and aid:
                links.append({"vendor_incident_id": inc_id, "vendor_alert_id": aid})
    return links


def extract_events(raw_extra: Dict[str, Any], vendor_alert_id: str) -> List[Dict[str, Any]]:
    """Extract event/evidence records from multi-events or extra data."""
    events: List[Dict[str, Any]] = []
    if not isinstance(raw_extra, dict):
        return events
    # Multi-events responses often nest under "alerts" -> events lists.
    for container in raw_extra.values():
        if isinstance(container, list):
            for item in container:
                if isinstance(item, dict):
                    ev = dict(item)
                    ev["vendor_alert_id"] = vendor_alert_id
                    events.append(ev)
    return events