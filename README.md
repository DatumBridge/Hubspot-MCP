# HubSpot MCP

Thin HubSpot CRM tool-server for DatumBridge. Tools: search/get/create/update contacts, companies, and deals.

**Publish name:** `HubSpot MCP` (k8s host `hubspot-mcp-main`).

**Auth:** Studio **Account → Integrations → Connect HubSpot**. Vault injects `credentials_json` (`token` / `access_token`, plus refresh material). Do not map tokens in workflows. Access tokens expire ~30 minutes; **Integrations** refreshes on inject and persists rotated refresh tokens (HubSpot rotates RTs). This MCP uses the injected access token only — it does not refresh. Writes require `confirm=true` (`dry_run=true` to preview).

## Tools

| Tool | Notes |
|---|---|
| `hubspot_search_contacts` / `hubspot_get_contact` | Read |
| `hubspot_create_contact` / `hubspot_update_contact` | `confirm=true` |
| `hubspot_search_companies` / `hubspot_get_company` / `hubspot_create_company` | Create is confirm-gated |
| `hubspot_search_deals` / `hubspot_get_deal` / `hubspot_create_deal` | Create is confirm-gated |

Run: `uvicorn app.mcp_server:http_app --host 0.0.0.0 --port 8000`
