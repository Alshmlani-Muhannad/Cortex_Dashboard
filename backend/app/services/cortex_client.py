"""Cortex XDR public API client."""
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("app.cortex")


class CortexXDRClientError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class CortexXDRAuthenticationError(CortexXDRClientError):
    pass


class CortexXDRRateLimitError(CortexXDRClientError):
    def __init__(self, message: str, retry_after: Optional[float] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class CortexXDRClient:
    def __init__(
        self,
        tenant_fqdn: Optional[str] = None,
        api_key_id: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        base_backoff: Optional[float] = None,
    ):
        self.tenant_fqdn = tenant_fqdn or settings.CORTEX_TENANT_FQDN
        self.api_key_id = api_key_id or settings.CORTEX_API_KEY_ID
        self.api_key = api_key or settings.CORTEX_API_KEY
        self.timeout = timeout or settings.CORTEX_REQUEST_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else settings.CORTEX_MAX_RETRIES
        self.base_backoff = base_backoff or settings.CORTEX_BASE_BACKOFF_SECONDS
        self.api_version = settings.CORTEX_API_VERSION
        self._client = httpx.Client(
            timeout=httpx.Timeout(self.timeout),
            headers={"Content-Type": "application/json"},
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.tenant_fqdn and self.api_key_id and self.api_key)

    def _base_url(self) -> str:
        if not self.tenant_fqdn:
            raise CortexXDRClientError("Cortex XDR tenant FQDN is not configured")
        return f"{self.tenant_fqdn}/public_api/{self.api_version}"

    def _auth_headers(self) -> Dict[str, str]:
        return {
            "x-xdr-auth-key-id": self.api_key_id or "",
            "x-xdr-auth-key": self.api_key or "",
        }

    def _request(
        self,
        method: str,
        path: str,
        request_data: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured:
            raise CortexXDRAuthenticationError("Cortex XDR credentials are not configured")

        url = f"{self._base_url()}{path}"
        body: Dict[str, Any] = {}
        if request_data is not None:
            body["request_data"] = request_data

        headers = dict(self._auth_headers())
        if extra_headers:
            headers.update(extra_headers)

        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self._client.request(method, url, json=body, headers=headers)
            except httpx.TimeoutException as exc:
                last_exc = exc
                wait = self._backoff(attempt)
                logger.warning(
                    "Cortex request timeout (attempt %d/%d), retrying in %.1fs",
                    attempt,
                    self.max_retries,
                    wait,
                )
                time.sleep(wait)
                continue
            except httpx.RequestError as exc:
                last_exc = exc
                wait = self._backoff(attempt)
                logger.warning(
                    "Cortex request error (attempt %d/%d): %s", attempt, self.max_retries, exc
                )
                time.sleep(wait)
                continue

            if resp.status_code == 200:
                try:
                    data = resp.json()
                except ValueError as exc:
                    raise CortexXDRClientError(f"Invalid JSON response: {exc}") from exc
                return self._unwrap_response(data)

            if resp.status_code == 429:
                retry_after = self._parse_retry_after(resp)
                raise CortexXDRRateLimitError(
                    "Cortex XDR API rate limit exceeded",
                    status_code=resp.status_code,
                    retry_after=retry_after,
                )

            if resp.status_code in (401, 403):
                try:
                    err = resp.json().get("error", {})
                except ValueError:
                    err = {}
                raise CortexXDRAuthenticationError(
                    err.get("message", f"Authentication failed (HTTP {resp.status_code})"),
                    status_code=resp.status_code,
                    code=err.get("code"),
                )

            if 400 <= resp.status_code < 500:
                try:
                    err = resp.json().get("error", {})
                except ValueError:
                    err = {}
                raise CortexXDRClientError(
                    err.get("message", f"Client error (HTTP {resp.status_code})"),
                    status_code=resp.status_code,
                    code=err.get("code"),
                )

            last_exc = CortexXDRClientError(
                f"Server error (HTTP {resp.status_code})",
                status_code=resp.status_code,
            )
            wait = self._backoff(attempt)
            logger.warning(
                "Cortex server error (attempt %d/%d), retrying in %.1fs",
                attempt,
                self.max_retries,
                wait,
            )
            time.sleep(wait)

        raise CortexXDRClientError(
            f"Request failed after {self.max_retries} attempts: {last_exc}",
        )

    @staticmethod
    def _unwrap_response(data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise CortexXDRClientError("Unexpected response format: expected a JSON object")
        if "error" in data:
            err = data.get("error") or {}
            raise CortexXDRClientError(
                err.get("message", "Cortex XDR API error"),
                code=err.get("code"),
            )
        if "reply" in data:
            return data.get("reply") or {}
        return data

    @staticmethod
    def _backoff(attempt: int) -> float:
        return min(30.0, (2 ** (attempt - 1)) * 1.0 + 0.5)

    @staticmethod
    def _parse_retry_after(resp: httpx.Response) -> Optional[float]:
        try:
            return float(resp.headers.get("retry-after", "0")) or None
        except (TypeError, ValueError):
            return None

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ------------------------------------------------------------------ #
    # Endpoints
    # ------------------------------------------------------------------ #

    def get_alerts(
        self,
        search_from: int = 0,
        search_to: int = 100,
        sort_field: str = "creation_time",
        sort_order: str = "desc",
        alert_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """POST /public_api/v1/alerts/get_alerts.

        Returns {"total_count": int, "alerts": [ {...}, ... ]}.
        """
        request_data: Dict[str, Any] = {
            "search_from": search_from,
            "search_to": search_to,
            "sort_field": sort_field,
            "sort_order": sort_order,
        }
        if alert_filter:
            request_data["alert_filter"] = alert_filter
        return self._request("POST", "/alerts/get_alerts", request_data=request_data)

    def get_incidents(
        self,
        search_from: int = 0,
        search_to: int = 100,
        sort_field: str = "creation_time",
        sort_order: str = "desc",
        incident_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """POST /public_api/v1/incidents/get_incidents.

        Returns {"total_count": int, "incidents": [ {...}, ... ]}.
        """
        request_data: Dict[str, Any] = {
            "search_from": search_from,
            "search_to": search_to,
            "sort_field": sort_field,
            "sort_order": sort_order,
        }
        if incident_filter:
            request_data["incident_filter"] = incident_filter
        return self._request("POST", "/incidents/get_incidents", request_data=request_data)

    def get_incident_extra_data(
        self,
        incident_ids: List[str],
    ) -> Dict[str, Any]:
        """POST /public_api/v1/incidents/get_incident_extra_data.

        Returns extra evidence for the given incident IDs.
        """
        request_data: Dict[str, Any] = {"incident_ids": incident_ids}
        return self._request("POST", "/incidents/get_incident_extra_data", request_data=request_data)

    def get_alerts_multi_events(
        self,
        alert_ids: List[str],
    ) -> Dict[str, Any]:
        """POST /public_api/v2/alerts/get_alerts_multi_events.

        Returns process/network/file events for the given alert IDs.
        Availability depends on the tenant license.
        """
        request_data: Dict[str, Any] = {"alert_ids": alert_ids}
        return self._request("POST", "/alerts/get_alerts_multi_events", request_data=request_data)