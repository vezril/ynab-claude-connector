## 1. Model & Parsers — TDD

- [ ] 1.1 RED: extend `tests/test_ynab_models.py` — `parse_payees({"data": {"payees": [...]}})` returns `Payee` tuples (id, name, transfer_account_id, deleted); `parse_payee({"data": {"payee": {...}}})` returns a single `Payee`; run `pytest`, confirm FAILS
- [ ] 1.2 GREEN: add a frozen `Payee` dataclass (`id`, `name`, `transfer_account_id: str | None`, `deleted: bool`), a shared `_payee_from`, and pure `parse_payees`/`parse_payee` to `ynab/models.py`; run `pytest`, confirm PASS
- [ ] 1.3 RED: add edge-case tests — empty payees list → `()`; a payee missing `transfer_account_id` → `None` (no raise); `parse_payee` on a body missing `payee`/`id` raises; run `pytest`, confirm FAILS
- [ ] 1.4 GREEN: make `parse_payees` defensive and `parse_payee` require `payee`/`id`; run `pytest`, confirm PASS

## 2. Client Methods — TDD (httpx MockTransport)

- [ ] 2.1 RED: extend `tests/test_ynab_client.py` — `YnabClient.list_payees()` returns parsed payees and the request is `GET /v1/plans/last-used/payees` with bearer; run `pytest`, confirm FAILS
- [ ] 2.2 GREEN: add `async def list_payees(self, plan_id: str = "last-used") -> tuple[Payee, ...]`; run `pytest`, confirm PASS
- [ ] 2.3 RED: add a test — `YnabClient.get_payee("py1")` returns the `Payee` and the request is `GET /v1/plans/last-used/payees/py1`; a 404 maps to `YnabApiError`; run `pytest`, confirm FAILS
- [ ] 2.4 GREEN: add `async def get_payee(self, payee_id: str, plan_id: str = "last-used") -> Payee`; run `pytest`, confirm PASS

## 3. MCP Tools — TDD

- [ ] 3.1 RED: extend `tests/test_ynab_tools.py` — `list_payees()` and `get_payee("py1")` return data via a `MockTransport`-backed client (monkeypatched `client_from_env`), asserting the request paths; and each raises `YnabAuthError` with no token; run `pytest`, confirm FAILS
- [ ] 3.2 GREEN: add the `list_payees` and `get_payee` tools to `ynab/tools.py` (thin wrappers; full type hints); run `pytest`, confirm PASS

## 4. Register Tools & Server Test

- [ ] 4.1 GREEN: register `list_payees` and `get_payee` in `build_server` (`server.py`)
- [ ] 4.2 Update `test_server.py` to expect the new tools in the registered set (12 total) with typed input schemas; run `pytest`

## 5. Refactor & Quality Gate

- [ ] 5.1 REFACTOR: confirm FP boundaries (pure parsers; I/O only in the client) and full type hints
- [ ] 5.2 Run the full local gate: `ruff check`, `ruff format --check`, `mypy` (strict), and `pytest` with `--cov-fail-under=90` — all green

## 6. Documentation & Smoke Test

- [ ] 6.1 Update `README.md`: add `list_payees` and `get_payee` to the tools table
- [ ] 6.2 Smoke-test `list_payees` via `MockTransport` (assert the `/plans/last-used/payees` path + bearer); confirm `python -m ynab_claude_connector` still starts with all tools registered
- [ ] 6.3 Confirm `python -m build` still produces a valid sdist + wheel

## 7. Final Verification

- [ ] 7.1 Run the full local gate once more (`pre-commit run --all-files`, `actionlint`, `pytest`) — all green
- [ ] 7.2 Commit on a feature branch, open a PR, and confirm CI passes across the Python matrix
