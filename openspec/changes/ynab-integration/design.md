## Context

The connector (Feature 2) is a FastMCP server with a stateless `build_server` factory, env-based immutable `ServerConfig`, and a `ping` tool — all under a 90% coverage gate with ruff/mypy(strict) across Python 3.11–3.13. Feature 3 adds the first real capability: authenticated, read-only access to the YNAB API surfaced as MCP tools. The user chose a **Personal Access Token** (single user, their own account) and all four read tools (**budgets, accounts, categories, transactions**).

YNAB API essentials: base `https://api.ynab.com/v1`; bearer auth (`Authorization: Bearer <token>`); responses wrapped in a `data` envelope (`{"data": {"budgets": [...]}}`); errors as `{"error": {"id","name","detail"}}` with a non-2xx status; **200 requests/hour per token** (HTTP 429 on exceed). Budget-scoped paths accept the literal `default` as a budget-id alias for the last-used budget. (The API serves these under `/budgets/...`; "plans" is newer UI terminology only.)

## Goals / Non-Goals

**Goals:**
- An async YNAB client that authenticates, calls the four GET endpoints, unwraps the envelope, returns typed models, and maps errors to clear exceptions.
- Four MCP tools: `list_budgets`, `list_accounts`, `list_categories`, `list_transactions`.
- Token loaded from the environment, never logged or reprised; missing token yields a clear, actionable error only when a YNAB tool is used (server still starts).
- TDD with no live network: pure parsers + error mapping unit-tested; client/tools tested via httpx `MockTransport`. Hold the 90% gate and ruff/mypy green.

**Non-Goals:**
- OAuth / refresh tokens (PAT only now); any write/mutating operations.
- Delta sync (`server_knowledge`/`last_knowledge_of_server`) — future optimization.
- Client-side rate-limit throttling/retry/backoff (surface 429 clearly; revisit later).
- Caching, pagination helpers, or exhaustive field coverage (expose a useful subset).

## Decisions

### Decision 1: `httpx` async client; tools are async
**Choice**: Add `httpx` and make the YNAB client and the four tools **async**. FastMCP supports async tool functions and runs them on its event loop.
**Why over `requests`**: YNAB calls are network I/O; blocking calls would stall the server's event loop (and, under Streamable HTTP, other requests). `httpx` is the modern async client and ships a built-in `MockTransport`, letting us test the full request/response path with zero live network and **no extra test dependency**.
**Alternatives**: `requests` (sync; would need thread offloading to avoid blocking — more complexity); `aiohttp` (heavier, less ergonomic typing).

### Decision 2: Functional core / imperative shell — separate parsing from I/O
**Choice**: Split each endpoint into (a) a **pure parser** `parse_budgets(payload: Mapping) -> tuple[Budget, ...]` (and friends) that maps the JSON envelope to frozen-dataclass models, and (b) a thin **async I/O method** on the client that performs the GET and delegates to the parser. Error mapping is a pure function `error_from_response(status, body) -> YnabError`.
**Why**: The pure parsers and error mapper are exhaustively unit-testable from sample payloads (the bulk of behavior and coverage) without any transport; only the thin I/O methods need `MockTransport`. Matches the project's FP preference.

### Decision 3: Typed models as frozen dataclasses (curated field subset)
**Choice**: `Budget`, `Account`, `Category`, `Transaction` as `@dataclass(frozen=True, slots=True)` with type hints, exposing a useful subset (e.g. ids/names; account `type`/`balance`; category `budgeted`/`activity`/`balance`; transaction `date`/`amount`/`payee_name`/`category_id`/`memo`/`cleared`). Monetary amounts stay in YNAB **milliunits** (integers) with the field named to make that explicit (e.g. `balance_milliunits`).
**Why**: Immutable, type-checked records make illegal states harder and serialize cleanly to MCP structured content. Keeping milliunits avoids lossy/ambiguous currency conversion in the client; presentation/conversion can be layered later.
**Alternatives**: Pydantic models (adds a dependency; dataclasses suffice for read-only mapping). Converting to decimal currency now (premature; loses fidelity, invites rounding bugs).

