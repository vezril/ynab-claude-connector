## 1. Parser — TDD

- [ ] 1.1 RED: extend `tests/test_ynab_models.py` — `parse_transaction({"data": {"transaction": {...}}})` returns a `Transaction` (id, date, amount, cleared, approved, account_id, memo, payee_name, category_id); run `pytest`, confirm FAILS
- [ ] 1.2 GREEN: add a pure `parse_transaction(payload) -> Transaction` (reads `data["transaction"]`; reuse the existing field mapping) to `ynab/models.py`; run `pytest`, confirm PASS
- [ ] 1.3 RED: add an edge-case test — a payload missing `transaction`/`id` raises (`KeyError`/`TypeError`); run `pytest`, confirm FAILS
- [ ] 1.4 GREEN: ensure `parse_transaction` treats the `transaction` object and its `id` as required; run `pytest`, confirm PASS

## 2. Client Methods — TDD (httpx MockTransport)

- [ ] 2.1 RED: extend `tests/test_ynab_client.py` — `get_transaction("t1")` → `GET /v1/plans/last-used/transactions/t1` (and a 404 → `YnabApiError`); run `pytest`, confirm FAILS
- [ ] 2.2 GREEN: add `async def get_transaction(self, transaction_id: str, plan_id: str = "last-used") -> Transaction`; run `pytest`, confirm PASS
- [ ] 2.3 RED: add tests for the four scoped lists — `list_transactions_by_account("a1")` → `.../accounts/a1/transactions`; `..._by_category("c1")` → `.../categories/c1/transactions`; `..._by_payee("py1")` → `.../payees/py1/transactions`; `..._by_month("current")` → `.../months/current/transactions`; all returning parsed transactions with bearer; run `pytest`, confirm FAILS
- [ ] 2.4 GREEN: add the four scoped-list methods to `YnabClient` (reuse `parse_transactions`); run `pytest`, confirm PASS

## 3. MCP Tools — TDD

- [ ] 3.1 RED: extend `tests/test_ynab_tools.py` — the five tools return data via a `MockTransport`-backed client (monkeypatched `client_from_env`), asserting the request paths; and each raises `YnabAuthError` with no token; run `pytest`, confirm FAILS
- [ ] 3.2 GREEN: add the five tools to `ynab/tools.py` (thin wrappers; full type hints; `by_month` docstring notes `month` accepts `current`/ISO); run `pytest`, confirm PASS

## 4. Register Tools & Server Test

- [ ] 4.1 GREEN: register the five tools in `build_server` (`server.py`)
- [ ] 4.2 Update `test_server.py` to expect the new tools in the registered set (26 total) with typed input schemas; run `pytest`

## 5. Refactor & Quality Gate

- [ ] 5.1 REFACTOR: confirm FP boundaries (pure parsers; I/O only in the client) and full type hints
- [ ] 5.2 Run the full local gate: `ruff check`, `ruff format --check`, `mypy` (strict), and `pytest` with `--cov-fail-under=90` — all green

## 6. Documentation & Smoke Test

- [ ] 6.1 Update `README.md`: add the five transaction tools to the tools table
- [ ] 6.2 Smoke-test `get_transaction` via `MockTransport` (assert the `/plans/last-used/transactions/{id}` path + bearer); confirm `python -m ynab_claude_connector` still starts with all tools registered
- [ ] 6.3 Confirm `python -m build` still produces a valid sdist + wheel

## 7. Final Verification

- [ ] 7.1 Run the full local gate once more (`pre-commit run --all-files`, `actionlint`, `pytest`) — all green
- [ ] 7.2 Commit on a feature branch, open a PR, and confirm CI passes across the Python matrix
