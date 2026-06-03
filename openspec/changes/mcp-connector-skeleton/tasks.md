## 1. Dependency & Environment Setup

- [ ] 1.1 Add runtime dependency `mcp` (FastMCP) to `[project].dependencies` in `pyproject.toml` with a pinned minimum version
- [ ] 1.2 Reinstall the dev environment (`pip install -e ".[dev]"`) and confirm `from mcp.server.fastmcp import FastMCP` imports
- [ ] 1.3 Verify `mcp` supports Python 3.11–3.13; if not, narrow `requires-python`/the CI matrix and note it in the proposal/design

## 2. Configuration — TDD (Red → Green → Refactor)

- [ ] 2.1 RED: Write `tests/test_config.py` asserting `from_env({})` returns the documented defaults (transport `stdio`, host `127.0.0.1`, port `8000`, log level `INFO`); run `pytest`, confirm it FAILS
- [ ] 2.2 RED: Add tests for environment overrides (valid transport/host/port/log level, port parsed as `int`); confirm FAILS
- [ ] 2.3 GREEN: Implement `config.py` — a frozen `ServerConfig` dataclass, a `ConfigError` exception, and a pure `from_env(env: Mapping[str, str]) -> ServerConfig` with type hints; run `pytest`, confirm PASS
- [ ] 2.4 RED: Add edge-case tests — invalid transport (e.g. `carrier-pigeon`) raises `ConfigError`; non-integer port (e.g. `abc`) raises `ConfigError`; confirm they FAIL appropriately
- [ ] 2.5 GREEN: Add validation to `from_env` so edge-case tests PASS; run `pytest`

## 3. Health Tool — TDD

- [ ] 3.1 RED: Write `tests/test_tools.py` asserting `ping() -> str` returns `"pong"` and is pure (same result on repeated calls); run `pytest`, confirm it FAILS
- [ ] 3.2 GREEN: Implement `tools.py` with a pure, type-hinted `ping() -> str`; run `pytest`, confirm PASS

## 4. Server Factory — TDD

- [ ] 4.1 RED: Write `tests/test_server.py` asserting `build_server(config)` returns a `FastMCP` instance whose tool listing includes `ping` (await the SDK tool-listing via `asyncio.run`); run `pytest`, confirm it FAILS
- [ ] 4.2 RED: Add a test that `build_server` called twice returns independent instances (no shared mutable state); confirm FAILS
- [ ] 4.3 GREEN: Implement `server.py` — `build_server(config: ServerConfig) -> FastMCP` that creates a `FastMCP` (name + host/port from config) and registers `ping`; run `pytest`, confirm PASS
- [ ] 4.4 RED (optional integration): Add a test invoking `ping` through the server (SDK `call_tool`) and asserting the `"pong"` result; GREEN if not already passing; run `pytest`

## 5. Logging & Entry Point

- [ ] 5.1 Implement `logging.py` with `configure_logging(level: str) -> None` (structured/standard logging setup); add a minimal test that it accepts a valid level without error
- [ ] 5.2 Implement `__main__.py` with `main() -> None`: load `from_env(os.environ)` → `configure_logging` → `build_server` → `server.run(transport=...)`; isolate the blocking `run` call and mark only that line `# pragma: no cover`
- [ ] 5.3 RED: Add a test that `main()` with an invalid environment raises `ConfigError` before serving (e.g. by monkeypatching `os.environ` and asserting it fails fast); GREEN by confirming wiring order; run `pytest`
- [ ] 5.4 Add a console-script entry point in `pyproject.toml` (`[project.scripts] ynab-claude-connector = "ynab_claude_connector.__main__:main"`)

## 6. Refactor & Quality Gate

- [ ] 6.1 REFACTOR: Ensure FP style (pure functions, immutable config, no module-level mutable state); confine all `mcp` SDK usage to `server.py`/`__main__.py`
- [ ] 6.2 Run the full local gate: `ruff check`, `ruff format --check`, `mypy` (strict, including the new modules), and `pytest` with `--cov-fail-under=90` — all green
- [ ] 6.3 Add any necessary mypy overrides for the `mcp` package only if it lacks type information (prefer none)

## 7. Smoke Test & Documentation

- [ ] 7.1 Manually smoke-test `python -m ynab_claude_connector` on the default `stdio` transport — confirm it starts without error (and shuts down cleanly)
- [ ] 7.2 Update `README.md`: add a "Running the connector" section (module + console script, the env vars and their defaults, stdio vs streamable-http) and note YNAB features are not included yet
- [ ] 7.3 Confirm `python -m build` still produces valid sdist + wheel with the new runtime dependency declared

## 8. Final Verification

- [ ] 8.1 Run the full local gate once more (`pre-commit run --all-files`, `actionlint`, `pytest`) — all green
- [ ] 8.2 Commit on a feature branch, open a PR, and confirm CI passes across the Python matrix
