## Context

The `ynab-integration` capability exposes read-only YNAB tools via an async `httpx` client with typed models, pure parsers, a typed error taxonomy, and a stateless server factory (currently 8 tools; 72 tests at 100% coverage; ruff/mypy strict across Python 3.11–3.13). Verified against the live OpenAPI spec, the **Categories** category has three GET endpoints (`getCategories`, `getCategoryById`, `getMonthCategoryById`) and five writes. We already expose `getCategories` as `list_categories`. The chosen scope is **read-only**: add the two single-category GETs and defer all writes.

Both GET-single endpoints return `CategoryResponse` → `data.category` (a single `Category`). Paths:
- `GET /plans/{plan_id}/categories/{category_id}`
- `GET /plans/{plan_id}/months/{month}/categories/{category_id}` (`month` accepts `current` or an ISO `YYYY-MM-01`).

## Goals / Non-Goals

**Goals:**
- `get_category(category_id, plan_id="last-used")` and `get_month_category(month, category_id, plan_id="last-used")` MCP tools returning the typed `Category`.
- Reuse the existing `Category` model and FP/test patterns; hold the 90% coverage floor and ruff/mypy green; no new dependencies.

**Non-Goals:**
- No write/mutating endpoints (createCategory, updateCategory, updateMonthCategory, create/updateCategoryGroup) — a separate future feature.
- No delta sync; no change to existing tools.

## Decisions

### Decision 1: Reuse the `Category` model; add a single-object `parse_category`
**Choice**: Add a pure `parse_category(payload) -> Category` that reads `data["category"]`, reusing the existing `Category` dataclass (id, name, category_group_id, budgeted, activity, balance). Both new client methods delegate to it.
**Why**: Both endpoints return the same `Category` shape as the list endpoint's items, so a single parser covers both. Consistency with the established parser/model pattern; the month-specific values (budgeted/activity/balance for that month) populate the same fields.
**Alternatives**: A distinct `MonthCategory` model — rejected; the payload shape is identical and a separate type adds nothing.

### Decision 2: Tool signatures and the `month` argument
**Choice**: `get_category(category_id: str, plan_id: str = "last-used")`; `get_month_category(month: str, category_id: str, plan_id: str = "last-used")`. `month` is a required string documented to accept `current` or an ISO date.
**Why**: Mirrors the existing plan-scoped tools (`plan_id` last). `month` has no sensible default beyond `current`, but making it explicit avoids surprising the caller; the docstring notes the `current` alias.
**Alternatives**: Default `month="current"` — convenient but hides an important parameter; left explicit (caller can pass `"current"`).

### Decision 3: Errors and missing categories
**Choice**: A missing category/plan yields a non-2xx (typically 404), already mapped by the existing `error_from_response` to `YnabApiError`; the tools let it propagate. `parse_category` treats the `category` object and its `id` as required so a malformed body raises rather than returning an empty model.
**Why**: Consistent, typed failures; no silent empties. Covered by tests (404 → `YnabApiError`; malformed payload raises).

## Risks / Trade-offs

- **Risk: month value formats** (`current` vs ISO). → Mitigation: pass the caller's value straight through (the API validates it); document the accepted forms; a test asserts the path is built verbatim.
- **Risk: assuming the single-category payload matches the list-item shape.** → Mitigation: shape taken from the spec (`CategoryResponse.data.category` is a `Category`); parser is defensive on optional fields and unit-tested.
- **Trade-off: deferring writes** means "all endpoints" isn't fully covered this round. → Accepted and explicit; keeps the connector read-only per the chosen scope.

## Migration Plan

1. TDD bottom-up: `parse_category` (+ malformed edge case) → client `get_category`/`get_month_category` (MockTransport, assert paths + bearer) → tools → register in `build_server`.
2. Update the README tool list and the `ynab-integration` living spec (ADD one requirement).
- **Rollback**: additive; revert the change.

## Open Questions

- None blocking. The category **write** endpoints are a deliberate separate feature.
