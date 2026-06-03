## 1. Model & Parser — TDD

- [x] 1.1 RED: extend `tests/test_ynab_models.py` — `parse_user({"data": {"user": {"id": "u1"}}})` returns a `User` with `id == "u1"`; run `pytest`, confirm FAILS
- [x] 1.2 GREEN: add a frozen, slotted `User` dataclass (`id: str`) and a pure `parse_user(payload) -> User` to `ynab/models.py`; run `pytest`, confirm PASS
- [x] 1.3 RED: add an edge-case test — a payload missing `user`/`id` raises (e.g. `KeyError`/`TypeError`), not a `User` with an empty id; run `pytest`, confirm FAILS
- [x] 1.4 GREEN: ensure `parse_user` treats `id` as required so the malformed case raises; run `pytest`, confirm PASS

## 2. Client Method — TDD (httpx MockTransport)

- [x] 2.1 RED: extend `tests/test_ynab_client.py` — via `MockTransport`, `YnabClient.get_user()` returns the parsed `User`, and the captured request is `GET /v1/user` carrying `Authorization: Bearer <token>`; run `pytest`, confirm FAILS
- [x] 2.2 GREEN: add `async def get_user(self) -> User` to `YnabClient` (`parse_user(await self._get("user"))`); run `pytest`, confirm PASS

## 3. MCP Tool — TDD

- [x] 3.1 RED: extend `tests/test_ynab_tools.py` — `get_user` (no args) returns the user id, using a `MockTransport`-backed client via monkeypatched `client_from_env`; and `get_user` with no token raises `YnabAuthError` before any network call; run `pytest`, confirm FAILS
- [x] 3.2 GREEN: add the `async def get_user() -> User` tool to `ynab/tools.py` (thin wrapper over `client_from_env`); run `pytest`, confirm PASS
- [x] 3.3 GREEN: register `get_user` in `build_server` (`server.py`); update `tests/test_server.py` to expect the new tool name in the registered set and a typed input schema; run `pytest`, confirm PASS

## 4. Refactor & Quality Gate

- [x] 4.1 REFACTOR: confirm the new code keeps the FP boundaries (pure `parse_user`; I/O only in the client) and full type hints
- [x] 4.2 Run the full local gate: `ruff check`, `ruff format --check`, `mypy` (strict), and `pytest` with `--cov-fail-under=90` — all green

## 5. Documentation & Smoke Test

- [x] 5.1 Update `README.md`: add `get_user` to the YNAB tools table
- [x] 5.2 Smoke-test `get_user` via a `MockTransport` (asserts `GET /user` + bearer); confirm `python -m ynab_claude_connector` still starts with the tool registered
- [x] 5.3 Confirm `python -m build` still produces a valid sdist + wheel

## 6. Final Verification

- [x] 6.1 Run the full local gate once more (`pre-commit run --all-files`, `actionlint`, `pytest`) — all green
- [x] 6.2 Commit on a feature branch, open a PR, and confirm CI passes across the Python matrix
