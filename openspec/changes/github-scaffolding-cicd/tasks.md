## 1. Repository & Environment Setup

- [ ] 1.1 Run `git init`; create the default `main` branch
- [ ] 1.2 Add a Python `.gitignore` (venv, `__pycache__`, `dist/`, `.mypy_cache`, `.pytest_cache`, `*.egg-info`)
- [ ] 1.3 Create a virtual environment (`python -m venv .venv`) and document activation in notes for the README
- [ ] 1.4 Create the `src/ynab_claude_connector/` package directory with an empty `__init__.py` placeholder

## 2. Packaging & Tooling Configuration

- [ ] 2.1 Create `pyproject.toml` with PEP 621 metadata (name `ynab-claude-connector`, `requires-python = ">=3.11"`), build backend `hatchling`, and `dynamic = ["version"]` configured via `hatch-vcs` (tag-derived version) with the `src/` layout
- [ ] 2.2 Add dev dependencies (`pytest`, `pytest-cov`, `ruff`, `mypy`, `build`, `pre-commit`) via an optional-dependencies `dev` group
- [ ] 2.3 Configure `ruff` (lint + format) in `pyproject.toml`
- [ ] 2.4 Configure `mypy` (strict-ish, type hints required on public APIs) in `pyproject.toml`
- [ ] 2.5 Configure `pytest` in `pyproject.toml`: testpaths, `importlib` import mode, and coverage options including `--cov=ynab_claude_connector --cov-fail-under=90`
- [ ] 2.6 Create `.pre-commit-config.yaml` running `ruff` (lint + format) and `mypy` to mirror CI gates locally
- [ ] 2.7 Install the package in editable mode with dev extras (`pip install -e ".[dev]"`), install hooks (`pre-commit install`), and confirm tools run

## 3. Placeholder Behavior — TDD (Red → Green → Refactor)

- [ ] 3.1 RED: Write `tests/test_version.py` asserting the package version (read via `importlib.metadata.version("ynab-claude-connector")`, re-exported as `__version__`) is a valid SemVer string; run `pytest` and confirm it FAILS
- [ ] 3.2 RED: Add a test for one pure, type-hinted placeholder function (e.g. `package_name() -> str`) asserting its return value; run `pytest` and confirm it FAILS
- [ ] 3.3 GREEN: Implement `__version__` (sourced from `importlib.metadata`) and the placeholder pure function in `__init__.py` with full type hints; run `pytest` and confirm tests PASS
- [ ] 3.4 RED: Add edge-case tests (SemVer pre-release string like `0.2.0-rc.1` is accepted; version is non-empty / matches the pattern boundaries); run `pytest` and confirm they FAIL where appropriate
- [ ] 3.5 GREEN: Adjust the SemVer validation helper so edge-case tests PASS; run `pytest`
- [ ] 3.6 REFACTOR: Clean up for FP style (no mutable state, pure functions), ensure `ruff check`, `ruff format`, and `mypy` all pass; re-run `pytest` to confirm still green

## 4. Build Verification

- [ ] 4.1 Run `python -m build` and confirm an sdist (`.tar.gz`) and wheel (`.whl`) are produced under `dist/`
- [ ] 4.2 Install the built wheel into a fresh throwaway venv and confirm `import ynab_claude_connector` works (validates the `src/` layout / packaging)

## 5. CI Workflow (`.github/workflows/ci.yml`)

- [ ] 5.1 Create `ci.yml` triggered on `push` and `pull_request`
- [ ] 5.2 Add a build matrix over Python `3.11`, `3.12`, and `3.13`; steps: checkout (pinned, `fetch-depth: 0` so `hatch-vcs` sees tags) → setup-python with pip cache → install `.[dev]`
- [ ] 5.3 Add steps to run `actionlint`, `ruff check`, `mypy`, then `pytest` with coverage (`--cov-fail-under=90`) — the gate fails if any step fails
- [ ] 5.4 Set least-privilege `permissions: contents: read` and a `concurrency` group with `cancel-in-progress: true`
- [ ] 5.5 Validate the workflow YAML with `actionlint` locally before commit

## 6. Release Workflow (`.github/workflows/release.yml`)

- [ ] 6.1 Create `release.yml` triggered on `push` of tags matching `v*`
- [ ] 6.2 Add steps: checkout (`fetch-depth: 0` so `hatch-vcs` derives the version from the tag) → setup-python → `python -m build` → `actions/upload-artifact` for `dist/*`
- [ ] 6.3 Set least-privilege `permissions: contents: read`
- [ ] 6.4 Confirm a non-tag push does not match the trigger (review trigger filter)

## 7. Documentation

- [ ] 7.1 Write root `README.md`: project overview, setup (venv + `pip install -e ".[dev]"` + `pre-commit install`), how to run tests with coverage (`pytest`), how to build (`python -m build`)
- [ ] 7.2 Document the trunk-based branching model: `main` protected/releasable, PRs require passing CI, `vX.Y.Z` tag cuts a release, pre-release tags for experimental builds
- [ ] 7.3 Document the SemVer scheme (tag-derived via `hatch-vcs`, single source of truth), the 90% coverage floor, and the TDD (Red–Green–Refactor) workflow expectation

## 8. Final Verification

- [ ] 8.1 Run the full local gate: `pre-commit run --all-files` (ruff + mypy), `actionlint`, and `pytest` with `--cov-fail-under=90` — all green
- [ ] 8.2 Commit the baseline; (on push) confirm CI runs on a PR and passes
- [ ] 8.3 Push a `v0.1.0` tag and confirm the release workflow produces build artifacts
