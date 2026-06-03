## RENAMED Requirements

- FROM: `### Requirement: Read-only budget tools`
- TO: `### Requirement: Read-only plan tools`

## MODIFIED Requirements

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

## ADDED Requirements

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
