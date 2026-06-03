## Why

Feature 6 (from the backlog) calls for implementing the YNAB **"Categories" category**. That category has eight endpoints — three reads and five writes (create/update category, category group, and month category). The connector is deliberately **read-only**, so this change implements the **read endpoints** and explicitly defers the mutating ones to a future "write tools" feature. We already expose the list endpoint (`getCategories` as `list_categories`); this adds the two single-category reads, completing read coverage of the category.

## What Changes

- **Add `get_category`** (`GET /plans/{plan_id}/categories/{category_id}`): returns a single category by id.
- **Add `get_month_category`** (`GET /plans/{plan_id}/months/{month}/categories/{category_id}`): returns a single category with the budgeted/activity/balance for a specific month. `month` accepts `current` (the current month) or an ISO date (`YYYY-MM-01`).
- Both accept a `plan_id` defaulting to the `last-used` alias, consistent with the other plan-scoped tools.
- Add a pure `parse_category` parser (reads the `data.category` envelope) reusing the existing `Category` model; add client methods and register the two tools.
- Extend tests (TDD) for the parser, client methods, tools, and edge cases; update the README tool list.

## Capabilities

### New Capabilities
<!-- None — extends the existing ynab-integration capability. -->

### Modified Capabilities
- `ynab-integration`: Adds a new requirement for **single-category read tools** (`get_category`, `get_month_category`). No existing requirements change.

## Impact

- **Changed files**: `ynab/models.py` (add `parse_category`), `ynab/client.py` (add `get_category`, `get_month_category`), `ynab/tools.py` (add the two tools), `server.py` (register), `README.md`, and the corresponding `tests/`.
- **Dependencies**: none new.
- **Security**: unchanged — same bearer-token handling; reads only.
- **External constraints**: two more endpoints against YNAB's 200 req/hour limit; existing 429 mapping applies. A 404 for a missing category surfaces as the typed API error.
- **Out of scope (explicit)**: the five **write** endpoints — `createCategory`, `updateCategory`, `updateMonthCategory`, `createCategoryGroup`, `updateCategoryGroup` — are deferred to a dedicated write-tools feature (keeps the connector read-only for now). Also out of scope: OAuth, delta sync.
