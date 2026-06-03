## Why

The YNAB–Claude connector has no repository structure, no build tooling, and no automated quality gates yet. Before any YNAB or Claude integration code is written, we need a versioned Python project with CI/CD that runs tests on every change — this is the foundation that makes the required TDD workflow enforceable and makes every later feature shippable.

## What Changes

- Add a Git repository layout for a `src/`-style Python package (working name `ynab_claude_connector`) managed via `pyproject.toml`.
- Adopt a **trunk-based branching model with SemVer release tags** (revised from the original `main`/`development` proposal — see Design for rationale): `main` is always releasable; short-lived feature branches merge via PR; releases are cut by pushing a `vX.Y.Z` tag.
- Add a GitHub Actions **CI workflow** that runs on pushes and pull requests: install deps, lint (ruff), type-check (mypy), and run the test suite (pytest) across a Python version matrix.
- Add a GitHub Actions **release workflow** triggered by `v*` tags that builds the package (sdist + wheel) and publishes it as a versioned build artifact.
- Add baseline tooling config (ruff, mypy, pytest) and a placeholder package with one trivial, tested function so the pipeline is exercised end-to-end (red→green).
- Add a root `README.md` documenting how to install, run, and test the project, plus the branching/release strategy.

This change covers **Feature 1** and the buildable-skeleton portion of **Feature 2**; no YNAB or Claude API code is introduced here.

## Capabilities

### New Capabilities
- `project-scaffolding`: The Python package layout, `pyproject.toml` packaging metadata, tooling configuration (ruff/mypy/pytest), and the documented branching + SemVer release strategy.
- `ci-pipeline`: The GitHub Actions continuous-integration workflow (lint, type-check, test matrix on push/PR) and the tag-triggered release/build workflow producing versioned artifacts.

### Modified Capabilities
<!-- None — this is the first change; no existing specs. -->

## Impact

- **New files**: `pyproject.toml`, `src/ynab_claude_connector/__init__.py`, `tests/`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `.gitignore`, `README.md`, `ruff`/`mypy`/`pytest` config (in `pyproject.toml`).
- **Dependencies (dev)**: `pytest`, `pytest-cov`, `ruff`, `mypy`, `build`, `pre-commit`. Build backend `hatchling` + `hatch-vcs` (tag-derived version). `actionlint` runs in CI. No runtime dependencies yet.
- **Systems**: GitHub repository, GitHub Actions CI/CD. Requires the repo to be pushed to GitHub for workflows to run.
- **No production runtime impact** — there is no deployed service yet; the artifact is a buildable Python package.
