"""HubSpot MCP Server — thin CRM surface for contacts, companies, and deals."""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastmcp import FastMCP
from pydantic import Field
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from app.services.hubspot_service import HubSpotError, HubSpotService

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="hubspot",
    instructions="HubSpot CRM tools. Credentials are injected as credentials_json from Studio Connect. Writes require confirm=true.",
)

_CREDS_JSON = Field(default=None, description="OAuth token JSON from Studio vault inject")
_CREDS_PATH = Field(default=None, description="Local credentials JSON path")


def _creds_required() -> dict:
    return {
        "error_code": "CREDENTIALS_REQUIRED",
        "error_message": "Provide credentials_path or credentials_json",
        "retryable": False,
        "original_provider_error": None,
    }


def _confirm_required() -> dict:
    return {
        "error_code": "CONFIRM_REQUIRED",
        "error_message": "Set confirm=true to execute this side-effecting tool",
        "retryable": False,
        "original_provider_error": None,
    }


def _svc(credentials_path, credentials_json) -> HubSpotService:
    if not credentials_path and not credentials_json:
        raise HubSpotError("missing credentials", error_code="CREDENTIALS_REQUIRED")
    return HubSpotService(credentials_json=credentials_json, credentials_path=credentials_path)


def _ok(payload: dict) -> dict:
    return {"success": True, **payload}


def _fail(err: HubSpotError) -> dict:
    return {"success": False, "error": err.to_dict()}


@mcp.tool()
def hubspot_search_contacts(
    query: str = Field(default="", description="Search query"),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    limit: int = Field(default=20),
) -> dict:
    """Search HubSpot contacts."""
    try:
        if not credentials_path and not credentials_json:
            return {"success": False, "error": _creds_required()}
        results = _svc(credentials_path, credentials_json).search("contacts", query, limit)
        return _ok({"results": results, "total_count": len(results)})
    except HubSpotError as e:
        return _fail(e)


@mcp.tool()
def hubspot_get_contact(
    contact_id: str = Field(..., description="HubSpot contact id"),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
) -> dict:
    """Get a HubSpot contact by id."""
    try:
        if not credentials_path and not credentials_json:
            return {"success": False, "error": _creds_required()}
        return _ok({"contact": _svc(credentials_path, credentials_json).get("contacts", contact_id)})
    except HubSpotError as e:
        return _fail(e)


@mcp.tool()
def hubspot_create_contact(
    properties_json: str = Field(..., description="JSON object of HubSpot contact properties"),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    confirm: bool = Field(default=False),
    dry_run: bool = Field(default=False),
) -> dict:
    """Create a HubSpot contact. Requires confirm=true."""
    try:
        if not credentials_path and not credentials_json:
            return {"success": False, "error": _creds_required()}
        props = json.loads(properties_json) if isinstance(properties_json, str) else properties_json
        if dry_run:
            return _ok({"dry_run": True, "message": "Would create contact", "properties": props})
        if not confirm:
            return {"success": False, "error": _confirm_required()}
        created = _svc(credentials_path, credentials_json).create("contacts", props)
        return _ok({"contact": created, "message": "Created contact"})
    except HubSpotError as e:
        return _fail(e)
    except json.JSONDecodeError:
        return {"success": False, "error": {"error_code": "VALIDATION_ERROR", "error_message": "properties_json must be JSON", "retryable": False}}


@mcp.tool()
def hubspot_update_contact(
    contact_id: str = Field(..., description="HubSpot contact id"),
    properties_json: str = Field(..., description="JSON object of properties to patch"),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    confirm: bool = Field(default=False),
    dry_run: bool = Field(default=False),
) -> dict:
    """Update a HubSpot contact. Requires confirm=true."""
    try:
        if not credentials_path and not credentials_json:
            return {"success": False, "error": _creds_required()}
        props = json.loads(properties_json) if isinstance(properties_json, str) else properties_json
        if dry_run:
            return _ok({"dry_run": True, "message": "Would update contact", "contact_id": contact_id})
        if not confirm:
            return {"success": False, "error": _confirm_required()}
        updated = _svc(credentials_path, credentials_json).update("contacts", contact_id, props)
        return _ok({"contact": updated, "message": "Updated contact"})
    except HubSpotError as e:
        return _fail(e)
    except json.JSONDecodeError:
        return {"success": False, "error": {"error_code": "VALIDATION_ERROR", "error_message": "properties_json must be JSON", "retryable": False}}


