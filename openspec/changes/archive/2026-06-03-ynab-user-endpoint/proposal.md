## Why

Feature 4 (from the backlog) calls for implementing **all endpoints under the YNAB "User" category**. In the [YNAB API](https://api.ynab.com/v1) that category contains a single endpoint — `GET /user` — which returns the authenticated user's id. Exposing it lets Claude confirm *who* the configured token belongs to (useful for verifying the connection and disambiguating accounts), and completes the User category as a clean, low-risk increment on the existing read-only integration.

## What Changes

- Add a `User` model (frozen dataclass with `id`) and a pure `parse_user` function for the `GET /user` response envelope.
- Add an async `get_user()` method to the existing `YnabClient` (calls `GET /user`).
- Add a `get_user` MCP tool (no arguments) that returns the authenticated user's id.
- Register `get_user` in the server factory alongside the existing tools.
- Extend tests (TDD) for the parser, the client method, and the tool; update the README tool list.

## Capabilities

### New Capabilities
<!-- None — this extends the existing ynab-integration capability. -->

### Modified Capabilities
- `ynab-integration`: Adds a new requirement for a read-only **user-info tool** (`get_user` → `GET /user`). No existing requirements change; this is an additive requirement within the capability.

## Impact

- **Changed files**: `ynab/models.py` (add `User` + `parse_user`), `ynab/client.py` (add `get_user`), `ynab/tools.py` (add `get_user` tool), `server.py` (register it), `README.md` (tool list). New tests under `tests/`.
- **Dependencies**: none new — reuses the existing `httpx` client, auth, error mapping, and config (`YNAB_TOKEN`).
- **Security**: unchanged — same bearer-token handling; the user id is non-sensitive and the token remains a secret.
- **External constraints**: one extra endpoint counts against YNAB's 200 requests/hour limit; the existing 429 → rate-limit mapping applies.
- **Out of scope**: still no OAuth, write operations, or delta sync.
