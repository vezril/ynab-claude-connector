## Context

The `ynab-integration` capability exposes 21 read-only YNAB tools via an async `httpx` client with typed models, pure parsers, a typed error taxonomy, and a stateless server factory (113 tests at 100% coverage; ruff/mypy strict across Python 3.11–3.13). Verified against the live OpenAPI spec, the **Transactions** category has six GET endpoints and five writes. The chosen scope is **read-only**: add the single-get and the four scoped lists, defer the writes.

Shapes (from the spec):
- `GET /plans/{plan_id}/transactions/{transaction_id}` → `TransactionResponse` → `data.transaction` (single).
- `GET /plans/{plan_id}/accounts/{account_id}/transactions` and `.../months/{month}/transactions` → `TransactionsResponse` → `data.transactions`.
- `GET /plans/{plan_id}/categories/{category_id}/transactions` and `.../payees/{payee_id}/transactions` → `HybridTransactionsResponse` → `data.transactions` (hybrid).
- `HybridTransaction` extends `TransactionSummary`, which **requires `account_id`** — so the hybrid responses carry the same core fields as a normal transaction; the existing `Transaction` model and `parse_transactions` cover them.

## Goals / Non-Goals

**Goals:**
- `get_transaction(transaction_id, plan_id="last-used")` and four scoped list tools (`by_account`, `by_category`, `by_payee`, `by_month`), returning typed `Transaction` data.
- Reuse the established FP/test patterns and the existing `Transaction` model; hold the 90% coverage floor and ruff/mypy green; no new dependencies.

**Non-Goals:**
- No write/mutating endpoints (create, update, bulk-update, delete, import) — a future write-tools feature.
- No `since_date`/`type` query filters and no `last_knowledge_of_server` delta — consistent with how prior features exposed endpoints by path without optional query niceties.

## Decisions

### Decision 1: Reuse `Transaction` + `parse_transactions`; add a single-object `parse_transaction`
**Choice**: Add a pure `parse_transaction(payload) -> Transaction` that reads `data["transaction"]`, reusing the existing `Transaction` dataclass. The four list endpoints (regular and hybrid) reuse `parse_transactions` (which reads `data["transactions"]`).
**Why**: All five endpoints return the same `Transaction` shape (hybrid included, since it extends `TransactionSummary` with `account_id` required). One new parser (single) plus the existing list parser cover the whole read surface — consistent with the `Category`/`parse_category` pattern from Feature 6.
**Alternatives**: A distinct `HybridTransaction` model exposing `type`/`parent_transaction_id` — rejected; those extra fields aren't needed for read insights and a separate type adds complexity for no benefit here.

### Decision 2: Tool signatures mirror the existing scoped tools
**Choice**: `get_transaction(transaction_id, plan_id="last-used")`; `list_transactions_by_account(account_id, plan_id="last-used")`; `list_transactions_by_category(category_id, ...)`; `list_transactions_by_payee(payee_id, ...)`; `list_transactions_by_month(month, plan_id="last-used")` (`month` accepts `current`/ISO).
**Why**: Identical ergonomics to `get_category`/`get_month_category`/`list_*`; the scoping id is first, `plan_id` last.

### Decision 3: Errors
**Choice**: A missing transaction/plan yields a non-2xx (typically 404), already mapped to `YnabApiError`; tools let it propagate. `parse_transaction` requires the `transaction` object and its `id`.
**Why**: Consistent typed failures; no silent empties. Covered by tests (404 → `YnabApiError`; malformed → raises; empty list → `()`).

## Risks / Trade-offs

- **Risk: hybrid responses lack a normal field.** → Mitigation: confirmed against the spec that `HybridTransaction` extends `TransactionSummary` (which requires `account_id`); reusing `parse_transactions` is safe. Covered by a by-category test using a hybrid-style payload.
- **Trade-off: deferring writes and query filters** means "all endpoints" isn't fully covered this round. → Accepted and explicit; keeps the connector read-only and consistent with prior features.

## Migration Plan

1. TDD bottom-up: `parse_transaction` (+ malformed edge case) → client methods (MockTransport, assert all five paths + bearer) → tools → register in `build_server`.
2. Update the README tool list and the `ynab-integration` living spec (ADD one requirement).
- **Rollback**: additive; revert the change.

## Open Questions

- None blocking. Transaction **writes** and the `since_date`/`type`/delta query options are deliberate separate features.
