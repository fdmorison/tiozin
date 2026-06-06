# Contributing

Tiozin is a runtime framework for defining and executing modular data jobs. Contributors extend it by adding new families, new Tiozins inside existing families, or fixes to the core. This guide covers the local workflow: setting up the repo, running tests, checking style, and preparing a pull request.

## Prerequisites

Install the following tools before working on Tiozin:

- Python 3.11 or later.
- [uv](https://docs.astral.sh/uv/) version 0.8.1 or later.
- Git.
- Make.
- [Claude Code](https://claude.ai/code) (optional, required for AI agents and skills).

## AI Assistance

The project ships [Claude Code](https://claude.ai/code) agents and skills that enforce project conventions automatically.

- `tester`: writes and reviews tests following the project testing conventions.
- `technical-writer`: writes and updates documentation following the project doc conventions.
- `pr-writer`: writes pull request descriptions following the project PR template.
- `creating-plugins`: creates Tiozins and families.

## Where Code Lives

**Packages**

- `tiozin/api/` holds the core abstractions (base classes, contracts, context types).
- `tiozin/family/` holds the built-in provider families: `tio_kernel`, `tio_spark`, `tio_duckdb`.
- `tiozin/compose/` holds code that assembles jobs from definitions.
- `tests/` holds unit and integration tests mirroring the package layout.

**Configuration**

- `tiozin/env.py` reads environment variables from multiple sources (system, user, container, project) and exposes them as named constants.
- `tiozin/config.py` builds application configuration from `env` values and other computed constants.

**Resources**

- `docs/` holds concept pages, reference pages, and user guides.
- `examples/` holds runnable job definitions and schemas used in documentation.
- `tiozin.example.yaml` is a template for configuring registries and runtime defaults.

## Set Up the Repo

Install dependencies and pre-commit hooks:

```bash
make install-dev
```

To install only runtime dependencies, run `make install` instead.

## Testing

Run the full suite with:

```bash
make test
```

Tests are split across two trees:

- `tests/unit/` mirrors the structure of `tiozin/`. Each module under `tiozin/` has a sibling test module ending in `_test.py`.
- `tests/integration/` contains tests that depend on external services or full pipelines. Some integration tests rely on [Testcontainers](https://testcontainers.com/), so Docker must be running locally to execute them.

## Code Style

Format and auto-fix code:

```bash
make format
```

Verify style without modifying files:

```bash
make check
```

A pre-commit hook is installed by `make install-dev` and runs on every commit.

## Releases

Every merge to `main` that touches `tiozin/` or `pyproject.toml` triggers [release-please](https://github.com/googleapis/release-please), which maintains an open release PR that accumulates changes and bumps the version based on conventional commits. Merging the release PR publishes the package to PyPI and creates a GitHub release.

## Pull Request Expectations

Before opening a pull request, confirm the following:

1. `make check` passes locally.
2. `make test` passes locally, including the coverage threshold.
3. New behavior is covered by a test under `tests/unit/` or `tests/integration/`.
4. Documentation under `docs/` is updated when adding or changing user-facing behavior.
5. Breaking changes are clearly flagged in the pull request description.
6. The pull request follows the project template at [`.github/pull_request_template.md`](../.github/pull_request_template.md).
