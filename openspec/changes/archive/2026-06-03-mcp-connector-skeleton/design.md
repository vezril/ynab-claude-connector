## Context

Feature 1 produced a tested, CI-backed package (`ynab_claude_connector`) with a `src/` layout, ruff/mypy/pytest gates, a 90% coverage floor, and tag-derived versioning. It contains only placeholder helpers — there is no runnable application. Feature 2 makes the package a runnable **Claude connector** skeleton without any YNAB functionality, establishing the runtime that Feature 3 will extend with YNAB auth and queries.

Per the Claude connectors documentation, connectors are **MCP servers**; remote connectors use the **Streamable HTTP** transport, and there is an official **Python SDK (`mcp`, including FastMCP)**. The user confirmed (a) building on the **official MCP Python SDK / FastMCP**, and (b) the Feature 2 deliverable is a **minimal MCP server exposing one trivial tool**, tested via the in-memory/stdio path, with Streamable HTTP wiring present but no real endpoints or auth yet.

## Goals / Non-Goals

**Goals:**
- A runnable MCP server built with FastMCP that starts up and exposes one trivial, pure tool (`ping`).
- Environment-based, validated, immutable configuration (transport, host, port, log level).
- Structured logging setup.
- A `python -m ynab_claude_connector` entry point (and a console script) that runs the server; `stdio` default for local/test, `streamable-http` selectable.
- TDD coverage of the tool, config parsing (incl. edge cases), and server construction via the in-memory transport — keeping the 90% coverage floor and ruff/mypy green across Python 3.11–3.13.

**Non-Goals:**
- No YNAB API calls, auth, or data tools (Feature 3).
- No OAuth / Dynamic Client Registration, no deployed remote HTTP endpoint, no container/infra (later).
- No resources/prompts/sampling — just a single tool to prove the path.
- No persistence or state.

## Decisions

### Decision 1: Use the official MCP Python SDK (FastMCP) as the runtime
**Choice**: Depend on `mcp` and build the server with `from mcp.server.fastmcp import FastMCP`. Tools are registered on a `FastMCP` instance.
**Why over Flask**: Connectors must speak MCP; FastMCP implements the protocol, tool schema generation (from type hints), and both `stdio` and `streamable-http` transports. Flask would require hand-rolling MCP framing and the Streamable HTTP transport — more code, more bugs, non-standard. FastMCP also derives each tool's input schema from Python type hints, which dovetails with the project's "type hints everywhere" rule.
**Alternatives**: Flask (rejected — see above); MCP SDK mounted on FastAPI (deferred — only needed once we add non-MCP HTTP routes like OAuth callbacks/health, which belong to the deployment feature).

### Decision 2: Functional core, thin imperative shell
**Choice**: Keep all logic pure and testable:
- `config.py` — `ServerConfig` frozen dataclass + `from_env(env: Mapping[str, str]) -> ServerConfig` (pure; takes the environment as an argument).
- `tools.py` — tool implementations as pure, type-hinted functions (`ping() -> str`).
- `server.py` — `build_server(config: ServerConfig) -> FastMCP` factory that registers tools and returns a fresh instance (no module-level mutable state).
- `logging.py` — `configure_logging(level: str) -> None` (thin side-effecting setup).
- `__main__.py` — `main()` wires env → config → logging → server and calls `server.run(...)`; only the final blocking `run` call is outside test coverage.
**Why**: Purity makes the tool and config trivially unit-testable and matches the project's FP preference; the only hard-to-test line (the blocking server run) is isolated.

### Decision 3: Configuration via environment variables, validated into an immutable type
**Choice**: `from_env` reads `YNAB_CONNECTOR_TRANSPORT` (default `stdio`), `YNAB_CONNECTOR_HOST` (default `127.0.0.1`), `YNAB_CONNECTOR_PORT` (default `8000`), `YNAB_CONNECTOR_LOG_LEVEL` (default `INFO`). Invalid transport or non-integer/out-of-range port raises a custom `ConfigError`.
**Why**: Twelve-factor style; environment config is the norm for connectors/servers and keeps secrets/host config out of code (important for Feature 3's YNAB token). A frozen dataclass makes config immutable and type-checked. A dedicated exception gives callers a precise failure (EAFP).
**Alternatives**: `pydantic-settings` — heavier dependency; the dataclass + a small pure parser is enough now and avoids a dep. A CLI flag parser — deferred; env vars are the deployment-friendly default.

### Decision 4: Default transport `stdio`; `streamable-http` available but no endpoints
**Choice**: Default to `stdio` so the server is runnable locally and in tests without networking; allow `streamable-http` (FastMCP configures host/port from `ServerConfig`). No custom HTTP routes, health endpoint, or auth are added yet.
**Why**: Claude.ai uses Streamable HTTP for remote connectors, but standing up a deployable, authenticated HTTP endpoint is a separate concern (deployment/Feature 3). `stdio` keeps Feature 2 self-contained and fully testable while the transport choice is already pluggable for later.

### Decision 5: Test through the in-memory/SDK surface, no new heavy test deps
**Choice**: Unit-test pure functions directly (sync). For server construction, assert the tool is registered by awaiting the SDK's tool listing via `asyncio.run(...)` (and optionally invoking the tool through the server) — no `pytest-asyncio` needed.
**Why**: Keeps the dev toolchain unchanged and the tests fast and deterministic; `asyncio.run` around a single coroutine is sufficient for the one integration assertion.

## Risks / Trade-offs

- **Risk: `mcp` SDK API surface/version drift** (FastMCP method names, run signature). → Mitigation: pin a minimum `mcp` version in `pyproject.toml`; isolate SDK usage to `server.py`/`__main__.py` so a future API change touches one place; CI across 3.11–3.13 catches version/compat issues.
- **Risk: `mcp` may not support the full Python matrix.** → Mitigation: verify on install during apply; if it requires a higher floor, narrow the matrix and `requires-python` and note it (CI will surface failures immediately).
- **Risk: the blocking `server.run()` line is untestable, threatening the 90% gate.** → Mitigation: isolate it in `__main__` and mark only that line `# pragma: no cover`; all wiring around it is tested.
- **Trade-off: `stdio` default differs from the eventual remote Streamable HTTP deployment.** → Accepted; transport is a single config value, so switching later is a config change, not a refactor.
- **Trade-off: env-var config without pydantic** means hand-written validation. → Accepted; the surface is tiny and fully unit-tested, avoiding a dependency.

## Migration Plan

1. Add the `mcp` runtime dependency; reinstall dev environment.
2. TDD the pure pieces (tool, config) then the server factory (Red→Green→Refactor).
3. Add the entry point and console script; manually smoke-test `python -m ynab_claude_connector` (stdio) starts and responds.
4. Update the README run section.
- **Rollback**: additive; revert the change. No deployed runtime to roll back.

## Open Questions

- None blocking. (Whether to later mount FastMCP on FastAPI for OAuth/health endpoints is deferred to the deployment/YNAB-auth feature.)
