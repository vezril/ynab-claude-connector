## Context

The `ynab-integration` capability exposes 12 read-only YNAB tools via an async `httpx` client with typed models, pure parsers, a typed error taxonomy, and a stateless server factory (89 tests at 100% coverage; ruff/mypy strict across Python 3.11–3.13). Verified against the live OpenAPI spec, the **Payee Locations** category has three GET endpoints and no writes, so the whole category is implemented here.

Shapes (from the spec):
- `GET /plans/{plan_id}/payee_locations` → `PayeeLocationsResponse` → `data.payee_locations` (array).
- `GET /plans/{plan_id}/payee_locations/{payee_location_id}` → `PayeeLocationResponse` → `data.payee_location` (single).
- `GET /plans/{plan_id}/payees/{payee_id}/payee_locations` → `PayeeLocationsResponse` → `data.payee_locations` (array, scoped to a payee).
- `PayeeLocation` fields: `id`, `payee_id`, `latitude` (string, nullable), `longitude` (string, nullable), `deleted` (bool).

## Goals / Non-Goals

**Goals:**
- `list_payee_locations(plan_id="last-used")`, `get_payee_location(payee_location_id, plan_id="last-used")`, and `list_payee_locations_for_payee(payee_id, plan_id="last-used")` MCP tools returning the typed `PayeeLocation`.
- Reuse the established FP/test patterns; hold the 90% coverage floor and ruff/mypy green; no new dependencies.

**Non-Goals:**
- No writes (none exist for this category); no delta sync; no change to existing tools.

## Decisions

### Decision 1: `PayeeLocation` model + shared `_payee_location_from` mapper; two parsers
**Choice**: `@dataclass(frozen=True, slots=True) PayeeLocation(id, payee_id, latitude: str | None, longitude: str | None, deleted: bool)`. A private `_payee_location_from(item)` maps one record; `parse_payee_locations` reads `data["payee_locations"]` (defensive → `()`), `parse_payee_location` reads `data["payee_location"]` (required → raises). Both list endpoints share `parse_payee_locations`.
**Why**: Mirrors the `Payee`/`_payee_from` and `Category`/`_category_from` patterns. `latitude`/`longitude` are kept as the API's nullable strings (no float coercion — they are textual coordinates and may be absent).
**Alternatives**: Coercing lat/long to float — rejected; the API returns strings, they're nullable, and coercion invites precision/None bugs for no benefit here.

### Decision 2: Tool signatures mirror the existing plan-scoped tools
**Choice**: `list_payee_locations(plan_id="last-used")`; `get_payee_location(payee_location_id, plan_id="last-used")`; `list_payee_locations_for_payee(payee_id, plan_id="last-used")` (`payee_id` first, then `plan_id`).
**Why**: Identical ergonomics to the category/payee tools; `plan_id` last, defaulting to `last-used`.

### Decision 3: Errors and missing records
**Choice**: A missing location/plan yields a non-2xx (typically 404), already mapped to `YnabApiError`; tools let it propagate. `parse_payee_location` requires the `payee_location` object and its `id`.
**Why**: Consistent typed failures; no silent empties. Covered by tests (404 → `YnabApiError`; malformed → raises; empty list → `()`).

## Risks / Trade-offs

- **Risk: nullable `latitude`/`longitude`.** → Mitigation: typed `str | None`, read with `.get`; unit-tested with present and absent values.
- **Trade-off: lat/long as strings, not numbers.** → Accepted; matches the API and avoids lossy/None-prone coercion. A presentation layer can parse if needed.

## Migration Plan

1. TDD bottom-up: `parse_payee_locations`/`parse_payee_location` (+ edge cases) → client methods (MockTransport, assert paths + bearer) → tools → register in `build_server`.
2. Update the README tool list and the `ynab-integration` living spec (ADD one requirement).
- **Rollback**: additive; revert the change.

## Open Questions

- None. The category is fully covered (read-only, no writes exist).
