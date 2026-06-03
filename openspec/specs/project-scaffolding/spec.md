# project-scaffolding Specification

## Purpose
Defines the Python packaging, tooling, versioning, branching, and documentation requirements that scaffold the project.

## Requirements

### Requirement: Python package builds from pyproject.toml
The project SHALL be a Python package defined by a single `pyproject.toml` (PEP 621) using a `src/` layout, and SHALL build to both an sdist and a wheel via a standard build frontend (`python -m build`).

#### Scenario: Clean build produces distributions
- **WHEN** a developer runs `python -m build` in a clean checkout
- **THEN** a `.tar.gz` sdist and a `.whl` wheel are produced under `dist/` with no errors

#### Scenario: Installed package is importable
- **WHEN** the built wheel is installed into a fresh virtual environment
- **THEN** `import ynab_claude_connector` succeeds and exposes the package version

#### Scenario: Edge case — build fails on malformed metadata
- **WHEN** `pyproject.toml` is missing a required field (e.g. `name` or `version`)
- **THEN** `python -m build` exits non-zero with an error identifying the missing metadata, rather than producing an artifact

#### Scenario: Edge case — src layout prevents shadow imports
- **WHEN** tests run against the installed/packaged module rather than the working-directory source
- **THEN** importing the package resolves to the installed distribution, so a packaging omission (a module not included in the wheel) is detected as an ImportError in CI

### Requirement: Tooling configuration is centralized and enforces style and types
The project SHALL configure `ruff` (lint + format), `mypy` (type checking), and `pytest` in `pyproject.toml`, and all first-party code SHALL pass these checks with type hints on public functions.

#### Scenario: Lint and type checks pass on conforming code
- **WHEN** a developer runs `ruff check .` and `mypy` on the source tree
- **THEN** both commands exit zero with no reported violations

#### Scenario: Edge case — untyped public function is rejected
- **WHEN** a public function is added without type hints and `mypy` runs in its configured (strict) mode
- **THEN** `mypy` exits non-zero and reports the missing annotation

### Requirement: Versioning follows Semantic Versioning with the Git tag as the single source of truth
Releases SHALL be identified by Semantic Versioning `MAJOR.MINOR.PATCH` strings. The package version SHALL be derived from the Git release tag (`vX.Y.Z`) at build time via `hatch-vcs` — there SHALL NOT be a separately maintained static version string — and SHALL be readable at runtime via package metadata.

#### Scenario: Package reports a valid SemVer version from metadata
- **WHEN** the package version is read via `importlib.metadata.version("ynab-claude-connector")`
- **THEN** it returns a valid SemVer-compatible version string and does not require a hardcoded `version =` field in `pyproject.toml`

#### Scenario: Tagged build matches the tag
- **WHEN** the package is built from a checkout whose latest tag is `v0.1.0`
- **THEN** the resulting distribution's version is `0.1.0` (no manual edit required to keep them in sync)

#### Scenario: Edge case — untagged commit yields a deterministic development version
- **WHEN** the package is built from a commit that has no release tag
- **THEN** `hatch-vcs` produces a development version (e.g. `0.1.dev3+g<sha>`) rather than failing the build

#### Scenario: Edge case — pre-release version is valid SemVer
- **WHEN** an experimental build is tagged with a pre-release identifier such as `v0.2.0-rc.1`
- **THEN** the derived version `0.2.0-rc.1` is accepted as valid SemVer and ordered before the corresponding `0.2.0` final release

### Requirement: Branching and release strategy is documented
The repository SHALL document a trunk-based branching model in which `main` is always releasable, changes merge via pull request with passing CI, and releases are cut by pushing a `vX.Y.Z` tag.

#### Scenario: README describes the workflow
- **WHEN** a contributor reads `README.md`
- **THEN** it states that `main` is protected and releasable, that feature work merges via PR after CI passes, and that a `vX.Y.Z` tag triggers a release

#### Scenario: Edge case — experimental builds without a long-lived dev branch
- **WHEN** a contributor needs an experimental/pre-release build
- **THEN** the documentation directs them to use a SemVer pre-release tag (e.g. `v0.2.0-rc.1`) and/or per-PR CI artifacts rather than a separate `development` branch

### Requirement: README documents install, run, and test
The repository SHALL include a root `README.md` explaining how to set up the environment, install the package, and run the test suite.

#### Scenario: Following the README sets up a working environment
- **WHEN** a new developer follows the README setup steps from a clean clone
- **THEN** they can create a virtual environment, install dev dependencies, and run `pytest` to a passing result
