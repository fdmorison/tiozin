---
name: creating-plugins
description: Creates Tiozin classes (Input, Transform, CoTransform, Output, Runner, and Registry). Use when asked to create a Tiozin, family, plugin, data source, transform, sink, or registry.
user-invocable: true
---

## Rules

- Family packages must be prefixed with `tio_` or `tia_`
  - ✔ `tio_john`, `tia_cassandra`
  - ✘ `john`, `my_plugins`
- Add `setup` only when preparation is required before the lifecycle method runs
  - ✔ acquire a resource, adjust a target schema, create a directory
- Add `teardown` only when cleanup is required afterward
- Use `CoTransform` instead of `Transform` when more than one upstream input is required
- Always call `super().__init__(**options)`
- `Input`, `Transform`, and `Output` must be stateless:
  - `__init__` may store constructor arguments
  - lifecycle methods must not accumulate state between calls
- Use `self.info()`, `self.warning()`, `self.error()` for logging
- Register every new class in the family's root `__init__.py`
- Class name: `{FamilyName}{Purpose}{Role}` in PascalCase
  - ✔ `JohnS3Input`, `JohnFileOutput`, `JohnSqlTransform`
  - ✘ `S3Input`, `inputFile`, `John_SQL_Transform`
- Class name: avoid repeating words already in the role name
  - ✔ `GoogleSecretRegistry`
  - ✘ `GoogleSecretManagerSecretRegistry`
- Validate required arguments with `RequiredArgumentError.raise_if_missing`:
  ```python
  RequiredArgumentError.raise_if_missing(
      path=path,
  )
  ```
- Every plugin must have a class-level docstring; follow [docstrings.md](rules/docstrings.md)
- A family must be a Python package (directory with `__init__.py`), never a single class or module

## Policies

- When the family is a project files go at `{family}/{role}s/{purpose}_{role}.py`
  - ✔ `tio_john/inputs/s3_input.py`
  - ✘ `tio_john/s3_input.py`
- When the family is a package inside a larger project, files go at `{project root}/{family}/{role}s/{purpose}_{role}.py`
  - ✔ `data_platform_utils/tio_john/inputs/s3_input.py`
  - ✘ `data_platform_utils/tio_john/s3_input.py`
- When the family is part of the Tiozin core, files go at `tiozin/family/{family}/{role}s/{purpose}_{role}.py`
  - ✔ `tiozin/family/tio_kernel/inputs/s3_input.py`
  - ✘ `tio_kernel/inputs/s3_input.py`
- Use `as_list` from `tiozin.utils` when a parameter can be a single value or a list
  - ✔ `self.sources = as_list(sources)` with type hint `str | list[str]`
  - ✘ `self.sources = sources`
- Declare OpenLineage datasets through `external_datasets`
  - Override on Inputs and Outputs
  - Override on Transforms only when accessing external datasets
  - Use a `Dataset` factory when available; otherwise see https://openlineage.io/docs/spec/naming/

## Additional Context

- When creating:
  - an Input, see [input.md](examples/input.md)
  - a single-input Transform, see [transform.md](examples/transform.md)
  - a multi-input Transform, see [transform.md](examples/transform.md)
  - an Output, see [output.md](examples/output.md)
  - a Runner, see [runner.md](examples/runner.md)
  - a Registry, see [registry.md](examples/registry.md)
- When adding to the DuckDB family, see [duckdb-bases.md](examples/duckdb-bases.md)
- When adding to the Spark family, see [spark-bases.md](examples/spark-bases.md)
- When creating a new family, use `tio_duckdb` or `tio_spark` as structural reference
- When declaring `external_datasets`, see [datasets.md](rules/datasets.md) for available factories

## Workflow

1. Identify the role (Input, Transform, CoTransform, Output, Runner, Registry).
2. Identify the family: existing or new.
3. Create the plugin file.
4. Implement the required method and declare `external_datasets` when applicable.
5. Register the class in the family's `__init__.py`.
6. If the family is new, register it as an entry point in `pyproject.toml`:
   ```toml
   [project.entry-points."tiozin.family"]
   tio_john = "tio_john"
   tia_cassandra = "data_platform_utils.tia_cassandra"
   ```
7. Delegate test writing to the `tester` agent.
8. Self-review: check for unnecessary methods, parameters, or abstractions not required by the task.
9. Run `make format`.
