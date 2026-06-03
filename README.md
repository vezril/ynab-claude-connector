# ynab-claude-connector

A [Claude connector](https://claude.com/docs/connectors/building) that integrates with
[YNAB (You Need A Budget)](https://api.ynab.com/) so you can get insights into your budget
through Claude.

> **Status:** Foundation only. This first release is the buildable, tested, CI-backed
> Python skeleton — there is no YNAB or Claude integration code yet. Those features land
> in subsequent changes.

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
(FastMCP). It currently exposes a single trivial `ping` health tool — **no YNAB features
yet** (those land in a later change).

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

## Project layout

```
.
├── .github/workflows/   # CI (lint/type-check/test) and Release (tag-triggered build)
├── src/
│   └── ynab_claude_connector/
│       ├── __main__.py        # runnable entry point (python -m ynab_claude_connector)
│       ├── server.py          # FastMCP server factory (MCP SDK usage lives here)
│       ├── tools.py           # tool implementations (currently: ping)
│       ├── config.py          # env-based, validated, immutable ServerConfig
│       └── logging_config.py  # logging setup
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
