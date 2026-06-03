## Why

Feature 5 (from the backlog) calls for implementing **all endpoints under the YNAB "Plans" category**. Verifying against the live [YNAB OpenAPI spec](https://api.ynab.com/papi/open_api_spec.yaml) surfaced two things: (1) YNAB has rebranded "Budgets" → **"Plans"**, and the API now serves these endpoints under **`/plans`**, with no `/budgets` paths in the current spec; (2) our Feature 3 tools call `/budgets/...`, which is off the documented contract (it slipped through because tests assert our own mocked paths). So this change both **completes the Plans category** and **corrects the existing tools** to the documented `/plans` paths and YNAB's "plan" terminology.

The Plans category has three endpoints: `GET /plans` (list — we already expose this), `GET /plans/{plan_id}` (full plan export), and `GET /plans/{plan_id}/settings`.

## What Changes

- **BREAKING (tool rename):** rename the existing YNAB tools to plan terminology — `list_budgets` → `list_plans`; the `budget_id` argument on `list_accounts`/`list_categories`/`list_transactions` → `plan_id`. (Pre-1.0; acceptable.)
- **Correctness fix:** migrate all YNAB request paths from `/budgets/...` to `/plans/...`. Rename the `Budget` model → `Plan` and `parse_budgets` → `parse_plans`.
- Change the default plan alias from `"default"` to **`"last-used"`** — both are valid YNAB aliases, but `"default"` only resolves when the user has enabled default-plan selection, whereas `"last-used"` always works.
- **Add `get_plan`** (`GET /plans/{plan_id}`): returns a **curated summary** — plan metadata (id, name, last_modified_on, first/last month), currency & date format, and **entity counts** (accounts, categories, payees, months, transactions, scheduled transactions). The full export is intentionally not dumped to stay within MCP tool-result limits; detailed data remains available via the existing list tools.
- **Add `get_plan_settings`** (`GET /plans/{plan_id}/settings`): returns the plan's date format and currency format.
- Extend tests (TDD) for the renames, new models/parsers/client methods/tools, and edge cases; update the README tool list.

## Capabilities

### New Capabilities
<!-- None — extends the existing ynab-integration capability. -->

### Modified Capabilities
- `ynab-integration`: The "Read-only budget tools" requirement is renamed/updated to **plan** terminology and `/plans` paths, and two new requirements are added — a **single-plan summary tool** and a **plan-settings tool**.

## Impact

- **Changed files**: `ynab/models.py` (`Budget`→`Plan`; add `PlanDetailSummary`, `PlanSettings`, `CurrencyFormat`, `DateFormat` + parsers), `ynab/client.py` (`/budgets`→`/plans`, rename methods, add `get_plan`/`get_plan_settings`, `plan_id` params, `last-used` default), `ynab/tools.py` (rename tools, add two), `server.py` (registration), `README.md`, and the corresponding `tests/`.
- **Dependencies**: none new.
- **Behavioral/compat**: tool names change (`list_budgets` → `list_plans`; `budget_id` → `plan_id`). Users with the connector in Claude Desktop will see the renamed tools after upgrading.
- **Security**: unchanged (same bearer-token handling; ids are non-sensitive; token stays secret).
- **External constraints**: two more endpoints against YNAB's 200 req/hour limit; existing 429 mapping applies. `GET /plans/{id}` supports `last_knowledge_of_server` (delta) — **not** used here (deferred).
- **Out of scope**: write operations, OAuth, delta sync, payees/months/scheduled-transactions categories (separate future features).
