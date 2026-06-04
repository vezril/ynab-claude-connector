## 1. Models & Parsers — TDD

- [ ] 1.1 RED: extend `tests/test_ynab_models.py` — `parse_money_movements({"data": {"money_movements": [...]}})` returns `MoneyMovement` tuples (id, month, moved_at, note, money_movement_group_id, performed_by_user_id, from_category_id, to_category_id, amount); `parse_money_movement_groups({"data": {"money_movement_groups": [...]}})` returns `MoneyMovementGroup` tuples (id, group_created_at, month, note, performed_by_user_id); run `pytest`, confirm FAILS
- [ ] 1.2 GREEN: add frozen `MoneyMovement`/`MoneyMovementGroup` dataclasses, shared `_money_movement_from`/`_money_movement_group_from`, and pure `parse_money_movements`/`parse_money_movement_groups` to `ynab/models.py`; run `pytest`, confirm PASS
- [ ] 1.3 RED: add edge-case tests — empty lists → `()`; a movement with only `id`/`amount` → other fields `None`; run `pytest`, confirm FAILS
- [ ] 1.4 GREEN: make the parsers defensive (only `id`/`amount` required on a movement; `id` on a group); run `pytest`, confirm PASS

## 2. Client Methods — TDD (httpx MockTransport)

- [ ] 2.1 RED: extend `tests/test_ynab_client.py` — `list_money_movements()` → `GET /v1/plans/last-used/money_movements`; `list_money_movements_for_month("current")` → `.../months/current/money_movements`; `list_money_movement_groups()` → `.../money_movement_groups`; `list_money_movement_groups_for_month("2026-06-01")` → `.../months/2026-06-01/money_movement_groups`; all with bearer; plus a 404 → `YnabApiError`; run `pytest`, confirm FAILS
- [ ] 2.2 GREEN: add the four methods to `YnabClient` (all `plan_id` default `last-used`); run `pytest`, confirm PASS

## 3. MCP Tools — TDD

- [ ] 3.1 RED: extend `tests/test_ynab_tools.py` — the four tools return data via a `MockTransport`-backed client (monkeypatched `client_from_env`), asserting the request paths; and each raises `YnabAuthError` with no token; run `pytest`, confirm FAILS
- [ ] 3.2 GREEN: add the four tools to `ynab/tools.py` (thin wrappers; full type hints; per-month docstrings note `month` accepts `current`/ISO); run `pytest`, confirm PASS

## 4. Register Tools & Server Test

- [ ] 4.1 GREEN: register the four tools in `build_server` (`server.py`)
- [ ] 4.2 Update `test_server.py` to expect the new tools in the registered set (21 total) with typed input schemas; run `pytest`

## 5. Refactor & Quality Gate

- [ ] 5.1 REFACTOR: confirm FP boundaries (pure parsers; I/O only in the client) and full type hints
- [ ] 5.2 Run the full local gate: `ruff check`, `ruff format --check`, `mypy` (strict), and `pytest` with `--cov-fail-under=90` — all green

## 6. Documentation & Smoke Test

- [ ] 6.1 Update `README.md`: add the four money-movement tools to the tools table
- [ ] 6.2 Smoke-test `list_money_movements` via `MockTransport` (assert the `/plans/last-used/money_movements` path + bearer); confirm `python -m ynab_claude_connector` still starts with all tools registered
- [ ] 6.3 Confirm `python -m build` still produces a valid sdist + wheel

## 7. Final Verification

- [ ] 7.1 Run the full local gate once more (`pre-commit run --all-files`, `actionlint`, `pytest`) — all green
- [ ] 7.2 Commit on a feature branch, open a PR, and confirm CI passes across the Python matrix
