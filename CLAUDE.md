# Claude Instructions — Tiozin

## What is Tiozin

Tiozin is a Python runtime framework for defining and executing declarative data jobs (batch, streaming, ML). It loads YAML job definitions, discovers plugins via `entry_points`, and coordinates execution.

**YOU MUST NOT treat Tiozin as:** an orchestrator, scheduler, DAG manager, or compute engine. It can run standalone or inside orchestration systems, but it is not one.

---

## Commands

Use Makefile commands for all standard operations.

| Purpose          | Command            |
|------------------|--------------------|
| Run tests        | `make test`        |
| Format code      | `make format`      |
| Lint check       | `make check`       |
| Install deps     | `make install`     |
| Install dev deps | `make install-dev` |
| Build package    | `make build`       |
| Deploy           | `make deploy`      |

During development, prefer running only the relevant test file: `uv run pytest -vvv tests/path/to/file_test.py`

Run `make test` (full suite) only when: completing a task, validating a refactor that touches multiple modules, or confirming no regressions before a PR.

---

## Code Rules (IMPORTANT)

- Never define functions outside of classes — use `@staticmethod` on the relevant class instead
- Never use `# noqa` to suppress linter errors — fix the code
- Never use `| None` in parameter or return type annotations
- Use single backticks in docstrings, never RST double backticks

---

## Behavior Rules (IMPORTANT)

- Never overwrite a file the user has manually edited — user edits are authoritative
- Do exactly what was asked — no extra fixtures, helpers, or abstractions

---

## Public API

**Breaking changes** are defined only as changes to these files:

- `tiozin/__init__.py`
- `tiozin/utils/__init__.py`
- `tiozin/family/tio_duckdb/__init__.py`
- `tiozin/family/tio_kernel/__init__.py`
- `tiozin/family/tio_spark/__init__.py`

---

## Stateless Enforcement

`Input`, `Transform`, and `Output` Tiozins must be stateless. They must not open connections, store runtime objects, create loggers, or maintain mutable state. They receive runtime dependencies from the Runner via `self.context`.

---

## Package Structure

| Path                   | Purpose                                             |
|------------------------|-----------------------------------------------------|
| `tiozin/api/`          | Public domain model (metadata, registries, runtime) |
| `tiozin/compose/`      | Assembly, proxies, templating internals             |
| `tiozin/family/`       | Built-in provider families (kernel, spark, duckdb)  |
| `tiozin/utils/`        | General-purpose utilities, no domain dependency     |
| `tiozin/config.py`     | Config keys — must stay in sync with `tests/config.py` |

---

## Config Sync

`tiozin/config.py` and `tests/config.py` must stay in sync. When adding or renaming a key in either file, apply the same change to the other.

---

## Agent Specs

When writing tests, follow @agents/test-agent.md and @agents/test-rules.md.
When writing documentation, follow @agents/docs-agent.md.
When writing pull requests, follow @agents/pr-agent.md.