### Decision 4: Credentials in config, treated as a secret, validated lazily
**Choice**: Extend configuration with `ynab_token: str | None` (from `YNAB_TOKEN`) and `ynab_api_base_url` (from `YNAB_API_BASE_URL`, default `https://api.ynab.com/v1`). The token field is declared `field(repr=False)` so it never appears in logs/reprs. The server **starts without a token** (ping works); building the YNAB client requires it and raises `YnabAuthError` with a clear "set YNAB_TOKEN" message if absent.
**Why**: Secrets belong in the environment, not code, and must not leak into logs (secure-coding). Lazy validation keeps the connector runnable for non-YNAB use and surfaces the misconfiguration precisely when a YNAB tool is called.
**Alternatives**: Fail server startup when the token is missing (rejected — couples the whole server to YNAB and breaks `ping`-only use). A dedicated `SecretStr` wrapper (overkill; `repr=False` + discipline is enough here).

### Decision 5: Error taxonomy mapped from HTTP status
**Choice**: A small exception hierarchy in `ynab/errors.py`: `YnabError` (base) → `YnabAuthError` (401/403 or missing token), `YnabRateLimitError` (429), `YnabApiError` (other non-2xx, carrying status + YNAB error `name`/`detail`). The client calls the pure `error_from_response` mapper and raises; tool functions let these propagate so MCP returns a meaningful tool error.
**Why**: Distinct, typed failures give Claude/users actionable messages (bad token vs rate limited vs server error). Keeping the mapper pure makes every branch unit-testable without a server.

### Decision 6: Budget scoping via the `default` alias; tool signatures
**Choice**: `list_budgets()` takes no args. `list_accounts`, `list_categories`, `list_transactions` take `budget_id: str = "default"`, passing YNAB's `default` alias when unspecified so the user need not know their budget id. Tools build the client from environment config at call time via a single indirection (`client_from_env`) that tests can substitute.
**Why**: Lowers friction (most users have one budget). The single client-construction seam keeps tools thin and lets tests inject a `MockTransport`-backed client.

### Decision 7: Testing via `httpx.MockTransport` + `asyncio.run`
**Choice**: Drive client/tool tests with an `httpx.MockTransport` handler that asserts the request (path, `Authorization` header) and returns canned JSON; await coroutines with `asyncio.run` (consistent with Feature 2 — no `pytest-asyncio`). Pure parsers/error-mapper are tested directly (sync).
**Why**: Deterministic, fast, no network, no new dependency; verifies auth header and URL construction end-to-end while keeping the heavy logic in sync unit tests.

## Risks / Trade-offs

- **Risk: leaking the token in logs/errors.** → Mitigation: `repr=False` on the token field; never include the token in exception messages; tests assert the token isn't in `repr(config)`.
- **Risk: YNAB rate limit (200/hr) hit during use.** → Mitigation: map 429 to `YnabRateLimitError` with a clear message; document the limit; throttling/backoff deferred. A test covers the 429 mapping.
- **Risk: model drift / unexpected/missing fields in API payloads.** → Mitigation: parsers read known keys defensively (treat optional fields as `None`, default missing lists to empty) and are unit-tested with both full and minimal payloads; we map only a curated subset.
- **Risk: blocking the event loop.** → Mitigation: fully async client/tools (Decision 1).
- **Risk: `httpx.AsyncClient` lifecycle leaks (unclosed connections).** → Mitigation: open the client within an `async with` per tool call (simple, correct) for the MVP; a shared pooled client can be introduced later if call volume warrants.
- **Trade-off: milliunits, not currency.** → Accepted; lossless and explicit, with conversion deferred to a presentation layer.
- **Trade-off: per-call client construction** adds minor overhead. → Accepted for MVP simplicity given the 200/hr ceiling.

## Migration Plan

1. Add `httpx`; reinstall dev env.
2. TDD bottom-up: models + pure parsers → error mapper → async client (MockTransport) → tools (MockTransport) → register in `build_server`.
3. Extend `ServerConfig` with token (secret) + base URL; wire `client_from_env`.
4. Update README (YNAB token setup, the four tools, rate-limit note). Smoke-test `list_budgets` against a `MockTransport` (and optionally a real token locally, not in CI).
- **Rollback**: additive; revert the change. No persisted state.

## Open Questions

- None blocking. Future: delta sync, OAuth, write tools, currency formatting, and a shared pooled HTTP client are explicit non-goals here and can each be their own change.
