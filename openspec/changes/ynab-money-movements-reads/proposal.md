## Why

Feature 10 (from the backlog) calls for implementing the YNAB **"Money Movements" category** — YNAB's record of money moved between categories (budget reallocations), and the groups those movements belong to. Like Months and Payee Locations, this category is **entirely read-only** in the YNAB API (all four endpoints are GETs), so the whole category is covered without deferring anything. Exposing it lets Claude see how budgeted money has been shuffled around, complementing the category/month tools.

The category has four endpoints: list money movements (plan-wide and per-month) and list money movement groups (plan-wide and per-month).

## What Changes

- **Add `list_money_movements`** (`GET /plans/{plan_id}/money_movements`) and **`list_money_movements_for_month`** (`GET /plans/{plan_id}/months/{month}/money_movements`).
- **Add `list_money_movement_groups`** (`GET /plans/{plan_id}/money_movement_groups`) and **`list_money_movement_groups_for_month`** (`GET /plans/{plan_id}/months/{month}/money_movement_groups`).
- All accept a `plan_id` defaulting to the `last-used` alias; the per-month variants accept a `month` (`current` or ISO `YYYY-MM-01`).
- Add `MoneyMovement` and `MoneyMovementGroup` models and pure `parse_money_movements`/`parse_money_movement_groups` parsers; add client methods and register the four tools.
- Extend tests (TDD) for the parsers, client methods, tools, and edge cases; update the README tool list.

## Capabilities

### New Capabilities
<!-- None — extends the existing ynab-integration capability. -->

### Modified Capabilities
- `ynab-integration`: Adds a new requirement for **read-only money-movement tools** (the four list tools). No existing requirements change.

## Impact

- **Changed files**: `ynab/models.py` (add `MoneyMovement`, `MoneyMovementGroup` + parsers), `ynab/client.py` (add four methods), `ynab/tools.py` (add four tools), `server.py` (register), `README.md`, and the corresponding `tests/`.
- **Dependencies**: none new.
- **Security**: unchanged — same bearer-token handling; reads only.
- **External constraints**: four more endpoints against YNAB's 200 req/hour limit; existing 429/404 mapping applies. The list endpoints support `server_knowledge` (delta) — not used here.
- **Out of scope**: OAuth, delta sync. (No writes exist for this category, so none are deferred.)
