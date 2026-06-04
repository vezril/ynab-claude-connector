## ADDED Requirements

### Requirement: Read-only scheduled-transaction tools
The connector SHALL expose MCP tools to read scheduled (recurring/upcoming) transactions: `list_scheduled_transactions` (all for a plan) and `get_scheduled_transaction` (a single one by id). Both SHALL accept a `plan_id` argument defaulting to the `last-used` alias, and SHALL return typed `ScheduledTransaction` data (id, first/next date, frequency, amount, account id, payee id, category id, memo, deleted) parsed from the `data.scheduled_transactions` / `data.scheduled_transaction` envelopes, with amounts in milliunits. These tools are read-only; scheduled-transaction write operations are out of scope.

#### Scenario: Listing scheduled transactions for a plan
- **WHEN** the `list_scheduled_transactions` tool is invoked with a valid token
- **THEN** it returns the scheduled transactions parsed from `GET /plans/{plan_id}/scheduled_transactions`

#### Scenario: Getting a scheduled transaction by id
- **WHEN** the `get_scheduled_transaction` tool is invoked with a valid token and a scheduled-transaction id
- **THEN** it returns the scheduled transaction parsed from `GET /plans/{plan_id}/scheduled_transactions/{scheduled_transaction_id}`

#### Scenario: Plan defaults to the last-used alias
- **WHEN** either tool is invoked without a `plan_id`
- **THEN** the request targets the plan path using the `last-used` alias

#### Scenario: Request carries the bearer token
- **WHEN** either tool issues its request
- **THEN** the request includes the header `Authorization: Bearer <token>` targeting the configured base URL

#### Scenario: Edge case — empty or partial payloads parse safely
- **WHEN** `list_scheduled_transactions` returns an empty list, or a record omits optional fields (e.g. `payee_id`, `memo`)
- **THEN** parsing yields an empty result (or models with those fields absent) without raising

#### Scenario: Edge case — a missing scheduled transaction surfaces as a typed API error
- **WHEN** the requested scheduled transaction does not exist and the API responds with `404`
- **THEN** `get_scheduled_transaction` raises the typed API error (carrying the HTTP status), not an empty result
