## 1. Parser — TDD

- [ ] 1.1 RED: extend `tests/test_ynab_models.py` — `parse_category({"data": {"category": {...}}})` returns a `Category` with id/name/category_group_id/budgeted/activity/balance (milliunits); run `pytest`, confirm FAILS
- [ ] 1.2 GREEN: add a pure `parse_category(payload) -> Category` (reads `data["category"]`; `id` required) to `ynab/models.py`; run `pytest`, confirm PASS
- [ ] 1.3 RED: add an edge-case test — a payload missing `category`/`id` raises (`KeyError`/`TypeError`), not an empty `Category`; run `pytest`, confirm FAILS
- [ ] 1.4 GREEN: ensure `parse_category` treats the `category` object and its `id` as required; run `pytest`, confirm PASS

## 2. Client Methods — TDD (httpx MockTransport)

- [ ] 2.1 RED: extend `tests/test_ynab_client.py` — `YnabClient.get_category("c1")` returns the parsed `Category` and the request is `GET /v1/plans/last-used/categories/c1` with bearer; run `pytest`, confirm FAILS
- [ ] 2.2 GREEN: add `async def get_category(self, category_id: str, plan_id: str = "last-used") -> Category`; run `pytest`, confirm PASS
- [ ] 2.3 RED: add a test — `YnabClient.get_month_category("2026-06-01", "c1")` returns the `Category` and the request is `GET /v1/plans/last-used/months/2026-06-01/categories/c1`; also assert `month="current"` builds `/months/current/`; run `pytest`, confirm FAILS
- [ ] 2.4 GREEN: add `async def get_month_category(self, month: str, category_id: str, plan_id: str = "last-used") -> Category`; run `pytest`, confirm PASS
- [ ] 2.5 RED: add an error test — a `MockTransport` returning 404 → `YnabApiError` from `get_category`; run `pytest`, confirm FAILS (or GREEN if existing mapping already covers it); GREEN

## 3. MCP Tools — TDD

- [ ] 3.1 RED: extend `tests/test_ynab_tools.py` — `get_category("c1")` and `get_month_category("current", "c1")` return the category via a `MockTransport`-backed client (monkeypatched `client_from_env`), asserting the request paths; and each raises `YnabAuthError` with no token; run `pytest`, confirm FAILS
- [ ] 3.2 GREEN: add the `get_category` and `get_month_category` tools to `ynab/tools.py` (thin wrappers; full type hints; docstring notes `month` accepts `current`/ISO date); run `pytest`, confirm PASS

## 4. Register Tools & Server Test

- [ ] 4.1 GREEN: register `get_category` and `get_month_category` in `build_server` (`server.py`)
- [ ] 4.2 Update `test_server.py` to expect the new tools in the registered set (10 total) with typed input schemas; run `pytest`

## 5. Refactor & Quality Gate

- [ ] 5.1 REFACTOR: confirm FP boundaries (pure `parse_category`; I/O only in the client) and full type hints
- [ ] 5.2 Run the full local gate: `ruff check`, `ruff format --check`, `mypy` (strict), and `pytest` with `--cov-fail-under=90` — all green

## 6. Documentation & Smoke Test

- [ ] 6.1 Update `README.md`: add `get_category` and `get_month_category` to the tools table (note `month` accepts `current` or an ISO date)
- [ ] 6.2 Smoke-test `get_category` via `MockTransport` (assert the `/plans/last-used/categories/{id}` path + bearer); confirm `python -m ynab_claude_connector` still starts with all tools registered
- [ ] 6.3 Confirm `python -m build` still produces a valid sdist + wheel

## 7. Final Verification

- [ ] 7.1 Run the full local gate once more (`pre-commit run --all-files`, `actionlint`, `pytest`) — all green
- [ ] 7.2 Commit on a feature branch, open a PR, and confirm CI passes across the Python matrix
