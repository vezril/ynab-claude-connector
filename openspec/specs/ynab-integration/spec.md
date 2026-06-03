# ynab-integration Specification

## Purpose
Defines the YNAB (You Need A Budget) integration for the connector: environment-loaded YNAB credentials with the access token treated as a secret, an authenticated read-only HTTP client that targets the YNAB API and unwraps its `data` envelope, a typed error taxonomy for non-success responses, and read-only MCP tools for listing budgets, accounts, categories, and transactions with monetary values preserved in YNAB milliunits.

## Requirements

### Requirement: YNAB credentials are loaded from the environment as a secret
The connector SHALL read a YNAB Personal Access Token and the YNAB API base URL from the environment. The token SHALL be treated as a secret: it MUST NOT appear in logs or in any configuration/object representation. The server SHALL start successfully without a token; a missing token SHALL only cause a failure when a YNAB tool is invoked.

#### Scenario: Base URL defaults and token is optional at startup
- **WHEN** configuration is built from an environment without YNAB variables
- **THEN** the YNAB API base URL defaults to `https://api.ynab.com/v1`, the token is absent, and the server still starts (the `ping` tool works)

#### Scenario: Token is not exposed in representations
- **WHEN** the configuration object containing a YNAB token is rendered via its string/representation form
- **THEN** the token value does not appear in that output

#### Scenario: Edge case — invoking a YNAB tool without a token fails clearly
- **WHEN** a YNAB tool is invoked while no token is configured
- **THEN** it raises an authentication error whose message indicates the token environment variable must be set, before any network call is attempted

### Requirement: Authenticated read-only access to the YNAB API
The connector SHALL provide an HTTP client that sends requests to the configured YNAB base URL with an `Authorization: Bearer <token>` header, and SHALL unwrap the YNAB `data` envelope when reading successful responses.

#### Scenario: Requests carry the bearer token
- **WHEN** the client issues any YNAB request with a configured token
- **THEN** the request includes the header `Authorization: Bearer <token>` targeting the configured base URL

#### Scenario: Successful responses are unwrapped from the data envelope
- **WHEN** the API returns `200` with a body shaped `{"data": {...}}`
- **THEN** the client returns the inner resource data mapped to typed models, not the raw envelope

### Requirement: API errors are mapped to a typed error taxonomy
The connector SHALL translate non-success YNAB responses into distinct, typed errors: authentication failures (HTTP 401/403), rate limiting (HTTP 429), and other API errors (other non-2xx), preserving the YNAB error name/detail where available.

#### Scenario: Unauthorized response maps to an auth error
- **WHEN** the API returns `401`
- **THEN** the client raises an authentication error distinct from other error types

#### Scenario: Rate-limited response maps to a rate-limit error
- **WHEN** the API returns `429`
- **THEN** the client raises a rate-limit error whose message conveys that the YNAB request limit was exceeded

#### Scenario: Edge case — other server errors map to a generic API error
- **WHEN** the API returns `500` with a `{"error": {...}}` body
- **THEN** the client raises a generic API error carrying the HTTP status and the YNAB error detail

### Requirement: Read-only plan tools
The connector SHALL expose MCP tools to list plans, accounts, categories, and transactions, targeting the YNAB `/plans` paths. `list_plans` SHALL take no arguments; the account, category, and transaction tools SHALL accept a `plan_id` argument defaulting to the YNAB `last-used` alias (the most recently used plan). Monetary values SHALL be returned in YNAB milliunits without lossy conversion.

#### Scenario: Listing plans returns the user's plans
- **WHEN** the `list_plans` tool is invoked with a valid token
- **THEN** it returns the plans (ids and names) parsed from `GET /plans`

#### Scenario: Plan-scoped tools default to the last-used plan
- **WHEN** `list_accounts` (or categories/transactions) is invoked without a `plan_id`
- **THEN** the request targets the plan path using the `last-used` alias (e.g. `GET /plans/last-used/accounts`)

#### Scenario: Account balances are returned in milliunits
- **WHEN** `list_accounts` returns accounts
- **THEN** each account's balance is the integer milliunit value from the API, not a rounded currency amount

#### Scenario: Edge case — empty or partial payloads parse safely
- **WHEN** an endpoint returns an empty resource list or items missing optional fields
- **THEN** parsing yields an empty result (or models with those optional fields absent) without raising

#### Scenario: Edge case — tool input schemas are typed
- **WHEN** the server lists its tools
- **THEN** each plan-scoped tool exposes an input schema derived from its type-hinted signature (e.g. `plan_id` as a string), with no untyped parameters

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

### Requirement: Single plan summary tool
The connector SHALL expose a `get_plan` tool that accepts a `plan_id` argument (defaulting to the `last-used` alias) and returns a curated summary of `GET /plans/{plan_id}`: plan metadata (id, name, last-modified, first/last month), the currency and date format, and counts of the nested entities. The tool SHALL NOT return the full plan export.

#### Scenario: Getting a plan returns a summary with entity counts
- **WHEN** the `get_plan` tool is invoked with a valid token
- **THEN** it returns the plan metadata, currency format, date format, and counts of accounts, categories, payees, months, transactions, and scheduled transactions parsed from `GET /plans/{plan_id}`

#### Scenario: Defaults to the last-used plan
- **WHEN** `get_plan` is invoked without a `plan_id`
- **THEN** the request targets `GET /plans/last-used`

#### Scenario: Edge case — the full export is not dumped
- **WHEN** `get_plan` returns its result
- **THEN** the result contains counts of nested entities, not the nested arrays themselves

#### Scenario: Edge case — missing nested arrays count as zero
- **WHEN** the plan payload omits some nested arrays
- **THEN** those counts are zero and parsing does not raise

### Requirement: Plan settings tool
The connector SHALL expose a `get_plan_settings` tool that accepts a `plan_id` argument (defaulting to the `last-used` alias) and returns the plan's date format and currency format from `GET /plans/{plan_id}/settings`.

#### Scenario: Getting plan settings returns date and currency format
- **WHEN** the `get_plan_settings` tool is invoked with a valid token
- **THEN** it returns the `date_format` and `currency_format` parsed from `GET /plans/{plan_id}/settings`

#### Scenario: Request carries the bearer token to the settings path
- **WHEN** `get_plan_settings` issues its request
- **THEN** the request targets `GET /plans/{plan_id}/settings` with the header `Authorization: Bearer <token>`

#### Scenario: Edge case — missing token fails before any network call
- **WHEN** `get_plan_settings` is invoked while no token is configured
- **THEN** it raises an authentication error indicating the token environment variable must be set, before any network call is attempted
