## Why

Feature 8 (from the backlog) calls for implementing the YNAB **"Payee Locations" category**. Unlike Categories/Payees, this category is **entirely read-only** in the YNAB API — payee locations are created automatically from transactions, so all three endpoints are GETs and the whole category is covered without deferring anything. Exposing them lets Claude see where a payee has been transacted (lat/long), complementing the payee tools.

The category has three endpoints: `getPayeeLocations` (list), `getPayeeLocationById` (single), and `getPayeeLocationsByPayee` (locations for one payee).

## What Changes

- **Add `list_payee_locations`** (`GET /plans/{plan_id}/payee_locations`): all payee locations for a plan.
- **Add `get_payee_location`** (`GET /plans/{plan_id}/payee_locations/{payee_location_id}`): a single payee location by id.
- **Add `list_payee_locations_for_payee`** (`GET /plans/{plan_id}/payees/{payee_id}/payee_locations`): locations for a specific payee.
- All accept a `plan_id` defaulting to the `last-used` alias.
- Add a `PayeeLocation` model and pure `parse_payee_locations`/`parse_payee_location` parsers; add client methods and register the three tools.
- Extend tests (TDD) for the parsers, client methods, tools, and edge cases; update the README tool list.

## Capabilities

### New Capabilities
<!-- None — extends the existing ynab-integration capability. -->

### Modified Capabilities
- `ynab-integration`: Adds a new requirement for **read-only payee-location tools** (`list_payee_locations`, `get_payee_location`, `list_payee_locations_for_payee`). No existing requirements change.

## Impact

- **Changed files**: `ynab/models.py` (add `PayeeLocation` + parsers), `ynab/client.py` (add three methods), `ynab/tools.py` (add three tools), `server.py` (register), `README.md`, and the corresponding `tests/`.
- **Dependencies**: none new.
- **Security**: unchanged — same bearer-token handling; reads only.
- **External constraints**: three more endpoints against YNAB's 200 req/hour limit; existing 429 mapping applies. A 404 for a missing location surfaces as the typed API error.
- **Out of scope**: OAuth, delta sync. (No writes exist for this category, so none are deferred.)
