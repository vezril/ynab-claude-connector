## ADDED Requirements

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