@mcp.tool()
def hubspot_search_companies(
    query: str = Field(default=""),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    limit: int = Field(default=20),
) -> dict:
    """Search HubSpot companies."""
    try:
        if not credentials_path and not credentials_json:
            return {"success": False, "error": _creds_required()}
        results = _svc(credentials_path, credentials_json).search("companies", query, limit)
        return _ok({"results": results, "total_count": len(results)})
    except HubSpotError as e:
        return _fail(e)


@mcp.tool()
def hubspot_get_company(
    company_id: str = Field(...),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
) -> dict:
    """Get a HubSpot company by id."""
    try:
        if not credentials_path and not credentials_json:
            return {"success": False, "error": _creds_required()}
        return _ok({"company": _svc(credentials_path, credentials_json).get("companies", company_id)})
    except HubSpotError as e:
        return _fail(e)


@mcp.tool()
def hubspot_create_company(
    properties_json: str = Field(..., description="JSON object of company properties"),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    confirm: bool = Field(default=False),
    dry_run: bool = Field(default=False),
) -> dict:
    """Create a HubSpot company. Requires confirm=true."""
    try:
        if not credentials_path and not credentials_json:
            return {"success": False, "error": _creds_required()}
        props = json.loads(properties_json) if isinstance(properties_json, str) else properties_json
        if dry_run:
            return _ok({"dry_run": True, "message": "Would create company"})
        if not confirm:
            return {"success": False, "error": _confirm_required()}
        created = _svc(credentials_path, credentials_json).create("companies", props)
        return _ok({"company": created, "message": "Created company"})
    except HubSpotError as e:
        return _fail(e)
    except json.JSONDecodeError:
        return {"success": False, "error": {"error_code": "VALIDATION_ERROR", "error_message": "properties_json must be JSON", "retryable": False}}


@mcp.tool()
def hubspot_search_deals(
    query: str = Field(default=""),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    limit: int = Field(default=20),
) -> dict:
    """Search HubSpot deals."""
    try:
        if not credentials_path and not credentials_json:
            return {"success": False, "error": _creds_required()}
        results = _svc(credentials_path, credentials_json).search("deals", query, limit)
        return _ok({"results": results, "total_count": len(results)})
    except HubSpotError as e:
        return _fail(e)


@mcp.tool()
def hubspot_get_deal(
    deal_id: str = Field(...),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
) -> dict:
    """Get a HubSpot deal by id."""
    try:
        if not credentials_path and not credentials_json:
            return {"success": False, "error": _creds_required()}
        return _ok({"deal": _svc(credentials_path, credentials_json).get("deals", deal_id)})
    except HubSpotError as e:
        return _fail(e)


@mcp.tool()
def hubspot_create_deal(
    properties_json: str = Field(..., description="JSON object of deal properties"),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    confirm: bool = Field(default=False),
    dry_run: bool = Field(default=False),
) -> dict:
    """Create a HubSpot deal. Requires confirm=true."""
    try:
        if not credentials_path and not credentials_json:
            return {"success": False, "error": _creds_required()}
        props = json.loads(properties_json) if isinstance(properties_json, str) else properties_json
        if dry_run:
            return _ok({"dry_run": True, "message": "Would create deal"})
        if not confirm:
            return {"success": False, "error": _confirm_required()}
        created = _svc(credentials_path, credentials_json).create("deals", props)
        return _ok({"deal": created, "message": "Created deal"})
    except HubSpotError as e:
        return _fail(e)
    except json.JSONDecodeError:
        return {"success": False, "error": {"error_code": "VALIDATION_ERROR", "error_message": "properties_json must be JSON", "retryable": False}}


_base_app = mcp.http_app()


async def health(_request):
    return JSONResponse({"status": "ok", "service": "hubspot-mcp"})


http_app = Starlette(
    routes=[Route("/health", health), Mount("/", _base_app)],
    lifespan=getattr(_base_app, "lifespan", None),
)

if __name__ == "__main__":
    mcp.run()
