## 1. Rename Migration: budgets → plans (TDD)

- [x] 1.1 RED: update existing tests to plan terminology and `/plans` paths — in `test_ynab_models.py` rename `parse_budgets`→`parse_plans` and use the `{"data": {"plans": [...]}}` envelope; in `test_ynab_client.py`/`test_ynab_tools.py` rename `list_budgets`→`list_plans`, `budget_id`→`plan_id`, and assert paths `/v1/plans`, `/v1/plans/last-used/accounts`, etc.; in `test_server.py` expect `list_plans` (+ later the new tools). Run `pytest`; confirm FAILS (code still uses budgets/`/budgets`)
- [x] 1.2 GREEN: rename in `ynab/models.py` — `Budget`→`Plan`, `parse_budgets`→`parse_plans` (read `data["plans"]`); run `pytest`
- [x] 1.3 GREEN: in `ynab/client.py` — rename `list_budgets`→`list_plans`, change all paths `budgets`→`plans`, rename the `budget_id` params → `plan_id`, and change the default alias `"default"`→`"last-used"`; update imports; run `pytest`
- [x] 1.4 GREEN: in `ynab/tools.py` — rename `list_budgets`→`list_plans`, rename `budget_id`→`plan_id` on the account/category/transaction tools; run `pytest`
- [x] 1.5 GREEN: update `server.py` registration (`list_plans`); run `pytest`, confirm the rename suite is GREEN
- [x] 1.6 Grep `src/` for any remaining `budget`/`/budgets`/`budget_id` references and clean up (none should remain except historical comments)

## 2. Single Plan Summary (`get_plan`) — TDD

- [x] 2.1 RED: add model tests — `parse_plan_detail_summary({"data": {"plan": {...}}})` returns a `PlanDetailSummary` with metadata (id, name, first/last month, last_modified_on), `currency_format`/`date_format`, and counts (accounts, category_groups, categories, payees, months, transactions, scheduled_transactions); include an edge case where nested arrays are missing → counts are 0; run `pytest`, confirm FAILS
- [x] 2.2 GREEN: add frozen dataclasses `CurrencyFormat`, `DateFormat`, `PlanDetailSummary` and the pure `parse_plan_detail_summary` (counts via `len` of each array, defaulting missing → 0) to `ynab/models.py`; run `pytest`
- [x] 2.3 RED: add client test — `YnabClient.get_plan()` returns the summary and the captured request is `GET /v1/plans/last-used` with bearer; `get_plan("p1")` targets `/v1/plans/p1`; run `pytest`, confirm FAILS
- [x] 2.4 GREEN: add `async def get_plan(self, plan_id: str = "last-used") -> PlanDetailSummary` to `YnabClient`; run `pytest`
- [x] 2.5 RED: add tool test — `get_plan` (arg `plan_id="last-used"`) returns the summary via a `MockTransport`-backed client; and `get_plan` with no token raises `YnabAuthError` before any network call; run `pytest`, confirm FAILS
- [x] 2.6 GREEN: add the `get_plan` tool to `ynab/tools.py`; run `pytest`

## 3. Plan Settings (`get_plan_settings`) — TDD

- [x] 3.1 RED: add model test — `parse_plan_settings({"data": {"settings": {"date_format": {...}, "currency_format": {...}}}})` returns a `PlanSettings` with typed `date_format`/`currency_format`; edge case: nullable formats (`None`) parse without raising; run `pytest`, confirm FAILS
- [x] 3.2 GREEN: add `PlanSettings` dataclass and pure `parse_plan_settings` to `ynab/models.py`; run `pytest`
- [x] 3.3 RED: add client test — `YnabClient.get_plan_settings()` returns the settings and the request is `GET /v1/plans/last-used/settings` with bearer; run `pytest`, confirm FAILS
- [x] 3.4 GREEN: add `async def get_plan_settings(self, plan_id: str = "last-used") -> PlanSettings`; run `pytest`
- [x] 3.5 RED: add tool test — `get_plan_settings` returns settings; no-token raises `YnabAuthError`; run `pytest`, confirm FAILS
- [x] 3.6 GREEN: add the `get_plan_settings` tool to `ynab/tools.py`; run `pytest`

## 4. Register Tools & Server Test

- [x] 4.1 GREEN: register `get_plan` and `get_plan_settings` in `build_server` (`server.py`)
- [x] 4.2 Update `test_server.py` to expect the full tool set — `ping`, `get_user`, `list_plans`, `list_accounts`, `list_categories`, `list_transactions`, `get_plan`, `get_plan_settings` — each with a typed input schema; run `pytest`

## 5. Refactor & Quality Gate

- [x] 5.1 REFACTOR: confirm FP boundaries (pure parsers incl. the count logic; I/O only in the client) and full type hints; confine `httpx` to `ynab/client.py`
- [x] 5.2 Run the full local gate: `ruff check`, `ruff format --check`, `mypy` (strict), and `pytest` with `--cov-fail-under=90` — all green

## 6. Documentation & Smoke Test

- [x] 6.1 Update `README.md`: rename `list_budgets`→`list_plans` and `budget_id`→`plan_id` in the tools table; add `get_plan` and `get_plan_settings`; note the `last-used` default alias and that tool names changed (breaking)
- [x] 6.2 Smoke-test `list_plans` and `get_plan` via `MockTransport` (assert `/plans` paths + bearer); confirm `python -m ynab_claude_connector` still starts with all tools registered
- [x] 6.3 Confirm `python -m build` still produces a valid sdist + wheel

## 7. Final Verification

- [x] 7.1 Run the full local gate once more (`pre-commit run --all-files`, `actionlint`, `pytest`) — all green
- [x] 7.2 Commit on a feature branch, open a PR, and confirm CI passes across the Python matrix
