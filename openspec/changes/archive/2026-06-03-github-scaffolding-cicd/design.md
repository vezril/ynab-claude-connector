## Context

This is the first change in the YNAB–Claude connector repository. There is currently no Git history, no package, and no automation. The connector will eventually authenticate to YNAB and expose budget data to Claude, but Feature 1 is purely the buildable, tested, CI-backed skeleton. The project mandates TDD (Red–Green–Refactor), functional-programming style, type hints, and clean code. The original spec proposed a `main` + `development` two-branch model but explicitly invited a better strategy.

## Goals / Non-Goals

**Goals:**
- A `pyproject.toml`-managed Python package that builds to sdist + wheel.
- GitHub Actions CI that lints, type-checks, and runs the test suite on every push and PR across a Python version matrix.
- A tag-driven release workflow that builds versioned artifacts following SemVer.
- A documented branching/release strategy and a README covering install/run/test.
- An end-to-end exercised pipeline: one trivial function with a test that goes red→green proves the harness works.

**Non-Goals:**
- No YNAB API calls, auth, or Claude connector endpoints (later features).
- No publishing to PyPI or a real package index (artifacts only; PyPI can be added later).
- No deployment of a running service — there is none yet.
- No coverage-threshold gating yet (kept simple; can tighten later).

## Decisions

### Decision 1: Branching model — trunk-based + SemVer tags (revise the original `main`/`development` split)
**Choice**: `main` is always releasable and protected. Work happens on short-lived feature branches that merge into `main` via PR (CI must pass). Releases are cut by pushing an annotated `vX.Y.Z` tag on `main`, which triggers the release workflow.
**Why over the original two-branch model**: A long-lived `development` branch for a solo/small project creates a permanent merge-debt between `development` and `main` and duplicates CI for little benefit. Trunk-based development with PR gates is the modern default, keeps `main` shippable continuously (DORA-aligned), and SemVer tags give precise, immutable release points. Pre-release/experimental builds are still expressed through SemVer pre-release tags (e.g. `v0.2.0-rc.1`) and per-PR CI artifacts — covering the "experimental builds" intent without a parallel branch.
**Alternatives considered**: (a) Git Flow `main`/`develop` — heavier, suits scheduled releases not continuous delivery. (b) Release branches `release/x.y` — useful once multiple major versions need maintenance; premature now. We document the trunk model in README and can graduate to release branches later.

### Decision 2: Packaging — `pyproject.toml` (PEP 621) with the `src/` layout
**Choice**: Single `pyproject.toml` declaring metadata, dependencies, and tool config; package under `src/ynab_claude_connector/`. Build backend: `hatchling`, with `hatch-vcs` providing a **dynamic, tag-derived version** (see Decision 6).
**Why**: PEP 621 is the standard, tool-agnostic metadata format. The `src/` layout prevents accidentally importing the package from the working directory instead of the installed one, which catches packaging bugs in CI.
**Alternatives**: Poetry/PDM — more features but extra lockfile tooling; not needed for a dependency-light project. Flat layout — simpler but error-prone for packaging tests.

### Decision 3: Tooling — ruff + mypy + pytest
**Choice**: `ruff` for lint+format, `mypy` for type checking (strict-ish), `pytest` for tests. All configured in `pyproject.toml`.
**Why**: Matches the toolkit's Python guidance — type hints everywhere, one obvious formatter/linter. Ruff is fast and consolidates flake8/isort/black. pytest is the de-facto standard and supports the TDD loop cleanly.

### Decision 4: CI structure — two workflows, least-privilege tokens, pinned actions
**Choice**:
- `ci.yml` on `push` and `pull_request`: matrix over Python `3.11`, `3.12`, `3.13` (see Decision 7), steps = checkout → setup-python (with pip cache) → install dev deps → `actionlint` (workflow lint) → `ruff check` → `mypy` → `pytest` with coverage. `permissions: contents: read`. `concurrency` cancels superseded runs.
- `release.yml` on `push: tags: ['v*']`: build sdist+wheel via `python -m build`, upload as a workflow artifact. `permissions: contents: read` (write/`id-token` added only if/when we publish).
**Why**: Separating gate (CI) from delivery (release) keeps each workflow single-purpose. Least-privilege `GITHUB_TOKEN`, action pinning, and concurrency control follow GitHub Actions security/efficiency best practices.
**Alternatives**: One combined workflow with `if:` guards — harder to read and reason about permissions; rejected.

### Decision 5: FP style for the skeleton code
**Choice**: The placeholder logic is a pure function with type hints (no side effects, no mutable state), e.g. a `version()`/simple pure helper, tested directly.
**Why**: Establishes the functional, type-hinted, testable pattern from line one so later features inherit it.

