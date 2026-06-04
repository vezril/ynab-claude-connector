## Context

The `ynab-integration` capability exposes 17 read-only YNAB tools via an async `httpx` client with typed models, pure parsers, a typed error taxonomy, and a stateless server factory (105 tests at 100% coverage; ruff/mypy strict across Python 3.11–3.13). Verified against the live OpenAPI spec, the **Money Movements** category has four GET endpoints and no writes, so the whole category is implemented here.

Shapes (from the spec):
- `GET /plans/{plan_id}/money_movements` and `GET /plans/{plan_id}/months/{month}/money_movements` → `MoneyMovementsResponse` → `data.money_movements` (array of `MoneyMovement`).
- `GET /plans/{plan_id}/money_movement_groups` and `GET /plans/{plan_id}/months/{month}/money_movement_groups` → `MoneyMovementGroupsResponse` → `data.money_movement_groups` (array of `MoneyMovementGroup`).
- `MoneyMovementBase` fields (required: `id`, `amount`): `id`, `month`, `moved_at`, `note`, `money_movement_group_id`, `performed_by_user_id`, `from_category_id`, `to_category_id`, `amount` (milliunits).
- `MoneyMovementGroup` fields: `id`, `group_created_at`, `month`, `note`, `performed_by_user_id`.
- `month` accepts `current` or an ISO `YYYY-MM-01`.

## Goals / Non-Goals

**Goals:**
- Four MCP tools: `list_money_movements`, `list_money_movements_for_month`, `list_money_movement_groups`, `list_money_movement_groups_for_month`, returning typed data.
- Reuse the established FP/test patterns; hold the 90% coverage floor and ruff/mypy green; no new dependencies.

**Non-Goals:**
- No writes (none exist); no delta sync; no change to existing tools.

## Decisions

### Decision 1: Two models + shared mappers; one parser per resource (shared by plan-wide and per-month)
**Choice**: Add `MoneyMovement(id, month: str | None, moved_at: str | None, note: str | None, money_movement_group_id: str | None, performed_by_user_id: str | None, from_category_id: str | None, to_category_id: str | None, amount: int)` and `MoneyMovementGroup(id, group_created_at: str | None, month: str | None, note: str | None, performed_by_user_id: str | None)`, both frozen/slotted. Private `_money_movement_from`/`_money_movement_group_from` mappers; `parse_money_movements` reads `data["money_movements"]` and `parse_money_movement_groups` reads `data["money_movement_groups"]` (both defensive → `()`). The plan-wide and per-month endpoints return the same shape, so each resource needs only one parser.
**Why**: Mirrors the established model/parser/mapper pattern. `id`/`amount` are the only required movement fields; everything else is nullable. `amount` stays in milliunits.

### Decision 2: Tool signatures mirror the existing plan-scoped / month-scoped tools
**Choice**: `list_money_movements(plan_id="last-used")`; `list_money_movements_for_month(month, plan_id="last-used")`; `list_money_movement_groups(plan_id="last-used")`; `list_money_movement_groups_for_month(month, plan_id="last-used")` (`month` first, then `plan_id`).
**Why**: Identical ergonomics to the existing list/month tools; `plan_id` last, defaulting to `last-used`; `month` accepts `current`/ISO.

### Decision 3: Errors
**Choice**: A bad plan/month yields a non-2xx, already mapped to the typed errors (`YnabApiError`/etc.); tools let it propagate. These are list endpoints (no single-get), so empty results are `()`.
**Why**: Consistent typed failures. Covered by tests (404 → `YnabApiError`; empty list → `()`; missing optional fields → `None`).

## Risks / Trade-offs

- **Risk: many nullable fields on `MoneyMovement`.** → Mitigation: only `id`/`amount` required (per spec); the rest typed optional and read with `.get`; unit-tested with full and minimal payloads.
- **Trade-off: four similar list tools.** → Accepted; they map to four distinct documented endpoints and each is a thin wrapper.

## Migration Plan

1. TDD bottom-up: `parse_money_movements`/`parse_money_movement_groups` (+ edge cases) → client methods (MockTransport, assert all four paths + bearer) → tools → register in `build_server`.
2. Update the README tool list and the `ynab-integration` living spec (ADD one requirement).
- **Rollback**: additive; revert the change.

## Open Questions

- None. The category is fully covered (read-only, no writes exist).
