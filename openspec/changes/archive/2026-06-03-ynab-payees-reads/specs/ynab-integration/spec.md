## ADDED Requirements

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
