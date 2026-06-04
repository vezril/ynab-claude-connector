## 1. Model & Parsers — TDD

- [ ] 1.1 RED: extend `tests/test_ynab_models.py` — `parse_scheduled_transactions({"data": {"scheduled_transactions": [...]}})` returns `ScheduledTransaction` tuples (id, date_first, date_next, frequency, amount, account_id, payee_id, category_id, memo, deleted); `parse_scheduled_transaction({"data": {"scheduled_transaction": {...}}})` returns a single one; run `pytest`, confirm FAILS
- [ ] 1.2 GREEN: add a frozen `ScheduledTransaction` dataclass, a shared `_scheduled_transaction_from`, and pure `parse_scheduled_transactions`/`parse_scheduled_transaction` to `ynab/models.py`; run `pytest`, confirm PASS
- [ ] 1.3 RED: add edge-case tests — empty list → `()`; a record missing `payee_id`/`category_id`/`memo` → `None` (no raise); `parse_scheduled_transaction` on a body missing `scheduled_transaction`/`id` raises; run `pytest`, confirm FAILS
- [ ] 1.4 GREEN: make `parse_scheduled_transactions` defensive and `parse_scheduled_transaction` require the object/`id`; run `pytest`, confirm PASS

## 2. Client Methods — TDD (httpx MockTransport)

- [ ] 2.1 RED: extend `tests/test_ynab_client.py` — `list_scheduled_transactions()` → `GET /v1/plans/last-used/scheduled_transactions` with bearer; run `pytest`, confirm FAILS
- [ ] 2.2 GREEN: add `async def list_scheduled_transactions(self, plan_id: str = "last-used") -> tuple[ScheduledTransaction, ...]`; run `pytest`, confirm PASS
- [ ] 2.3 RED: add a test — `get_scheduled_transaction("st1")` → `GET /v1/plans/last-used/scheduled_transactions/st1`; a 404 → `YnabApiError`; run `pytest`, confirm FAILS
- [ ] 2.4 GREEN: add `async def get_scheduled_transaction(self, scheduled_transaction_id: str, plan_id: str = "last-used") -> ScheduledTransaction`; run `pytest`, confirm PASS

## 3. MCP Tools — TDD

- [ ] 3.1 RED: extend `tests/test_ynab_tools.py` — `list_scheduled_transactions()` and `get_scheduled_transaction("st1")` return data via a `MockTransport`-backed client (monkeypatched `client_from_env`), asserting the request paths; and each raises `YnabAuthError` with no token; run `pytest`, confirm FAILS
- [ ] 3.2 GREEN: add the two tools to `ynab/tools.py` (thin wrappers; full type hints); run `pytest`, confirm PASS

## 4. Register Tools & Server Test

- [ ] 4.1 GREEN: register `list_scheduled_transactions` and `get_scheduled_transaction` in `build_server` (`server.py`)
- [ ] 4.2 Update `test_server.py` to expect the new tools in the registered set (28 total) with typed input schemas; run `pytest`

## 5. Refactor & Quality Gate

- [ ] 5.1 REFACTOR: confirm FP boundaries (pure parsers; I/O only in the client) and full type hints
- [ ] 5.2 Run the full local gate: `ruff check`, `ruff format --check`, `mypy` (strict), and `pytest` with `--cov-fail-under=90` — all green

## 6. Documentation & Smoke Test

- [ ] 6.1 Update `README.md`: add `list_scheduled_transactions` and `get_scheduled_transaction` to the tools table
- [ ] 6.2 Smoke-test `list_scheduled_transactions` via `MockTransport` (assert the `/plans/last-used/scheduled_transactions` path + bearer); confirm `python -m ynab_claude_connector` still starts with all tools registered
- [ ] 6.3 Confirm `python -m build` still produces a valid sdist + wheel

## 7. Final Verification

- [ ] 7.1 Run the full local gate once more (`pre-commit run --all-files`, `actionlint`, `pytest`) — all green
- [ ] 7.2 Commit on a feature branch, open a PR, and confirm CI passes across the Python matrix
