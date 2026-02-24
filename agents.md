# Tiozin Agent Specification

This document defines how the agent must understand, extend, and
interact with the Tiozin Framework.

The agent must follow this document strictly.

------------------------------------------------------------------------

## 1. Domain Understanding

Tiozin Framework is a Python runtime framework for defining and
executing declarative data jobs.

It structures execution for:

-   Batch pipelines
-   Streaming pipelines
-   Machine learning pipelines

Execution semantics depend exclusively on the Runner implementation.

The Framework defines structure. The Runner defines runtime behavior.

The agent must never treat Tiozin Framework as:

-   An orchestrator
-   A scheduler
-   A DAG manager
-   A compute engine
-   A canonical abstraction layer over runtimes

Tiozin Framework runs inside orchestration systems.

------------------------------------------------------------------------

## 2. Public API Surface

Breaking changes are defined exclusively as changes to the public Python
API surface.

The public API is composed only of:

-   `tiozin/__init__.py`
-   `tiozin/utils/__init__.py`
-   `tiozin/family/tio_duckdb/__init__.py`
-   `tiozin/family/tio_kernel/__init__.py`
-   `tiozin/family/tio_spark/__init__.py`

Changes outside these modules are not breaking changes unless they alter
behavior exposed through them.

The agent must not introduce breaking changes without explicit
justification.

------------------------------------------------------------------------

## 3. Core Concepts

### 3.1 Tiozin Framework

Tiozin Framework is the runtime system responsible for:

-   Loading declarative YAML jobs
-   Discovering Tiozins via Python `entry_points`
-   Applying proxies
-   Activating Context
-   Coordinating execution

Tiozin Framework is not a plugin.

------------------------------------------------------------------------

### 3.2 Tiozin

A Tiozin is a pluggable execution unit.

Every Tiozin:

-   Belongs to a Tiozin Family
-   Is registered via Python `entry_points`
-   Is discoverable and loadable by the Framework
-   Is replaceable
-   Is composable

All executable components in the system are Tiozins.

------------------------------------------------------------------------

### 3.3 Tiozin Family

A Tiozin Family is a provider domain grouping related Tiozins.

Families:

-   Define a runtime domain
-   Publish compatible Tiozins
-   Are distributed independently

------------------------------------------------------------------------

### 3.4 Tio / Tia Provider

A provider package must:

-   Be prefixed with `tio_` or `tia_`
-   Register Tiozins via Python `entry_points`

Discovery MUST rely exclusively on `entry_points`.

------------------------------------------------------------------------

### 3.5 Tiozin Roles

Valid Tiozin roles:

-   Job
-   Runner
-   Input
-   Transform
-   Output
-   Registry

------------------------------------------------------------------------

## 4. Stateless Enforcement for Step Tiozins

The following roles MUST remain stateless:

-   Input
-   Transform
-   Output

They MUST NOT:

-   Store runtime objects
-   Open connections
-   Create sessions
-   Create loggers
-   Maintain mutable cached state
-   Use global singletons

They MUST:

-   Receive runtime dependencies from the Runner
-   Access Context via `self.context`

------------------------------------------------------------------------

## 5. Runner Responsibilities

Runner Tiozins:

-   Own runtime session lifecycle
-   Manage connections
-   Define execution mode
-   Run lazy execution plans.
-   Run eager execution plans.

State is allowed only in Runner and Registry implementations.

------------------------------------------------------------------------

## 6. Registry Responsibilities

Registry Tiozins provide structured metadata retrieval and registration.

Existing registry types:

-   JobRegistry
-   LineageRegistry
-   MetricRegistry
-   SchemaRegistry
-   SecretRegistry
-   SettingRegistry
-   TransactionRegistry

Registries are not Step Tiozins.

------------------------------------------------------------------------

## 7. Declarative YAML Constraints

YAML job definitions must:

-   Remain flat
-   Avoid unnecessary nesting
-   Avoid structural overengineering
-   Not encode runtime logic
-   Remain human-readable
-   Remain machine-generatable

------------------------------------------------------------------------

## 8. Complexity Boundaries

Complexity is allowed only inside:

-   Framework core implementation
-   Provider family implementations

It must never leak into:

-   Public API
-   Declarative YAML

------------------------------------------------------------------------

## 9. Agent Instructions — Writing Pull Requests

When generating a Pull Request, the agent must strictly follow:

    .github/pull_request_template.md

The agent must:

- Preserve the template exactly as written
- Respect all embedded instructions inside the template
- Maintain section order and formatting

The agent must not:

- Remove sections
- Add new sections
- Modify headings
- Alter formatting
- Bypass or ignore template comments

All PRs must be written in Markdown.

### PR Titles

PR titles are used to compose the changelog.

The agent must ensure titles are:

- Accurate
- Specific to the actual change
- Clear enough for a changelog reader to understand what changed without opening the PR

------------------------------------------------------------------------

## Test Agent

All test generation must follow:

    agents/test-agent.md

The test agent is responsible for:

- Writing unit and integration tests
- Following project test conventions
- Ensuring determinism and isolation

------------------------------------------------------------------------

## Docs Agent

All documentation generation must follow:

    agents/docs-agent.md

The docs agent is responsible for:

- Writing user guides and reference pages under `docs/`
- Verifying behavior against source code before documenting it
- Keeping the README index up to date

------------------------------------------------------------------------

## 11. Package Structure

### `tiozin/api`

Public-facing domain model.

-   `tiozin/api/metadata` — Manifest models for metadata retrieval or registration.
-   `tiozin/api/registries` — Contracts for Tiozins responsible by handling metadata.
-   `tiozin/api/runtime` — Contracts for Tiozins responsible by handling etl runtime.

### `tiozin/compose`

Internals used to build, mount or format objects like they were lego.

-   `tiozin/compose/assembly` — Holds classes implementing construction patterns.
-   `tiozin/compose/proxies` — Proxy system (TioProxyMeta, @tioproxy)
-   `tiozin/compose/templating` — Tiozin properties templating and overlay

### `tiozin/family`

Provider implementations shipped with the framework. Each subfolder is a Tiozin Family registered
via `[project.entry-points."tiozin.family"]` in `pyproject.toml`.

-   `tio_kernel` — Built-in baseline family
-   `tio_spark` — Apache Spark family
-   `tio_duckdb` — DuckDB family

### `tiozin/utils`

General-purpose utilities with no domain dependency. Helpers, IO,
runtime, and message formatting.

------------------------------------------------------------------------

## 12. Config Mirroring

`tiozin/config.py` and `tests/config.py` must stay in sync.

`tests/config.py` mirrors the same keys with hardcoded test values,
avoiding environment variable reads and external dependencies.

When adding or renaming a key in `tiozin/config.py`, the agent must
apply the same change to `tests/config.py`.

------------------------------------------------------------------------

## 13. Useful Commands Recap

The agent MUST use Makefile commands for local operations instead of
invoking tools directly.

  Purpose             Command
  ------------------- --------------------
  Clean artifacts     `make clean`
  Install deps        `make install`
  Install dev deps    `make install-dev`
  Format code         `make format`
  Lint check          `make check`
  Run tests           `make test`
  Build package       `make build`
  Deploy package      `make deploy`
  Install git hooks   `make hooks`

The agent must prefer these commands when instructing how to test,
clean, format, build, or deploy the project.
