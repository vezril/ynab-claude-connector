## Why

Feature 11 (from the backlog) calls for implementing the YNAB **"Transactions" category** — the largest category, with both reads and writes. Consistent with the connector's read-only posture (matching Features 6–10), this change implements the **read endpoints** and explicitly defers the writes to a future write-tools feature. We already expose the plan-wide list (`getTransactions` as `list_transactions`); this adds the single-transaction lookup and the four scoped transaction lists (by account, category, payee, month), completing read coverage.

## What Changes

- **Add `get_transaction`** (`GET /plans/{plan_id}/transactions/{transaction_id}`): a single transaction by id.
- **Add `list_transactions_by_account`** (`GET /plans/{plan_id}/accounts/{account_id}/transactions`).
- **Add `list_transactions_by_category`** (`GET /plans/{plan_id}/categories/{category_id}/transactions`).
- **Add `list_transactions_by_payee`** (`GET /plans/{plan_id}/payees/{payee_id}/transactions`).
- **Add `list_transactions_by_month`** (`GET /plans/{plan_id}/months/{month}/transactions`; `month` accepts `current` or ISO `YYYY-MM-01`).
- All accept a `plan_id` defaulting to the `last-used` alias.
- Add a pure `parse_transaction` parser (reads the `data.transaction` envelope) reusing the existing `Transaction` model; the four list endpoints reuse `parse_transactions`. Add client methods and register the five tools.
- Extend tests (TDD) for the parser, client methods, tools, and edge cases; update the README tool list.

## Capabilities

### New Capabilities
<!-- None — extends the existing ynab-integration capability. -->

### Modified Capabilities
- `ynab-integration`: Adds a new requirement for **read-only transaction lookup tools** (`get_transaction` and the four scoped list tools). No existing requirements change.

## Impact

- **Changed files**: `ynab/models.py` (add `parse_transaction`), `ynab/client.py` (add five methods), `ynab/tools.py` (add five tools), `server.py` (register), `README.md`, and the corresponding `tests/`.
- **Dependencies**: none new.
- **Security**: unchanged — same bearer-token handling; reads only.
- **External constraints**: five more endpoints against YNAB's 200 req/hour limit; existing 429/404 mapping applies. The by-category and by-payee endpoints return "hybrid" transactions (which still carry `account_id`), so the existing `Transaction` model and parser cover them.
- **Out of scope (explicit)**: the five **write** endpoints — `createTransaction`, `updateTransaction`, `updateTransactions` (bulk), `deleteTransaction`, `importTransactions` — are deferred to a future write-tools feature. Also deferred (consistent with prior features): the optional `since_date`/`type` query filters and `last_knowledge_of_server` delta; OAuth.
