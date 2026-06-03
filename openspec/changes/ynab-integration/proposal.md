## Why

The connector runs but exposes only a `ping` tool — it does nothing useful yet. Feature 3 delivers the actual purpose: let Claude read the user's YNAB budget data. This adds authenticated, read-only access to the [YNAB API](https://api.ynab.com/v1) and surfaces it as MCP tools, so the user can ask Claude about their budgets, accounts, categories, and transactions.

## What Changes

- Add a runtime dependency on **`httpx`** (async HTTP client).
- Add a **YNAB API client** (`ynab/` subpackage): an async client over `https://api.ynab.com/v1` that injects the `Authorization: Bearer <token>` header, unwraps the `data` envelope, maps typed responses, and translates API errors (401 → auth, 429 → rate limit, others → API error).
- Add **typed models** (frozen dataclasses) for the subset of Budget, Account, Category, and Transaction fields we expose.
- Add **four read-only MCP tools**: `list_budgets`, `list_accounts`, `list_categories`, `list_transactions`. Budget-scoped tools accept a `budget_id` defaulting to YNAB's `default` alias (last-used budget) so the user need not know their budget id.
- Add **credential configuration**: a YNAB Personal Access Token read from the environment (kept out of logs/reprs) and a configurable API base URL. The server still starts without a token; YNAB tools fail with a clear error if the token is missing.
- Extend tests (TDD) with pure response-parsing tests, error-mapping tests, and client/tool tests driven by an in-memory HTTP transport (no live network). Update the README with YNAB setup and the new tools.

## Capabilities

### New Capabilities
- `ynab-integration`: Authenticated read-only access to the YNAB API — the async client, credential configuration, typed models, error mapping, and the four budget/account/category/transaction MCP tools.

### Modified Capabilities
<!-- None. connector-runtime is unchanged: the ping tool and the server/config/entry-point requirements still hold; YNAB tools are additive and registered through the same factory. -->

## Impact

- **New files**: `src/ynab_claude_connector/ynab/{__init__,client,models,errors,tools}.py`; corresponding `tests/`.
- **Changed files**: `config.py` (add YNAB token + base URL), `server.py` (register the four tools), `pyproject.toml` (add `httpx`), `README.md`.
- **Dependencies**: add runtime dep `httpx`. Dev deps unchanged (tests use httpx's built-in `MockTransport` — no new test dependency).
- **Secrets**: the YNAB token is a secret — it is read from the environment, never logged, and excluded from dataclass reprs.
- **External constraints**: YNAB rate limit is **200 requests/hour per token** (429 on exceed) — surfaced as a clear error; no client-side throttling in this MVP.
- **Out of scope**: OAuth/refresh tokens, write/mutating operations, and delta sync (`server_knowledge`/`last_knowledge_of_server`) — deferred to later features.
