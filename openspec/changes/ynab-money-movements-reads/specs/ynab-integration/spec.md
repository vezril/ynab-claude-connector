## ADDED Requirements

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
