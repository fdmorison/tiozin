# Contributing

Tiozin is a runtime framework for defining and executing modular data jobs. Contributors extend it by adding new families, new Tiozins inside existing families, or fixes to the core. This guide covers the local workflow: setting up the repo, running tests, checking style, and preparing a pull request.

## Prerequisites

Install the following tools before working on Tiozin:

- Python 3.11 or later.
- [uv](https://docs.astral.sh/uv/) version 0.8.1 or later.
- Git.
- Make.

## Install Development Dependencies

```bash
make install-dev
```

To install only runtime dependencies (without test tooling or pre-commit hooks), run `make install` instead.

## Run the Test Suite

Run the full suite with:

```bash
make test
```

Tests are split across two trees:

- `tests/unit/` mirrors the structure of `tiozin/`. Each module under `tiozin/` has a sibling test module ending in `_test.py`.
- `tests/integration/` contains tests that depend on external services or full pipelines. Some integration tests rely on [Testcontainers](https://testcontainers.com/), so Docker must be running locally to execute them.

When writing new tests, ask Claude to create or review them. The `tester` agent enforces the project testing conventions.

## Format and Check Style

Format and auto-fix code:

```bash
make format
```

Verify style without modifying files:

```bash
make check
```

The pre-commit hook installed by `make install-dev` runs the same checks on every commit. CI runs `make check` as well, so passing it locally is a prerequisite for a green pull request.

## Build the Package

Produce a distributable wheel and sdist:

```bash
make build
```

Artifacts land in `dist/`. Use `make clean` to remove `dist/`, `build/`, and cache directories.

## Where Code Lives

- `tiozin/api/` holds the core abstractions (base classes, contracts, context types).
- `tiozin/family/` holds the built-in provider families: `tio_kernel`, `tio_spark`, `tio_duckdb`.
- `tiozin/compose/` holds code that assembles jobs from definitions.
- `docs/` holds concept pages, reference pages, and user guides.
- `examples/` holds runnable job definitions and schemas used in documentation.
- `tests/` holds unit and integration tests mirroring the package layout.

## Configuration Mirrors

Two pairs of files must stay in sync:

- `tiozin/env.py` and `tests/env.py`
- `tiozin/config.py` and `tests/config.py`

Update both sides of the pair in the same change.

## AI Agents

The project includes Claude Code agents and skills for common tasks. Install [Claude Code](https://claude.ai/code) to use them from the repository root.

- To create a new Tiozin or family, use the `creating-plugins` skill. For concepts and conventions, see [`docs/extending/tiozins.md`](extending/tiozins.md). For creating a new family, see [`docs/extending/families.md`](extending/families.md).
- To write or review tests, ask Claude. The `tester` agent enforces the project testing conventions.
- To write or update documentation, ask Claude. The `technical-writer` agent enforces the project doc conventions.
- To write a pull request description, ask Claude to open a PR. The `pr-writer` agent handles formatting.

## Pull Request Expectations

Before opening a pull request, confirm the following:

1. `make check` passes locally.
2. `make test` passes locally, including the coverage threshold.
3. New behavior is covered by a test under `tests/unit/` or `tests/integration/`.
4. Documentation under `docs/` is updated when adding or changing user-facing behavior.
5. Breaking changes are clearly flagged in the pull request description.
6. The pull request follows the project template at [`.github/pull_request_template.md`](../.github/pull_request_template.md).

The pre-commit hook catches most style issues at commit time. CI runs `make check` and `make test`. A pull request that fails either step will not be merged until the failure is resolved.
