## Context

The `ynab-integration` capability exposes 26 read-only YNAB tools via an async `httpx` client with typed models, pure parsers, a typed error taxonomy, and a stateless server factory (120 tests at 100% coverage; ruff/mypy strict across Python 3.11–3.13). Verified against the live OpenAPI spec, the **Scheduled Transactions** category has two GET endpoints and three writes. The chosen scope is **read-only**: add the list and single-get, defer the writes.

Shapes (from the spec):
- `GET /plans/{plan_id}/scheduled_transactions` → `ScheduledTransactionsResponse` → `data.scheduled_transactions` (array).
- `GET /plans/{plan_id}/scheduled_transactions/{scheduled_transaction_id}` → `ScheduledTransactionResponse` → `data.scheduled_transaction` (single).
- `ScheduledTransactionSummary` (required: `id`, `account_id`, `amount`, `date_first`, `date_next`, `frequency`, `deleted`): `id`, `date_first`, `date_next`, `frequency`, `amount` (milliunits), `memo`, `account_id`, `payee_id`, `category_id`, `transfer_account_id`, `deleted`, …

## Goals / Non-Goals

**Goals:**
- `list_scheduled_transactions(plan_id="last-used")` and `get_scheduled_transaction(scheduled_transaction_id, plan_id="last-used")` MCP tools returning typed `ScheduledTransaction` data.
- Reuse the established FP/test patterns; hold the 90% coverage floor and ruff/mypy green; no new dependencies.

**Non-Goals:**
- No write endpoints (create, update, delete) — a future write-tools feature.
- No scheduled-subtransaction breakdown; no delta sync; no change to existing tools.

## Decisions

### Decision 1: A curated `ScheduledTransaction` model + shared mapper; two parsers
**Choice**: `@dataclass(frozen=True, slots=True) ScheduledTransaction(id, date_first: str, date_next: str, frequency: str, amount: int, account_id: str, payee_id: str | None, category_id: str | None, memo: str | None, deleted: bool)`. A private `_scheduled_transaction_from(item)` maps one record; `parse_scheduled_transactions` reads `data["scheduled_transactions"]` (defensive → `()`), `parse_scheduled_transaction` reads `data["scheduled_transaction"]` (required → raises).
**Why**: Mirrors the established model/parser/mapper pattern. Exposes the useful subset (schedule dates, frequency, amount, and the linking ids); required fields (`id`, `account_id`, `amount`, `date_first`, `date_next`, `frequency`) come straight from the spec; `payee_id`/`category_id`/`memo` are optional. Amount stays in milliunits.
**Alternatives**: Exposing every field (flag_color/name, transfer ids, scheduled subtransactions) — rejected as noise for read insights; the curated set mirrors how `Transaction` was scoped.

### Decision 2: Tool signatures mirror the existing list/get tools
**Choice**: `list_scheduled_transactions(plan_id="last-used")`; `get_scheduled_transaction(scheduled_transaction_id, plan_id="last-used")`.
**Why**: Identical ergonomics to `list_payees`/`get_payee` etc.; the scoping id first, `plan_id` last.

### Decision 3: Errors
**Choice**: A missing scheduled transaction/plan yields a non-2xx (typically 404), already mapped to `YnabApiError`; tools let it propagate. `parse_scheduled_transaction` requires the `scheduled_transaction` object and its `id`.
**Why**: Consistent typed failures; no silent empties. Covered by tests (404 → `YnabApiError`; malformed → raises; empty list → `()`).

## Risks / Trade-offs

- **Risk: optional fields** (`payee_id`/`category_id`/`memo`). → Mitigation: typed optional, read with `.get`; unit-tested with full and minimal payloads.
- **Trade-off: deferring writes** means the category isn't fully covered this round. → Accepted and explicit; keeps the connector read-only per the established scope.

## Migration Plan

1. TDD bottom-up: `parse_scheduled_transactions`/`parse_scheduled_transaction` (+ edge cases) → client methods (MockTransport, assert paths + bearer) → tools → register in `build_server`.
2. Update the README tool list and the `ynab-integration` living spec (ADD one requirement).
- **Rollback**: additive; revert the change.

## Open Questions

- None blocking. Scheduled-transaction **writes** and subtransaction detail are deliberate separate features.
