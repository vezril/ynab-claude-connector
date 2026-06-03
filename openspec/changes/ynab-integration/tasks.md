## 1. Dependency & Config Setup

- [ ] 1.1 Add runtime dependency `httpx` to `[project].dependencies` in `pyproject.toml` (pinned minimum); reinstall `pip install -e ".[dev]"` and confirm `import httpx`
- [ ] 1.2 Create the `src/ynab_claude_connector/ynab/` subpackage with `__init__.py`
- [ ] 1.3 RED: extend `tests/test_config.py` — `from_env({})` yields `ynab_token is None` and `ynab_api_base_url == "https://api.ynab.com/v1"`; an env with `YNAB_TOKEN`/`YNAB_API_BASE_URL` is reflected; `repr(config)` does NOT contain the token; run `pytest`, confirm FAILS
- [ ] 1.4 GREEN: extend `ServerConfig`/`from_env` with `ynab_token: str | None` (field `repr=False`) and `ynab_api_base_url: str`; run `pytest`, confirm PASS

## 2. Typed Models & Pure Parsers — TDD

- [ ] 2.1 RED: write `tests/test_ynab_models.py` asserting `parse_budgets`, `parse_accounts`, `parse_categories`, `parse_transactions` map a sample `data`-envelope payload to frozen dataclasses (ids/names; account `balance` in milliunits; category budgeted/activity/balance; transaction date/amount/payee/memo); run `pytest`, confirm FAILS
- [ ] 2.2 GREEN: implement `ynab/models.py` (frozen, slotted dataclasses) and the pure `parse_*` functions (read known keys, type-hinted); run `pytest`, confirm PASS
- [ ] 2.3 RED: add edge-case parser tests — empty resource lists yield empty tuples; items missing optional fields parse with those fields `None` (no raise); run `pytest`, confirm FAILS
- [ ] 2.4 GREEN: make parsers defensive for optional/missing fields; run `pytest`, confirm PASS

## 3. Error Taxonomy — TDD

- [ ] 3.1 RED: write `tests/test_ynab_errors.py` asserting `error_from_response(status, body)` returns `YnabAuthError` for 401/403, `YnabRateLimitError` for 429, and `YnabApiError` (carrying status + YNAB `name`/`detail`) for other non-2xx; all subclass `YnabError`; run `pytest`, confirm FAILS
- [ ] 3.2 GREEN: implement `ynab/errors.py` (exception hierarchy) and the pure `error_from_response` mapper; ensure messages never include the token; run `pytest`, confirm PASS

## 4. Async Client — TDD (httpx MockTransport)

- [ ] 4.1 RED: write `tests/test_ynab_client.py` using `httpx.MockTransport` — a `YnabClient` built around an injected `httpx.AsyncClient` calls `GET /budgets` and returns parsed budgets; the captured request carries `Authorization: Bearer <token>` and the configured base URL (drive with `asyncio.run`); run `pytest`, confirm FAILS
- [ ] 4.2 GREEN: implement `ynab/client.py` — `YnabClient` with async methods (`list_budgets`, `list_accounts`, `list_categories`, `list_transactions`) that GET the right path, unwrap the envelope via the parsers, and a `client_from_env(config)` factory building an `httpx.AsyncClient` (base URL + bearer header); raise `YnabAuthError` if the token is missing; run `pytest`, confirm PASS
- [ ] 4.3 RED: add client error tests — a `MockTransport` returning 401 → `YnabAuthError`, 429 → `YnabRateLimitError`, 500 → `YnabApiError`; run `pytest`, confirm FAILS
- [ ] 4.4 GREEN: wire the client to call `error_from_response` and raise on non-2xx; ensure the `httpx.AsyncClient` is properly closed (`async with`); run `pytest`, confirm PASS
- [ ] 4.5 RED/GREEN: add a test that budget-scoped methods default to the `default` alias path (e.g. `GET /budgets/default/accounts`) when no `budget_id` is given; implement; run `pytest`

## 5. MCP Tools — TDD

- [ ] 5.1 RED: write `tests/test_ynab_tools.py` — `list_budgets` (no args) and `list_accounts`/`list_categories`/`list_transactions` (`budget_id: str = "default"`) return parsed data; inject a `MockTransport`-backed client by monkeypatching `client_from_env`; run `pytest`, confirm FAILS
- [ ] 5.2 GREEN: implement the four async tools in `ynab/tools.py` (thin: build client via `client_from_env`, call, return typed models); full type hints; run `pytest`, confirm PASS
- [ ] 5.3 RED: add a test that invoking a YNAB tool with no token raises `YnabAuthError` before any network call; GREEN by confirming the token check happens in `client_from_env`; run `pytest`
- [ ] 5.4 GREEN: register the four tools in `build_server` (`server.py`) alongside `ping`; update `tests/test_server.py` to assert all five tool names are listed and their input schemas are typed; run `pytest`

## 6. Refactor & Quality Gate

- [ ] 6.1 REFACTOR: confirm FP boundaries (pure parsers/error-mapper; I/O only in client methods); confine all `httpx` usage to `ynab/client.py`; ensure the token never appears in logs/messages
- [ ] 6.2 Run the full local gate: `ruff check`, `ruff format --check`, `mypy` (strict, incl. new modules), and `pytest` with `--cov-fail-under=90` — all green
- [ ] 6.3 Add a mypy override for `httpx` only if it lacks type info (it ships types — prefer none)

## 7. Documentation & Smoke Test

- [ ] 7.1 Update `README.md`: how to create a YNAB Personal Access Token, the `YNAB_TOKEN`/`YNAB_API_BASE_URL` env vars, the four tools and their args, and the 200 requests/hour rate-limit note
- [ ] 7.2 Smoke-test `list_budgets` via a `MockTransport` (and optionally a real token locally — never commit a token); confirm `python -m ynab_claude_connector` still starts
- [ ] 7.3 Confirm `python -m build` still produces sdist + wheel with `httpx` declared as a runtime dependency

## 8. Final Verification

- [ ] 8.1 Run the full local gate once more (`pre-commit run --all-files`, `actionlint`, `pytest`) — all green
- [ ] 8.2 Commit on a feature branch, open a PR, and confirm CI passes across the Python matrix
