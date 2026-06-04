## 1. Model & Parsers — TDD

- [ ] 1.1 RED: extend `tests/test_ynab_models.py` — `parse_payee_locations({"data": {"payee_locations": [...]}})` returns `PayeeLocation` tuples (id, payee_id, latitude, longitude, deleted); `parse_payee_location({"data": {"payee_location": {...}}})` returns a single one; run `pytest`, confirm FAILS
- [ ] 1.2 GREEN: add a frozen `PayeeLocation` dataclass (`id`, `payee_id`, `latitude: str | None`, `longitude: str | None`, `deleted: bool`), a shared `_payee_location_from`, and pure `parse_payee_locations`/`parse_payee_location` to `ynab/models.py`; run `pytest`, confirm PASS
- [ ] 1.3 RED: add edge-case tests — empty list → `()`; a record missing `latitude`/`longitude` → `None` (no raise); `parse_payee_location` on a body missing `payee_location`/`id` raises; run `pytest`, confirm FAILS
- [ ] 1.4 GREEN: make `parse_payee_locations` defensive and `parse_payee_location` require `payee_location`/`id`; run `pytest`, confirm PASS

## 2. Client Methods — TDD (httpx MockTransport)

- [ ] 2.1 RED: extend `tests/test_ynab_client.py` — `list_payee_locations()` → `GET /v1/plans/last-used/payee_locations`; `get_payee_location("pl1")` → `GET /v1/plans/last-used/payee_locations/pl1` (and a 404 → `YnabApiError`); `list_payee_locations_for_payee("py1")` → `GET /v1/plans/last-used/payees/py1/payee_locations`; all with bearer; run `pytest`, confirm FAILS
- [ ] 2.2 GREEN: add `list_payee_locations`, `get_payee_location`, and `list_payee_locations_for_payee` to `YnabClient` (all `plan_id` default `last-used`); run `pytest`, confirm PASS

## 3. MCP Tools — TDD

- [ ] 3.1 RED: extend `tests/test_ynab_tools.py` — the three tools return data via a `MockTransport`-backed client (monkeypatched `client_from_env`), asserting the request paths; and each raises `YnabAuthError` with no token; run `pytest`, confirm FAILS
- [ ] 3.2 GREEN: add the three tools to `ynab/tools.py` (thin wrappers; full type hints); run `pytest`, confirm PASS

## 4. Register Tools & Server Test

- [ ] 4.1 GREEN: register the three tools in `build_server` (`server.py`)
- [ ] 4.2 Update `test_server.py` to expect the new tools in the registered set (15 total) with typed input schemas; run `pytest`

## 5. Refactor & Quality Gate

- [ ] 5.1 REFACTOR: confirm FP boundaries (pure parsers; I/O only in the client) and full type hints
- [ ] 5.2 Run the full local gate: `ruff check`, `ruff format --check`, `mypy` (strict), and `pytest` with `--cov-fail-under=90` — all green

## 6. Documentation & Smoke Test

- [ ] 6.1 Update `README.md`: add the three payee-location tools to the tools table
- [ ] 6.2 Smoke-test `list_payee_locations` via `MockTransport` (assert the `/plans/last-used/payee_locations` path + bearer); confirm `python -m ynab_claude_connector` still starts with all tools registered
- [ ] 6.3 Confirm `python -m build` still produces a valid sdist + wheel

## 7. Final Verification

- [ ] 7.1 Run the full local gate once more (`pre-commit run --all-files`, `actionlint`, `pytest`) — all green
- [ ] 7.2 Commit on a feature branch, open a PR, and confirm CI passes across the Python matrix
