## Why

Feature 9 (from the backlog) calls for implementing the YNAB **"Months" category**. Like Payee Locations, this category is **entirely read-only** in the YNAB API — its two endpoints are both GETs, so the whole category is covered without deferring anything. Months give Claude per-month budget totals (income, budgeted, activity, to-be-budgeted, age of money), which is core to budget insights.

The category has two endpoints: `getPlanMonths` (list of month summaries) and `getPlanMonth` (a single month).

## What Changes

- **Add `list_months`** (`GET /plans/{plan_id}/months`): the plan's month summaries.
- **Add `get_month`** (`GET /plans/{plan_id}/months/{month}`): a single month; `month` accepts `current` (the current calendar month) or an ISO date (`YYYY-MM-01`).
- Both accept a `plan_id` defaulting to the `last-used` alias.
- Add a `Month` model (month, note, income, budgeted, activity, to_be_budgeted, age_of_money, deleted — amounts in milliunits) and pure `parse_months`/`parse_month` parsers; add client methods and register the two tools.
- Extend tests (TDD) for the parsers, client methods, tools, and edge cases; update the README tool list.

## Capabilities

### New Capabilities
<!-- None — extends the existing ynab-integration capability. -->

### Modified Capabilities
- `ynab-integration`: Adds a new requirement for **read-only month tools** (`list_months`, `get_month`). No existing requirements change.

## Impact

- **Changed files**: `ynab/models.py` (add `Month` + parsers), `ynab/client.py` (add `list_months`, `get_month`), `ynab/tools.py` (add the two tools), `server.py` (register), `README.md`, and the corresponding `tests/`.
- **Dependencies**: none new.
- **Security**: unchanged — same bearer-token handling; reads only.
- **External constraints**: two more endpoints against YNAB's 200 req/hour limit; existing 429 mapping applies. A 404 for a missing month surfaces as the typed API error. `getPlanMonths` supports `last_knowledge_of_server` (delta) — not used here.
- **Design note**: `getPlanMonth` (`MonthDetail`) embeds the month's `categories`; `get_month` returns the **month summary** (not the embedded categories), since per-category month figures are already available via `get_month_category` (Feature 6).
- **Out of scope**: OAuth, delta sync. (No writes exist for this category, so none are deferred.)
