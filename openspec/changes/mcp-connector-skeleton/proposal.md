## Why

Feature 1 delivered a buildable, tested Python package but no actual application — there is nothing to run. Feature 2 turns the package into a runnable **Claude connector skeleton** so that Feature 3 (YNAB auth + queries) has a real runtime to plug into. Per the [Claude connectors docs](https://claude.com/docs/connectors/building), connectors are **MCP (Model Context Protocol) servers**; remote connectors use the **Streamable HTTP** transport. We adopt the **official MCP Python SDK (FastMCP)** rather than the tentatively-proposed Flask, which would mean hand-rolling the protocol.

## What Changes

- Add a runtime dependency on the official **`mcp`** package (FastMCP) — the first runtime dependency in the project.
- Add a connector application: a factory that builds a configured `FastMCP` server instance and registers tools.
- Add **one trivial tool** (a `ping`/health tool) as a pure, type-hinted function — proves the tool-registration and request/response path end-to-end with **no YNAB calls**.
- Add **configuration** loaded from environment variables (transport, host, port, log level) as an immutable dataclass, with validation.
- Add **structured logging** setup for the server.
- Add a **runnable entry point** (`python -m ynab_claude_connector`) that starts the server; transport defaults to `stdio` for local/test use, with `streamable-http` wiring available for remote deployment (no real HTTP endpoints/auth yet — those come with Feature 3).
- Extend tests (TDD) to cover the tool, the config parsing, and server construction via the in-memory transport; update the README run section.

## Capabilities

### New Capabilities
- `connector-runtime`: The MCP server application skeleton — server factory, tool registration, the sample health/ping tool, environment-based configuration, logging, and the runnable entry point. No YNAB integration.

### Modified Capabilities
<!-- None. project-scaffolding/ci-pipeline requirements are unchanged; this builds on them. -->

## Impact

- **New files**: `src/ynab_claude_connector/server.py`, `tools.py`, `config.py`, `logging.py`, `__main__.py`; corresponding `tests/`.
- **Dependencies**: adds runtime dep `mcp` (FastMCP). Dev deps unchanged.
- **Tooling**: `mcp` is a third-party dependency — mypy/ruff must remain green against the new code; type stubs handled via the SDK's own typing.
- **CI/CD**: no workflow changes required; the existing matrix (3.11–3.13) and coverage gate now also exercise the connector skeleton. Confirm `mcp` supports the full matrix.
- **No deployment yet**: the server is runnable locally; remote Streamable HTTP hosting/OAuth is deferred to a later feature.
