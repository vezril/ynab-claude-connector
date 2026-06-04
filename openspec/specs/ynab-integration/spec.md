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

### Requirement: Single-category read tools
The connector SHALL expose MCP tools to read a single category: `get_category` (by category id) and `get_month_category` (a category's values for a specific month). Both SHALL accept a `plan_id` argument defaulting to the `last-used` alias; `get_month_category` SHALL also accept a `month` argument (accepting `current` or an ISO `YYYY-MM-01`). Both SHALL return the typed `Category` parsed from the `data.category` envelope, with monetary values in milliunits. These tools are read-only; category write operations are out of scope.

#### Scenario: Getting a category by id
- **WHEN** the `get_category` tool is invoked with a valid token and a category id
- **THEN** it returns the category parsed from `GET /plans/{plan_id}/categories/{category_id}`

#### Scenario: Getting a category for a specific month
- **WHEN** the `get_month_category` tool is invoked with a `month` and a category id
- **THEN** it returns the category parsed from `GET /plans/{plan_id}/months/{month}/categories/{category_id}`, with that month's budgeted/activity/balance

#### Scenario: Plan defaults to the last-used alias
- **WHEN** `get_category` (or `get_month_category`) is invoked without a `plan_id`
- **THEN** the request targets the plan path using the `last-used` alias

#### Scenario: Request carries the bearer token
- **WHEN** either tool issues its request
- **THEN** the request includes the header `Authorization: Bearer <token>` targeting the configured base URL

#### Scenario: Edge case — a missing category surfaces as a typed API error
- **WHEN** the requested category does not exist and the API responds with `404`
- **THEN** the tool raises the typed API error (carrying the HTTP status), not an empty result

#### Scenario: Edge case — malformed payload raises rather than returning an empty category
- **WHEN** the response body omits the `category` object or its `id`
- **THEN** parsing raises an error instead of returning a `Category` with empty fields

### Requirement: Read-only payee tools
The connector SHALL expose MCP tools to read payees: `list_payees` (all payees for a plan) and `get_payee` (a single payee by id). Both SHALL accept a `plan_id` argument defaulting to the `last-used` alias, and SHALL return typed `Payee` data (id, name, transfer account id, deleted flag) parsed from the `data.payees` / `data.payee` envelopes. These tools are read-only; payee write operations are out of scope.

#### Scenario: Listing payees returns the plan's payees
- **WHEN** the `list_payees` tool is invoked with a valid token
- **THEN** it returns the payees parsed from `GET /plans/{plan_id}/payees`

#### Scenario: Getting a payee by id
- **WHEN** the `get_payee` tool is invoked with a valid token and a payee id
- **THEN** it returns the payee parsed from `GET /plans/{plan_id}/payees/{payee_id}`

#### Scenario: Plan defaults to the last-used alias
- **WHEN** `list_payees` (or `get_payee`) is invoked without a `plan_id`
- **THEN** the request targets the plan path using the `last-used` alias

#### Scenario: Request carries the bearer token
- **WHEN** either tool issues its request
- **THEN** the request includes the header `Authorization: Bearer <token>` targeting the configured base URL

#### Scenario: Edge case — empty or partial payee payloads parse safely
- **WHEN** `list_payees` returns an empty list, or a payee omits the optional `transfer_account_id`
- **THEN** parsing yields an empty result (or a payee with `transfer_account_id` absent) without raising

#### Scenario: Edge case — a missing payee surfaces as a typed API error
- **WHEN** the requested payee does not exist and the API responds with `404`
- **THEN** `get_payee` raises the typed API error (carrying the HTTP status), not an empty result

### Requirement: Read-only payee-location tools
The connector SHALL expose MCP tools to read payee locations: `list_payee_locations` (all for a plan), `get_payee_location` (a single location by id), and `list_payee_locations_for_payee` (locations for one payee). All SHALL accept a `plan_id` argument defaulting to the `last-used` alias, and SHALL return typed `PayeeLocation` data (id, payee id, latitude, longitude, deleted) parsed from the `data.payee_locations` / `data.payee_location` envelopes. The Payee Locations category is read-only in the YNAB API.

#### Scenario: Listing payee locations for a plan
- **WHEN** the `list_payee_locations` tool is invoked with a valid token
- **THEN** it returns the payee locations parsed from `GET /plans/{plan_id}/payee_locations`

#### Scenario: Getting a payee location by id
- **WHEN** the `get_payee_location` tool is invoked with a valid token and a payee-location id
- **THEN** it returns the location parsed from `GET /plans/{plan_id}/payee_locations/{payee_location_id}`

#### Scenario: Listing locations for a specific payee
- **WHEN** the `list_payee_locations_for_payee` tool is invoked with a payee id
- **THEN** it returns the locations parsed from `GET /plans/{plan_id}/payees/{payee_id}/payee_locations`

#### Scenario: Plan defaults to the last-used alias
- **WHEN** any payee-location tool is invoked without a `plan_id`
- **THEN** the request targets the plan path using the `last-used` alias

#### Scenario: Edge case — empty or partial payloads parse safely
- **WHEN** a list endpoint returns an empty list, or a location omits the optional `latitude`/`longitude`
- **THEN** parsing yields an empty result (or a location with those fields absent) without raising

#### Scenario: Edge case — a missing location surfaces as a typed API error
- **WHEN** the requested payee location does not exist and the API responds with `404`
- **THEN** `get_payee_location` raises the typed API error (carrying the HTTP status), not an empty result

### Requirement: Read-only month tools
The connector SHALL expose MCP tools to read budget months: `list_months` (all month summaries for a plan) and `get_month` (a single month). Both SHALL accept a `plan_id` argument defaulting to the `last-used` alias; `get_month` SHALL also accept a `month` argument (accepting `current` or an ISO `YYYY-MM-01`). Both SHALL return typed `Month` data (month, note, income, budgeted, activity, to-be-budgeted, age of money, deleted) with monetary values in milliunits. `get_month` returns the month summary; per-category month figures are available via `get_month_category`. The Months category is read-only in the YNAB API.

#### Scenario: Listing months returns the plan's month summaries
- **WHEN** the `list_months` tool is invoked with a valid token
- **THEN** it returns the months parsed from `GET /plans/{plan_id}/months`

#### Scenario: Getting a single month
- **WHEN** the `get_month` tool is invoked with a `month` value
- **THEN** it returns the month parsed from `GET /plans/{plan_id}/months/{month}`, with amounts in milliunits

#### Scenario: Plan defaults to the last-used alias
- **WHEN** `list_months` (or `get_month`) is invoked without a `plan_id`
- **THEN** the request targets the plan path using the `last-used` alias

#### Scenario: Request carries the bearer token
- **WHEN** either tool issues its request
- **THEN** the request includes the header `Authorization: Bearer <token>` targeting the configured base URL

#### Scenario: Edge case — empty or partial payloads parse safely
- **WHEN** `list_months` returns an empty list, or a month omits the optional `note`/`age_of_money`
- **THEN** parsing yields an empty result (or a month with those fields absent) without raising

#### Scenario: Edge case — a missing month surfaces as a typed API error
- **WHEN** the requested month does not exist and the API responds with `404`
- **THEN** `get_month` raises the typed API error (carrying the HTTP status), not an empty result

### Requirement: Read-only money-movement tools
The connector SHALL expose MCP tools to read money movements and money movement groups: `list_money_movements` and `list_money_movement_groups` (plan-wide), plus `list_money_movements_for_month` and `list_money_movement_groups_for_month` (scoped to a month). All SHALL accept a `plan_id` argument defaulting to the `last-used` alias; the per-month tools SHALL also accept a `month` argument (`current` or an ISO `YYYY-MM-01`). The tools SHALL return typed `MoneyMovement` / `MoneyMovementGroup` data parsed from the `data.money_movements` / `data.money_movement_groups` envelopes, with amounts in milliunits. The Money Movements category is read-only in the YNAB API.

#### Scenario: Listing money movements for a plan
- **WHEN** the `list_money_movements` tool is invoked with a valid token
- **THEN** it returns the movements parsed from `GET /plans/{plan_id}/money_movements`

#### Scenario: Listing money movements for a month
- **WHEN** the `list_money_movements_for_month` tool is invoked with a `month`
- **THEN** it returns the movements parsed from `GET /plans/{plan_id}/months/{month}/money_movements`

#### Scenario: Listing money movement groups for a plan
- **WHEN** the `list_money_movement_groups` tool is invoked with a valid token
- **THEN** it returns the groups parsed from `GET /plans/{plan_id}/money_movement_groups`

#### Scenario: Listing money movement groups for a month
- **WHEN** the `list_money_movement_groups_for_month` tool is invoked with a `month`
- **THEN** it returns the groups parsed from `GET /plans/{plan_id}/months/{month}/money_movement_groups`

#### Scenario: Plan defaults to the last-used alias
- **WHEN** any money-movement tool is invoked without a `plan_id`
- **THEN** the request targets the plan path using the `last-used` alias

#### Scenario: Edge case — empty or partial payloads parse safely
- **WHEN** a list endpoint returns an empty list, or a movement omits optional fields (e.g. `note`, `from_category_id`)
- **THEN** parsing yields an empty result (or models with those fields absent) without raising

#### Scenario: Edge case — API errors surface as typed errors
- **WHEN** the API responds with a non-success status (e.g. `404` for an unknown plan)
- **THEN** the tool raises the typed API error (carrying the HTTP status), not an empty result
