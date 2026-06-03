## ADDED Requirements

### Requirement: CI runs quality gates on pushes and pull requests
The repository SHALL include a GitHub Actions CI workflow that triggers on `push` and `pull_request` and runs linting (`ruff`), type checking (`mypy`), and the test suite (`pytest`) across a matrix of Python `3.11`, `3.12`, and `3.13`.

#### Scenario: CI passes for conforming changes
- **WHEN** a commit that lints cleanly, type-checks, and has passing tests is pushed or opened as a PR
- **THEN** the CI workflow runs all jobs in the Python matrix and reports a successful (green) status check

#### Scenario: CI fails when a test fails
- **WHEN** a change introduces a failing test
- **THEN** the `pytest` step exits non-zero and the workflow reports a failing status check that can block merge

#### Scenario: Edge case — lint or type error fails the build before tests pass
- **WHEN** a change has passing tests but a `ruff` or `mypy` violation
- **THEN** the corresponding step fails and the overall workflow is marked failed, so style/type regressions cannot merge

#### Scenario: Edge case — failure isolated to one matrix entry
- **WHEN** the suite passes on one Python version but fails on another in the matrix
- **THEN** the failing matrix job reports failure and the workflow's overall status is failed, surfacing the version-specific break

### Requirement: CI enforces a test coverage threshold
The CI test step SHALL measure code coverage (`pytest-cov`) and SHALL fail when coverage of the first-party package falls below 90%.

#### Scenario: Coverage at or above the threshold passes
- **WHEN** the test run covers at least 90% of `ynab_claude_connector`
- **THEN** the `pytest` step succeeds

#### Scenario: Edge case — coverage below the threshold fails the build
- **WHEN** code is added that drops package coverage below 90% (e.g. an untested branch)
- **THEN** `pytest --cov-fail-under=90` exits non-zero and the CI status is failed

### Requirement: CI lints workflow definitions
The CI workflow SHALL run `actionlint` to validate the GitHub Actions workflow files themselves.

#### Scenario: Valid workflows pass the lint step
- **WHEN** the workflow YAML and expressions are well-formed
- **THEN** the `actionlint` step succeeds

#### Scenario: Edge case — malformed workflow is caught
- **WHEN** a workflow file contains an invalid expression or unknown key
- **THEN** the `actionlint` step exits non-zero and reports the offending location before the broken workflow can be relied upon

### Requirement: Local pre-commit hooks mirror CI gates
The repository SHALL provide a `.pre-commit-config.yaml` that runs `ruff` (lint + format) and `mypy` so contributors get the same gates locally that CI enforces.

#### Scenario: Pre-commit blocks a non-conforming commit
- **WHEN** a contributor with hooks installed attempts to commit code with a lint or type violation
- **THEN** the pre-commit run fails and blocks the commit until the issue is fixed

### Requirement: CI workflow follows security and efficiency best practices
The CI workflow SHALL use a least-privilege `GITHUB_TOKEN` (`permissions: contents: read`), pin actions to known versions, cache dependencies, and cancel superseded runs via a concurrency group.

#### Scenario: Token is least-privilege by default
- **WHEN** the CI workflow runs
- **THEN** its `GITHUB_TOKEN` has read-only `contents` permission and no write scopes beyond what a step explicitly requires

#### Scenario: Edge case — superseded run is cancelled
- **WHEN** a second push to the same branch occurs while a prior CI run is still in progress
- **THEN** the in-progress run for that branch is cancelled by the concurrency group instead of both running to completion

### Requirement: Tagged releases build versioned artifacts
The repository SHALL include a GitHub Actions release workflow triggered by pushing a `v*` tag that builds the package (sdist + wheel) and uploads the distributions as a workflow artifact.

#### Scenario: Pushing a SemVer tag produces build artifacts
- **WHEN** an annotated tag matching `v*` (e.g. `v0.1.0`) is pushed to `main`
- **THEN** the release workflow builds the sdist and wheel and uploads them as a downloadable workflow artifact

#### Scenario: Non-tag pushes do not trigger a release
- **WHEN** a normal commit is pushed to a branch without a `v*` tag
- **THEN** the release workflow does not run

#### Scenario: Edge case — release build fails on a broken package
- **WHEN** a tag is pushed but the package fails to build (e.g. invalid metadata or import error)
- **THEN** the release workflow fails, no artifact is published, and the failure is visible on the tag's checks
