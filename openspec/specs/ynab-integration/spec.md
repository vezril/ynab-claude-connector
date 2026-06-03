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

### Requirement: Read-only budget tools
The connector SHALL expose MCP tools to list budgets, accounts, categories, and transactions. `list_budgets` SHALL take no arguments; the account, category, and transaction tools SHALL accept a `budget_id` argument defaulting to the YNAB `default` alias (the last-used budget). Monetary values SHALL be returned in YNAB milliunits without lossy conversion.

#### Scenario: Listing budgets returns the user's budgets
- **WHEN** the `list_budgets` tool is invoked with a valid token
- **THEN** it returns the budgets (ids and names) parsed from `GET /budgets`

#### Scenario: Budget-scoped tools default to the last-used budget
- **WHEN** `list_accounts` (or categories/transactions) is invoked without a `budget_id`
- **THEN** the request targets the budget path using the `default` alias

#### Scenario: Account balances are returned in milliunits
- **WHEN** `list_accounts` returns accounts
- **THEN** each account's balance is the integer milliunit value from the API, not a rounded currency amount

#### Scenario: Edge case — empty or partial payloads parse safely
- **WHEN** an endpoint returns an empty resource list or items missing optional fields
- **THEN** parsing yields an empty result (or models with those optional fields absent) without raising

#### Scenario: Edge case — tool input schemas are typed
- **WHEN** the server lists its tools
- **THEN** each YNAB tool exposes an input schema derived from its type-hinted signature (e.g. `budget_id` as a string), with no untyped parameters
