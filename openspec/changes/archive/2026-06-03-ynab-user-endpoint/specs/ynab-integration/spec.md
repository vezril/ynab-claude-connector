## ADDED Requirements

### Requirement: Read-only user-info tool
The connector SHALL expose an MCP tool named `get_user` that takes no arguments and returns the authenticated user's id, obtained from the YNAB User category endpoint `GET /user`. The tool SHALL reuse the existing authentication, error mapping, and configuration; the returned user id is non-sensitive while the token remains a secret.

#### Scenario: Getting the user returns the authenticated user's id
- **WHEN** the `get_user` tool is invoked with a valid token
- **THEN** it returns the user id parsed from `GET /user` (response shape `{"data": {"user": {"id": ...}}}`)

#### Scenario: Request carries the bearer token
- **WHEN** the `get_user` tool issues its request
- **THEN** the request targets `GET /user` on the configured base URL with the header `Authorization: Bearer <token>`

#### Scenario: Edge case — missing token fails before any network call
- **WHEN** `get_user` is invoked while no token is configured
- **THEN** it raises an authentication error indicating the token environment variable must be set, before any network call is attempted

#### Scenario: Edge case — malformed user payload raises rather than returning an empty id
- **WHEN** `GET /user` returns a body missing the `user` object or its `id`
- **THEN** parsing raises an error instead of returning a `User` with an empty id

#### Scenario: Edge case — tool input schema is typed
- **WHEN** the server lists its tools
- **THEN** `get_user` appears with an input schema derived from its (argument-free) type-hinted signature
