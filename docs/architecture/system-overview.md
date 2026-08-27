# HubSpot MCP — architecture

Thin FastMCP façade over HubSpot CRM v3. Credentials are never in workflow params; Studio Connect stores an OAuth bundle and MCP injects `credentials_json` when ADR-0070 tokens `hubspot-mcp` / `hubspot` hit.

Injected bundle includes `token`/`access_token`, `refresh_token`, `client_id`, `client_secret`, `token_uri`, and `expiry`. **Integrations** refreshes near-expiry tokens on inject and writes rotated refresh tokens back to the vault (HubSpot RT rotation). This MCP never refreshes — local refresh without vault write-back would invalidate Connect.

Tools: search/get/create/update contacts, companies, deals. Writes require `confirm=true`.
