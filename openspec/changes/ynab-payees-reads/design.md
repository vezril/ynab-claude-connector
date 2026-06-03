## Context

The `ynab-integration` capability exposes 10 read-only YNAB tools via an async `httpx` client with typed models, pure parsers, a typed error taxonomy, and a stateless server factory (80 tests at 100% coverage; ruff/mypy strict across Python 3.11–3.13). Verified against the live OpenAPI spec, the **Payees** category has two GET endpoints (`getPayees`, `getPayeeById`) and two writes. The chosen scope is **read-only** (matching Feature 6 for Categories): add the two GETs, defer the writes.

Shapes (from the spec):
- `GET /plans/{plan_id}/payees` → `PayeesResponse` → `data.payees` (array of `Payee`) (+ `server_knowledge`).
- `GET /plans/{plan_id}/payees/{payee_id}` → `PayeeResponse` → `data.payee` (single `Payee`).
- `Payee` fields: `id`, `name`, `transfer_account_id` (nullable), `deleted` (bool).

## Goals / Non-Goals

**Goals:**
- `list_payees(plan_id="last-used")` and `get_payee(payee_id, plan_id="last-used")` MCP tools returning the typed `Payee`.
- Reuse the established FP/test patterns; hold the 90% coverage floor and ruff/mypy green; no new dependencies.

**Non-Goals:**
- No write endpoints (`createPayee`, `updatePayee`) — a future write-tools feature.
- No delta sync; no "Payee Locations" (a separate category); no change to existing tools.

## Decisions

### Decision 1: Add a `Payee` model with a shared `_payee_from` mapper; two parsers
**Choice**: Add `@dataclass(frozen=True, slots=True) Payee(id, name, transfer_account_id: str | None, deleted: bool)`. A private `_payee_from(item)` maps one payee; `parse_payees` reads `data["payees"]` (defensive: missing/empty → `()`), and `parse_payee` reads `data["payee"]` (required → raises on malformed).
**Why**: Mirrors the `Category`/`_category_from` pattern added in Feature 6 (list + single share one mapper). Consistency, immutability, full typing.
**Alternatives**: Omitting `transfer_account_id`/`deleted` — rejected; they're cheap, typed, and useful (transfer payees, soft-deleted payees).

### Decision 2: Tool signatures mirror the existing plan-scoped tools
**Choice**: `list_payees(plan_id: str = "last-used")`; `get_payee(payee_id: str, plan_id: str = "last-used")`.
**Why**: Identical shape/ergonomics to `list_categories`/`get_category`; `plan_id` last, defaulting to `last-used`.

### Decision 3: Errors and missing payees
**Choice**: A missing payee/plan yields a non-2xx (typically 404), already mapped by `error_from_response` to `YnabApiError`; tools let it propagate. `parse_payee` treats the `payee` object and its `id` as required.
**Why**: Consistent typed failures; no silent empties. Covered by tests (404 → `YnabApiError`; malformed payload raises; empty list → `()`).

## Risks / Trade-offs

- **Risk: optional/nullable fields** (`transfer_account_id`). → Mitigation: typed as `str | None` and read defensively (`.get`); unit-tested with present and absent values.
- **Trade-off: deferring writes** means the category isn't fully covered this round. → Accepted and explicit; keeps the connector read-only per the established scope.

## Migration Plan

1. TDD bottom-up: `parse_payees`/`parse_payee` (+ edge cases) → client `list_payees`/`get_payee` (MockTransport, assert paths + bearer) → tools → register in `build_server`.
2. Update the README tool list and the `ynab-integration` living spec (ADD one requirement).
- **Rollback**: additive; revert the change.

## Open Questions

- None blocking. The payee **write** endpoints and "Payee Locations" are deliberate separate features.
