## Why

Feature 12 (from the backlog) calls for implementing the YNAB **"Scheduled Transactions" category** — recurring/upcoming transactions and their schedules. The category has two reads and three writes; consistent with the connector's read-only posture (matching Features 6–11), this change implements the **read endpoints** and defers the writes. Scheduled transactions let Claude see what's coming up (recurring bills, transfers), completing read coverage of the YNAB API's transaction surface.

The category has two read endpoints: `getScheduledTransactions` (list) and `getScheduledTransactionById` (single).

## What Changes

- **Add `list_scheduled_transactions`** (`GET /plans/{plan_id}/scheduled_transactions`): the plan's scheduled transactions.
- **Add `get_scheduled_transaction`** (`GET /plans/{plan_id}/scheduled_transactions/{scheduled_transaction_id}`): a single scheduled transaction by id.
- Both accept a `plan_id` defaulting to the `last-used` alias.
- Add a `ScheduledTransaction` model (id, date_first, date_next, frequency, amount, account_id, payee_id, category_id, memo, deleted — amount in milliunits) and pure `parse_scheduled_transactions`/`parse_scheduled_transaction` parsers; add client methods and register the two tools.
- Extend tests (TDD) for the parsers, client methods, tools, and edge cases; update the README tool list.

## Capabilities

### New Capabilities
<!-- None — extends the existing ynab-integration capability. -->

### Modified Capabilities
- `ynab-integration`: Adds a new requirement for **read-only scheduled-transaction tools** (`list_scheduled_transactions`, `get_scheduled_transaction`). No existing requirements change.

## Impact

- **Changed files**: `ynab/models.py` (add `ScheduledTransaction` + parsers), `ynab/client.py` (add `list_scheduled_transactions`, `get_scheduled_transaction`), `ynab/tools.py` (add the two tools), `server.py` (register), `README.md`, and the corresponding `tests/`.
- **Dependencies**: none new.
- **Security**: unchanged — same bearer-token handling; reads only.
- **External constraints**: two more endpoints against YNAB's 200 req/hour limit; existing 429/404 mapping applies. The list endpoint supports `server_knowledge` (delta) — not used here.
- **Out of scope (explicit)**: the three **write** endpoints — `createScheduledTransaction`, `updateScheduledTransaction`, `deleteScheduledTransaction` — are deferred to a future write-tools feature. Also deferred: scheduled subtransactions detail, OAuth, delta sync.
