## ADDED Requirements

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