### Decision 6: Version source of truth — tag-derived via `hatch-vcs` (resolves Open Question 1)
**Choice**: The Git tag is the single source of truth for the version. `pyproject.toml` declares `dynamic = ["version"]` and uses `hatch-vcs` to derive the version from the latest `vX.Y.Z` tag at build time; the package exposes it at runtime via `importlib.metadata.version("ynab-claude-connector")`. Untagged commits get a deterministic development version (e.g. `0.1.dev3+g<sha>`).
**Why over a static version string**: A hardcoded `version = "0.1.0"` in `pyproject.toml` inevitably drifts from the release tag and forces a manual edit (and an easy-to-forget step) on every release. Deriving from the tag makes `v0.1.0` → wheel `0.1.0` automatic and impossible to desync, which is the modern best practice (`hatch-vcs`/`setuptools-scm`). It also makes the release workflow trivial — tag, then build.
**Alternatives considered**: (a) Static version — simplest but drift-prone; rejected. (b) `bump-my-version`/manual bump commits — adds a release chore and a second source of truth; rejected. **Trade-off**: tests must read the version dynamically (via `importlib.metadata`) rather than asserting a literal, and a shallow CI checkout needs `fetch-depth: 0` so tags are visible — both handled in tasks.

### Decision 7: CI quality gates — Python matrix, coverage gate, workflow lint, pre-commit (resolves Open Questions 2 & 3)
**Choice**:
- **Matrix**: test on Python `3.11`, `3.12`, and `3.13`, with `requires-python = ">=3.11"`. 3.11 is the supported floor (broad compatibility, still upstream-supported); 3.13 is the current stable target.
- **Coverage**: run `pytest` with `pytest-cov` and enforce `--cov-fail-under=90`. The skeleton is trivially covered by its TDD tests, so a 90% floor is free now and keeps later features honest without being brittle.
- **Workflow lint**: run `actionlint` as a CI step to catch workflow YAML/expression errors early.
- **Local parity**: add a `.pre-commit-config.yaml` wiring `ruff` (lint + format) and `mypy` so the same gates run before commit as in CI.
**Why**: These are cheap, high-value defaults. A coverage floor turns "tests pass" into "tests pass *and* cover the code," reinforcing the mandated TDD discipline. `actionlint` prevents broken-pipeline-from-a-typo churn. `pre-commit` shifts feedback left so contributors don't discover lint/type failures only after pushing. The matrix follows the "support the current CPython releases" convention without an excessive number of jobs.
**Alternatives considered**: Deferring all of these (the original plan) — would let untested code and workflow typos slip in during early features when the patterns are being set; chosen to adopt now while the surface is tiny and the cost is near zero. A hard 100% coverage gate — too brittle as real features add error-handling branches; 90% chosen as a pragmatic floor.

## Risks / Trade-offs

- **Risk: Trunk-based model deviates from the written spec's `main`/`development`.** → Mitigation: Documented and justified here and in the README; the spec explicitly permitted a better strategy. Reversible — a `development` branch can be added later with no code change.
- **Risk: Workflows can't run until the repo is on GitHub.** → Mitigation: YAML is validated locally (e.g. `actionlint` optional / schema review) and exercised on first push; the README documents the push step.
- **Risk: Version source drift** (tag `v1.2.3` vs package version). → Mitigation: Resolved by Decision 6 — the tag is the single source via `hatch-vcs`; there is no second version string to drift.
- **Risk: `hatch-vcs` sees no version on a shallow CI checkout.** → Mitigation: use `actions/checkout` with `fetch-depth: 0` so tags are available; tests read the version via `importlib.metadata`, which works from the installed distribution.
- **Risk: Python matrix flakiness / slow CI.** → Mitigation: pip caching keyed on `pyproject.toml` hash; matrix limited to three current versions (3.11–3.13).
- **Trade-off: 90% coverage floor** can occasionally block a legitimately hard-to-cover branch. → Accepted; 90% (not 100%) leaves slack, and the floor can be tuned per-module later via `pyproject.toml`.

## Migration Plan

1. `git init`, create the package, configs, tests, workflows, README; commit as the initial baseline.
2. Create the GitHub repo, push `main`, enable branch protection requiring the `ci` check.
3. Open a PR from a feature branch to confirm CI runs on PRs (red→green proven by the placeholder test).
4. Tag `v0.1.0` to confirm the release workflow produces artifacts.
- **Rollback**: This is additive scaffolding; reverting is deleting the change. No runtime to roll back.

## Resolved Decisions (formerly Open Questions)

- **Version source of truth** → tag-derived via `hatch-vcs` (Decision 6). The Git `vX.Y.Z` tag is authoritative; the package reads its version through `importlib.metadata`. No static version string is maintained.
- **Python version matrix** → `3.11`, `3.12`, `3.13`, with `requires-python = ">=3.11"` (Decision 7). 3.11 is the supported floor; 3.13 is the current stable target. New CPython releases (e.g. 3.14) can be appended to the matrix as they stabilize.
- **`actionlint` + coverage threshold** → adopted now, not deferred (Decision 7). CI runs `actionlint`; `pytest` enforces `--cov-fail-under=90`; a `.pre-commit-config.yaml` mirrors the ruff/mypy gates locally.

No open questions remain; the change is ready to implement.
