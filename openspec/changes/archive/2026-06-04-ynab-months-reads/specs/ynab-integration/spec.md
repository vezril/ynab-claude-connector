## ADDED Requirements

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
