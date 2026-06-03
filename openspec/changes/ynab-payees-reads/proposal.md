## Why

Feature 7 (from the backlog) calls for implementing the YNAB **"Payees" category**. That category has four endpoints — two reads (`getPayees`, `getPayeeById`) and two writes (`createPayee`, `updatePayee`). Consistent with the connector's read-only posture (and matching the Feature 6 decision for Categories), this change implements the **read endpoints** and defers the writes. Payees let Claude see who transactions are with, complementing the existing transaction/category tools for budget insights.

## What Changes

- **Add `list_payees`** (`GET /plans/{plan_id}/payees`): returns the plan's payees (id, name, transfer account id, deleted flag).
- **Add `get_payee`** (`GET /plans/{plan_id}/payees/{payee_id}`): returns a single payee by id.
- Both accept a `plan_id` defaulting to the `last-used` alias, consistent with the other plan-scoped tools.
- Add a `Payee` model and pure `parse_payees`/`parse_payee` parsers; add client methods and register the two tools.
- Extend tests (TDD) for the parsers, client methods, tools, and edge cases; update the README tool list.

## Capabilities

### New Capabilities
<!-- None — extends the existing ynab-integration capability. -->

### Modified Capabilities
- `ynab-integration`: Adds a new requirement for **read-only payee tools** (`list_payees`, `get_payee`). No existing requirements change.

## Impact

- **Changed files**: `ynab/models.py` (add `Payee` + `parse_payees`/`parse_payee`), `ynab/client.py` (add `list_payees`, `get_payee`), `ynab/tools.py` (add the two tools), `server.py` (register), `README.md`, and the corresponding `tests/`.
- **Dependencies**: none new.
- **Security**: unchanged — same bearer-token handling; reads only.
- **External constraints**: two more endpoints against YNAB's 200 req/hour limit; existing 429 mapping applies. A 404 for a missing payee surfaces as the typed API error. `getPayees` supports `last_knowledge_of_server` (delta) — not used here.
- **Out of scope (explicit)**: the two **write** endpoints — `createPayee`, `updatePayee` — are deferred to a future write-tools feature (keeps the connector read-only). Also out of scope: OAuth, delta sync, and the separate "Payee Locations" category.
