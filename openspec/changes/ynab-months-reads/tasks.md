## 1. Model & Parsers — TDD

- [ ] 1.1 RED: extend `tests/test_ynab_models.py` — `parse_months({"data": {"months": [...]}})` returns `Month` tuples (month, note, income, budgeted, activity, to_be_budgeted, age_of_money, deleted; milliunits); `parse_month({"data": {"month": {...}}})` returns a single `Month`; run `pytest`, confirm FAILS
- [ ] 1.2 GREEN: add a frozen `Month` dataclass and a shared `_month_from`, plus pure `parse_months`/`parse_month` (read `data["months"]`/`data["month"]`) to `ynab/models.py`; run `pytest`, confirm PASS
- [ ] 1.3 RED: add edge-case tests — empty months list → `()`; a month missing `note`/`age_of_money` → `None` (no raise); `parse_month` on a body missing `month` raises; run `pytest`, confirm FAILS
- [ ] 1.4 GREEN: make `parse_months` defensive and `parse_month` require the `month` object; run `pytest`, confirm PASS

## 2. Client Methods — TDD (httpx MockTransport)

- [ ] 2.1 RED: extend `tests/test_ynab_client.py` — `list_months()` → `GET /v1/plans/last-used/months` with bearer; run `pytest`, confirm FAILS
- [ ] 2.2 GREEN: add `async def list_months(self, plan_id: str = "last-used") -> tuple[Month, ...]`; run `pytest`, confirm PASS
- [ ] 2.3 RED: add a test — `get_month("2026-06-01")` → `GET /v1/plans/last-used/months/2026-06-01`; `month="current"` builds `/months/current`; a 404 → `YnabApiError`; run `pytest`, confirm FAILS
- [ ] 2.4 GREEN: add `async def get_month(self, month: str, plan_id: str = "last-used") -> Month`; run `pytest`, confirm PASS

## 3. MCP Tools — TDD

- [ ] 3.1 RED: extend `tests/test_ynab_tools.py` — `list_months()` and `get_month("current")` return data via a `MockTransport`-backed client (monkeypatched `client_from_env`), asserting the request paths; and each raises `YnabAuthError` with no token; run `pytest`, confirm FAILS
- [ ] 3.2 GREEN: add the `list_months` and `get_month` tools to `ynab/tools.py` (thin wrappers; full type hints; docstring notes `month` accepts `current`/ISO date); run `pytest`, confirm PASS

## 4. Register Tools & Server Test

- [ ] 4.1 GREEN: register `list_months` and `get_month` in `build_server` (`server.py`)
- [ ] 4.2 Update `test_server.py` to expect the new tools in the registered set (17 total) with typed input schemas; run `pytest`

## 5. Refactor & Quality Gate

- [ ] 5.1 REFACTOR: confirm FP boundaries (pure parsers; I/O only in the client) and full type hints
- [ ] 5.2 Run the full local gate: `ruff check`, `ruff format --check`, `mypy` (strict), and `pytest` with `--cov-fail-under=90` — all green

## 6. Documentation & Smoke Test

- [ ] 6.1 Update `README.md`: add `list_months` and `get_month` to the tools table (note `month` accepts `current` or an ISO date)
- [ ] 6.2 Smoke-test `list_months` via `MockTransport` (assert the `/plans/last-used/months` path + bearer); confirm `python -m ynab_claude_connector` still starts with all tools registered
- [ ] 6.3 Confirm `python -m build` still produces a valid sdist + wheel

## 7. Final Verification

- [ ] 7.1 Run the full local gate once more (`pre-commit run --all-files`, `actionlint`, `pytest`) — all green
- [ ] 7.2 Commit on a feature branch, open a PR, and confirm CI passes across the Python matrix
