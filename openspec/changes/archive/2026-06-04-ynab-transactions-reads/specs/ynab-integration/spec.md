## ADDED Requirements

### Requirement: Read-only transaction lookup tools
The connector SHALL expose MCP tools to read transactions beyond the plan-wide list: `get_transaction` (a single transaction by id) and four scoped list tools — `list_transactions_by_account`, `list_transactions_by_category`, `list_transactions_by_payee`, and `list_transactions_by_month`. All SHALL accept a `plan_id` argument defaulting to the `last-used` alias; `list_transactions_by_month` SHALL also accept a `month` (`current` or an ISO `YYYY-MM-01`). The tools SHALL return typed `Transaction` data parsed from the `data.transaction` / `data.transactions` envelopes, with amounts in milliunits. These tools are read-only; transaction write operations are out of scope.

#### Scenario: Getting a transaction by id
- **WHEN** the `get_transaction` tool is invoked with a valid token and a transaction id
- **THEN** it returns the transaction parsed from `GET /plans/{plan_id}/transactions/{transaction_id}`

#### Scenario: Listing transactions by account
- **WHEN** the `list_transactions_by_account` tool is invoked with an account id
- **THEN** it returns the transactions parsed from `GET /plans/{plan_id}/accounts/{account_id}/transactions`

#### Scenario: Listing transactions by category
- **WHEN** the `list_transactions_by_category` tool is invoked with a category id
- **THEN** it returns the transactions parsed from `GET /plans/{plan_id}/categories/{category_id}/transactions`

#### Scenario: Listing transactions by payee
- **WHEN** the `list_transactions_by_payee` tool is invoked with a payee id
- **THEN** it returns the transactions parsed from `GET /plans/{plan_id}/payees/{payee_id}/transactions`

#### Scenario: Listing transactions by month
- **WHEN** the `list_transactions_by_month` tool is invoked with a `month`
- **THEN** it returns the transactions parsed from `GET /plans/{plan_id}/months/{month}/transactions`

#### Scenario: Plan defaults to the last-used alias
- **WHEN** any of these tools is invoked without a `plan_id`
- **THEN** the request targets the plan path using the `last-used` alias

#### Scenario: Edge case — a missing transaction surfaces as a typed API error
- **WHEN** the requested transaction does not exist and the API responds with `404`
- **THEN** `get_transaction` raises the typed API error (carrying the HTTP status), not an empty result

#### Scenario: Edge case — empty list and malformed single payloads
- **WHEN** a scoped list endpoint returns an empty list, or the single endpoint omits the `transaction` object or its `id`
- **THEN** the list parses to an empty result, and the single parse raises rather than returning a transaction with empty fields
