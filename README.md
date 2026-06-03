# ynab-claude-connector

A [Claude connector](https://claude.com/docs/connectors/building) that integrates with
[YNAB (You Need A Budget)](https://api.ynab.com/) so you can get insights into your budget
through Claude.

> **Status:** Working MCP connector with read-only YNAB access (budgets, accounts,
> categories, transactions) over the default `stdio` transport. Remote hosting (OAuth +
> HTTPS) and write operations are planned for later changes.

---

## Requirements

- Python **3.11+** (CI tests against 3.11, 3.12, and 3.13)
- [Git](https://git-scm.com/) (the package version is derived from Git tags — see
  [Versioning](#versioning))

## Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/vezril/ynab-claude-connector.git
cd ynab-claude-connector

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install the package with its development dependencies
pip install --upgrade pip
pip install -e ".[dev]"

# 4. Install the pre-commit hooks (runs ruff + mypy before each commit)
pre-commit install
```

## Running the tests

The test suite runs under [pytest](https://docs.pytest.org/) with coverage enabled by
default (configured in `pyproject.toml`):

```bash
pytest
```

This enforces a **minimum coverage floor of 90%**; the run fails if coverage drops below it.

Run the full local quality gate (the same checks CI runs):

```bash
pre-commit run --all-files   # ruff lint + format, mypy
pytest                       # tests + coverage
```

## Building the package

The project builds to an sdist and a wheel via the standard build frontend:

```bash
python -m build
# distributions are written to dist/
```

## Running the connector

The connector is a [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server
built with the official [`mcp`](https://github.com/modelcontextprotocol/python-sdk) SDK
(FastMCP). It exposes a `ping` health tool plus read-only [YNAB](https://api.ynab.com/)
tools (see [YNAB integration](#ynab-integration)).

Run it as a module or via the installed console script:

```bash
python -m ynab_claude_connector
# or
ynab-claude-connector
```

It is configured entirely through environment variables:

| Variable                     | Default     | Description                                  |
| ---------------------------- | ----------- | -------------------------------------------- |
| `YNAB_CONNECTOR_TRANSPORT`   | `stdio`     | Transport: `stdio` or `streamable-http`      |
| `YNAB_CONNECTOR_HOST`        | `127.0.0.1` | Bind host (used by `streamable-http`)        |
| `YNAB_CONNECTOR_PORT`        | `8000`      | Bind port (used by `streamable-http`)        |
| `YNAB_CONNECTOR_LOG_LEVEL`   | `INFO`      | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |

The default `stdio` transport is convenient for local use and testing. Claude's remote
connectors use the `streamable-http` transport:

```bash
YNAB_CONNECTOR_TRANSPORT=streamable-http YNAB_CONNECTOR_PORT=8000 ynab-claude-connector
```

Invalid configuration (e.g. an unknown transport or a non-numeric port) fails fast at
startup with a clear error before the server begins serving.

## YNAB integration

The connector exposes read-only access to your YNAB budget data as MCP tools.

### Authentication

Authentication uses a **Personal Access Token** (single user, your own account). Create one
in YNAB under **Account Settings → Developer Settings → New Token**, then provide it via the
environment:

| Variable            | Default                     | Description                                  |
| ------------------- | --------------------------- | -------------------------------------------- |
| `YNAB_TOKEN`        | _(none)_                    | YNAB Personal Access Token (**required** for YNAB tools) |
| `YNAB_API_BASE_URL` | `https://api.ynab.com/v1`   | API base URL (override for testing/proxying) |

The token is treated as a secret: it is read only from the environment and never logged or
included in any object representation. The server still starts without a token (the `ping`
tool works); a YNAB tool invoked without a token fails fast with a clear "set `YNAB_TOKEN`"
error before any network call.

```bash
export YNAB_TOKEN="your-personal-access-token"
ynab-claude-connector
```

### Tools

| Tool                | Arguments                       | Returns                                              |
| ------------------- | ------------------------------- | ---------------------------------------------------- |
| `get_user`          | _(none)_                        | The authenticated user's id                          |
| `list_budgets`      | _(none)_                        | Your budgets (id, name)                              |
| `list_accounts`     | `budget_id` (default `default`) | Accounts with balances                               |
| `list_categories`   | `budget_id` (default `default`) | Categories with budgeted/activity/balance            |
| `list_transactions` | `budget_id` (default `default`) | Transactions (date, amount, payee, category, memo)   |

`budget_id` defaults to YNAB's `default` alias (your last-used budget), so you usually don't
need to know your budget id. Monetary values are returned in YNAB **milliunits** (integers,
e.g. `123450` = `$123.45`) with no lossy currency conversion.

### Rate limits

YNAB allows **200 requests per hour per token**. Exceeding it returns HTTP 429, which the
connector surfaces as a clear rate-limit error.

> **Not yet included:** OAuth, write/mutating operations, and incremental delta sync — these
> are planned for later changes.

## Use with Claude Desktop

Claude Desktop can launch this connector as a **local MCP server** over the default `stdio`
transport. (Claude.ai's *web* "Custom Connectors" require a remote HTTPS URL with OAuth —
not covered here.)

### 1. Open the config file

In Claude Desktop: **Settings → Developer → Edit Config**. This opens (creating it if
needed):

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

### 2. Add the connector

Point `command` at an absolute path to the installed console script, and pass your YNAB
token via the `env` block:

```json
{
  "mcpServers": {
    "ynab": {
      "command": "/absolute/path/to/ynab-claude-connector/.venv/bin/ynab-claude-connector",
      "env": {
        "YNAB_TOKEN": "your-personal-access-token"
      }
    }
  }
}
```

Equivalent form using the module instead of the console script:

```json
{
  "mcpServers": {
    "ynab": {
      "command": "/absolute/path/to/ynab-claude-connector/.venv/bin/python",
      "args": ["-m", "ynab_claude_connector"],
      "env": { "YNAB_TOKEN": "your-personal-access-token" }
    }
  }
}
```

Notes:

- **No `args`/transport needed** for the first form — `stdio` is the default and is exactly
  what Claude Desktop expects.
- The **token goes in the `env` block**, not your shell — Desktop launches the process
  itself and won't inherit your terminal environment.
- **Use absolute paths.** Desktop doesn't run inside your virtualenv or the repo directory,
  so a bare `ynab-claude-connector`/`python` usually won't resolve.
- If you already have other servers, add the `"ynab"` key inside the existing `mcpServers`
  object.

### 3. Restart Claude Desktop

Fully quit and reopen it (the config is read at startup). The connector then appears in the
tools menu, exposing `ping`, `get_user`, `list_budgets`, `list_accounts`,
`list_categories`, and `list_transactions`. Try asking *"List my YNAB budgets"* or *"What
are my account balances?"*.

### Troubleshooting

- `ping` works without a token — use it as a first connectivity test. A missing token
  surfaces as a clear authentication error only when a YNAB tool runs.
- Check Desktop's MCP logs if the server doesn't load: `~/Library/Logs/Claude/mcp*.log`
  (macOS).
- The package must remain installed in the referenced environment
  (`pip install -e ".[dev]"`).

## Project layout

```
.
├── .github/workflows/   # CI (lint/type-check/test) and Release (tag-triggered build)
├── src/
│   └── ynab_claude_connector/
│       ├── __main__.py        # runnable entry point (python -m ynab_claude_connector)
│       ├── server.py          # FastMCP server factory (MCP SDK usage lives here)
│       ├── tools.py           # ping health tool
│       ├── config.py          # env-based, validated, immutable ServerConfig
│       ├── logging_config.py  # logging setup
│       └── ynab/              # YNAB integration
│           ├── client.py       # async httpx client (httpx usage lives here)
│           ├── models.py       # typed models + pure response parsers
│           ├── errors.py       # error taxonomy + status mapper
│           └── tools.py        # the four read-only MCP tools
├── tests/               # pytest suite
├── pyproject.toml       # metadata, dependencies, and tool config (ruff/mypy/pytest)
└── .pre-commit-config.yaml
```

The **`src/` layout** ensures tests run against the *installed* package, so packaging
mistakes (e.g. a module missing from the wheel) are caught in CI rather than masked by the
working directory.

## Tooling

| Concern        | Tool                          |
| -------------- | ----------------------------- |
| Lint + format  | [ruff](https://docs.astral.sh/ruff/) |
| Type checking  | [mypy](https://mypy-lang.org/) (strict) |
| Tests + coverage | [pytest](https://docs.pytest.org/) + [pytest-cov](https://pytest-cov.readthedocs.io/) |
| Build backend  | [hatchling](https://hatch.pypa.io/) + [hatch-vcs](https://github.com/ofek/hatch-vcs) |
| Workflow lint  | [actionlint](https://github.com/rhysd/actionlint) |

All code uses **type hints** and favors a **functional style** (pure functions, no mutable
module state).

## Development workflow

This project uses **trunk-based development**:

- **`main`** is always releasable and protected. Direct pushes are not allowed.
- Work happens on **short-lived feature branches** that merge into `main` via **pull
  request**. CI (lint, type-check, tests across the Python matrix) **must pass** before merge.
- **Releases** are cut by pushing an annotated SemVer tag (`vX.Y.Z`) on `main`, which
  triggers the release workflow to build and upload the versioned artifacts.
- **Experimental / pre-release builds** are expressed with SemVer pre-release tags
  (e.g. `v0.2.0-rc.1`) and per-PR CI artifacts — there is intentionally no long-lived
  `development` branch.

### Test-Driven Development (required)

All behavior is developed **test-first** following **Red → Green → Refactor**:

1. **Red** — write a failing test for the desired behavior and run `pytest` to see it fail.
2. **Green** — write the minimum code to make the test pass; run `pytest`.
3. **Refactor** — clean up (ruff + mypy green) while keeping the tests passing.

## Versioning

The project follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

The **Git tag is the single source of truth** for the version: `hatch-vcs` derives the
package version from the latest `vX.Y.Z` tag at build time, and the package reads it back at
runtime via `importlib.metadata`. There is **no static version string** to keep in sync.

- A tagged build from `v0.1.0` produces version `0.1.0`.
- An untagged commit produces a deterministic development version (e.g. `0.1.dev3+g<sha>`).

```python
import ynab_claude_connector
print(ynab_claude_connector.__version__)
```

## Continuous Integration

- **`.github/workflows/ci.yml`** — runs on pushes to `main` and on pull requests:
  `actionlint`, `ruff` (lint + format), `mypy`, and `pytest` (with the 90% coverage gate)
  across Python 3.11/3.12/3.13. Uses a least-privilege token and cancels superseded runs.
- **`.github/workflows/release.yml`** — runs only on `v*` tag pushes: builds the sdist and
  wheel and uploads them as a workflow artifact.

## License

MIT
