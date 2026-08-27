# Changelog

## 2026-08-27

### Changed

- Durable HubSpot auth after Connect: **Integrations inject** refreshes near-expiry access tokens and persists rotated `refresh_token`s. HubSpot MCP uses injected access tokens only (no local refresh).

### Fixed

- HubSpot tools no longer die ~30 minutes after Connect; refresh + vault write-back happens on each MCP inject.

## 2026-08-26

### Added

- Initial **hubspot-mcp** FastMCP tool-server (contacts, companies, deals).
- Studio vault inject via ADR-0070 tokens `hubspot-mcp` / `hubspot`.
