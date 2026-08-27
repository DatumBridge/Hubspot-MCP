"""HubSpot CRM HTTP client. Credentials come from vault inject (credentials_json)."""

from __future__ import annotations

import json
from typing import Any, Optional

import requests

HUBSPOT_BASE = "https://api.hubapi.com"
_REQUEST_TIMEOUT = 30


class HubSpotError(Exception):
    def __init__(
        self,
        message: str,
        error_code: str = "HUBSPOT_ERROR",
        retryable: bool = False,
        original_provider_error: Any = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.retryable = retryable
        self.original_provider_error = original_provider_error

    def to_dict(self) -> dict:
        return {
            "error_code": self.error_code,
            "error_message": str(self),
            "retryable": self.retryable,
            "original_provider_error": self.original_provider_error,
        }


def _token_from_creds(credentials_json: Optional[str], credentials_path: Optional[str]) -> str:
    data: dict[str, Any] = {}
    try:
        if credentials_json:
            data = json.loads(credentials_json)
        elif credentials_path:
            with open(credentials_path, encoding="utf-8") as fh:
                data = json.load(fh)
        else:
            raise HubSpotError(
                "Credentials required: provide credentials_path or credentials_json",
                error_code="CREDENTIALS_REQUIRED",
            )
    except HubSpotError:
        raise
    except json.JSONDecodeError as e:
        raise HubSpotError(
            "Invalid credentials JSON",
            error_code="INVALID_CREDENTIALS",
            original_provider_error=str(e),
        ) from e
    except OSError as e:
        raise HubSpotError(
            "Unable to read credentials file",
            error_code="INVALID_CREDENTIALS",
            original_provider_error=str(e),
        ) from e
    if not isinstance(data, dict):
        raise HubSpotError(
            "Credentials JSON must be an object",
            error_code="INVALID_CREDENTIALS",
        )
    token = (data.get("access_token") or data.get("token") or "").strip()
    if not token:
        raise HubSpotError(
            "Credentials required: provide credentials_path or credentials_json",
            error_code="CREDENTIALS_REQUIRED",
        )
    return token


class HubSpotService:
    """CRM client. Token refresh + vault write-back happen in Integrations inject (HubSpot RT rotation)."""

    def __init__(
        self,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ):
        self._token = _token_from_creds(credentials_json, credentials_path)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token}"
        resp = requests.request(
            method, HUBSPOT_BASE + path, headers=headers, timeout=_REQUEST_TIMEOUT, **kwargs
        )
        if resp.status_code in (401, 403):
            raise HubSpotError(
                "HubSpot auth failed; reconnect HubSpot in Account → Integrations "
                f"({resp.status_code}): {(resp.text or '')[:200]}",
                error_code="AUTH_ERROR",
                retryable=False,
                original_provider_error=(resp.text or "")[:300],
            )
        if resp.status_code >= 400:
            raise HubSpotError(
                f"HubSpot API {resp.status_code}: {(resp.text or '')[:300]}",
                error_code="HUBSPOT_API_ERROR",
                retryable=resp.status_code >= 500,
                original_provider_error=(resp.text or "")[:300],
            )
        if not resp.content:
            return {}
        return resp.json()

    def search(self, object_type: str, query: str, limit: int = 20) -> list[dict]:
        body = {
            "query": query or "",
            "limit": max(1, min(limit, 100)),
            "properties": [
                "email",
                "firstname",
                "lastname",
                "name",
                "domain",
                "dealname",
                "amount",
                "pipeline",
            ],
        }
        data = self._request("POST", f"/crm/v3/objects/{object_type}/search", json=body)
        return data.get("results") or []

    def get(self, object_type: str, object_id: str) -> dict:
        return self._request("GET", f"/crm/v3/objects/{object_type}/{object_id}")

    def create(self, object_type: str, properties: dict) -> dict:
        return self._request(
            "POST", f"/crm/v3/objects/{object_type}", json={"properties": properties}
        )

    def update(self, object_type: str, object_id: str, properties: dict) -> dict:
        return self._request(
            "PATCH",
            f"/crm/v3/objects/{object_type}/{object_id}",
            json={"properties": properties},
        )
