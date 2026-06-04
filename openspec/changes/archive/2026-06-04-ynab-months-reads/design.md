## Context

The `ynab-integration` capability exposes 15 read-only YNAB tools via an async `httpx` client with typed models, pure parsers, a typed error taxonomy, and a stateless server factory (97 tests at 100% coverage; ruff/mypy strict across Python 3.11–3.13). Verified against the live OpenAPI spec, the **Months** category has two GET endpoints and no writes, so the whole category is implemented here.

Shapes (from the spec):
- `GET /plans/{plan_id}/months` → `MonthSummariesResponse` → `data.months` (array of `MonthSummary`).
- `GET /plans/{plan_id}/months/{month}` → `MonthDetailResponse` → `data.month` (a `MonthDetail` = `MonthSummary` + a `categories` array). `month` accepts `current` or an ISO `YYYY-MM-01`.
- `MonthSummaryBase` fields: `month` (ISO date id), `note` (nullable), `income`, `budgeted`, `activity`, `to_be_budgeted` (milliunits), `age_of_money` (nullable int), `deleted` (bool).

## Goals / Non-Goals

**Goals:**
- `list_months(plan_id="last-used")` and `get_month(month, plan_id="last-used")` MCP tools returning typed `Month` data.
- Reuse the established FP/test patterns; hold the 90% coverage floor and ruff/mypy green; no new dependencies.

**Non-Goals:**
- No writes (none exist); no delta sync; no change to existing tools.
- `get_month` does NOT return the embedded per-month `categories` array (see Decision 2).

## Decisions

### Decision 1: One `Month` model (summary fields) + shared `_month_from`; two parsers
**Choice**: `@dataclass(frozen=True, slots=True) Month(month, note: str | None, income: int, budgeted: int, activity: int, to_be_budgeted: int, age_of_money: int | None, deleted: bool)`. A private `_month_from(item)` maps one record; `parse_months` reads `data["months"]` (defensive → `()`), `parse_month` reads `data["month"]` (required → raises). Amounts stay in milliunits.
**Why**: Mirrors the `Payee`/`Category` patterns. Both list and single endpoints share the same summary shape, so one model + mapper covers both.

### Decision 2: `get_month` returns the month summary, not the embedded categories
**Choice**: `MonthDetail` includes a `categories` array (per-category budgeted/activity/balance for that month). `get_month` maps only the `Month` summary fields and ignores that array.
**Why**: Per-category month figures are already reachable via `get_month_category(month, category_id)` (Feature 6) and the category list tools; embedding ~50–100 categories in every `get_month` result would bloat tool output for little marginal value. Consistent with the `get_plan` curated-summary philosophy.
**Alternatives**: Returning the full categories list — heavier output, redundant with existing tools; rejected. Adding a `categories_count` — minor; omitted for a clean single `Month` shape shared by both tools (can be added later if useful).

### Decision 3: Errors and missing months
**Choice**: A missing month/plan yields a non-2xx (typically 404), already mapped to `YnabApiError`; tools let it propagate. `parse_month` requires the `month` object and its `month` id field.
**Why**: Consistent typed failures; no silent empties. Covered by tests (404 → `YnabApiError`; malformed → raises; empty list → `()`).

## Risks / Trade-offs

- **Risk: nullable `note`/`age_of_money`.** → Mitigation: typed as optional, read with `.get`; unit-tested with present and absent values.
- **Trade-off: dropping the embedded month categories from `get_month`.** → Accepted; available via `get_month_category`; documented in the proposal and README.

## Migration Plan

1. TDD bottom-up: `parse_months`/`parse_month` (+ edge cases) → client `list_months`/`get_month` (MockTransport, assert paths + bearer) → tools → register in `build_server`.
2. Update the README tool list and the `ynab-integration` living spec (ADD one requirement).
- **Rollback**: additive; revert the change.

## Open Questions

- None. The category is fully covered (read-only, no writes exist).
