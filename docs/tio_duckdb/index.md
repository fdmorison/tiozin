# tio_duckdb

`tio_duckdb` is the Tiozin provider family for DuckDB. It runs pipelines on a local DuckDB connection. Every step result is automatically available as a named relation for downstream SQL queries. The family is designed for single-node, in-memory or file-based workloads.

> **Note:** `tio_duckdb` currently lives inside the `tiozin` core repository. In a future major version it will be extracted into its own independent package. Creating new provider families inside the core repository is not allowed.

## Installation

```bash
pip install tiozin[tio_duckdb]
```

## How data flows through steps

Every step in `tio_duckdb` produces a `DuckDBPyRelation`. After each step runs, the framework automatically registers that relation as a named temporary view using the step's slug as the view name. The slug is the slugified version of the step's `name` field: lowercase, with spaces and special characters replaced by underscores.

```yaml
inputs:
  - kind: DuckdbFileInput
    name: raw customers      # slug: raw_customers
    path: data/customers.csv

transforms:
  - kind: DuckdbSqlTransform
    name: filtered
    query: SELECT * FROM raw_customers WHERE status = 'active'
    # raw_customers is available because the input was registered under that slug
```

This view registration happens at the framework level for all inputs and transforms. No step needs to do it explicitly.

## Components

- [DuckdbRunner](runner.md)
- [DuckdbFileInput](file-input.md)
- [DuckdbSqlTransform](sql-transform.md)
- [DuckdbFileOutput](file-output.md)
- [DuckdbPostgresOutput](postgres-output.md)

To implement a custom Input, Transform, or Output from scratch, see [Creating Pluggable Tiozins](../extending/tiozins.md).

## Accessing the connection

When writing a custom step in `tio_duckdb`, use `self.duckdb` to access the active DuckDB connection. `self` here refers to the step instance: any class that extends `DuckdbTransform`, `DuckdbInput`, or `DuckdbOutput`.

```python
def transform(self, data: DuckDBPyRelation) -> DuckDBPyRelation:
    sql = f"SELECT * FROM {data.alias} WHERE amount > 100"
    return self.duckdb.sql(sql)
```

This connection is the one opened and managed by the runner. It is shared across all steps in the pipeline, so every step reads from and writes to the same DuckDB session. Do not open a new connection with `duckdb.connect()` inside a step: that would create an isolated session with no access to the data registered by other steps.

`self.duckdb` is shorthand for:

```python
conn = self.context.runner.session  # DuckDBPyConnection
```

Both are equivalent. `self.duckdb` is the idiomatic form.
