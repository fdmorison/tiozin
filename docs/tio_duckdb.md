# tio_duckdb

`tio_duckdb` is the Tiozin provider family for DuckDB. It provides a runner, file inputs, SQL transforms, and file outputs for DuckDB-based pipelines.

> **Note:** `tio_duckdb` currently lives inside the `tiozin` core repository. In a future major version it will be extracted into its own independent package. Creating new provider families inside the core repository is not allowed.

## Installation

```bash
pip install tiozin[tio_duckdb]
```

## DuckdbRunner

Runs pipelines on DuckDB. Manages a `DuckDBPyConnection` during setup and closes it during teardown. By default, uses an in-memory database named after the job slug.

```yaml
runner:
  kind: DuckdbRunner
```

Persistent database:

```yaml
runner:
  kind: DuckdbRunner
  database: path/to/main.duckdb
```

### Properties

| Property | Default | Description |
|---|---|---|
| `database` | `:memory:<job_name>` | DuckDB database path, `:memory:`, or `:default:` |
| `read_only` | `false` | Open all databases in read-only mode |
| `attach` | `{}` | Map of alias to path for external databases |
| `extensions` | `[]` | DuckDB extensions to install and load during setup |
| `**options` | `-` | DuckDB config options passed to `duckdb.connect(config=...)` |

### Extensions

```yaml
runner:
  kind: DuckdbRunner
  extensions:
    - httpfs
    - spatial
```

Extensions are installed and loaded during `setup()`.

### Attaching external databases

```yaml
runner:
  kind: DuckdbRunner
  attach:
    staging: /data/staging.duckdb
    analytics: /data/analytics.duckdb
```

Attached databases are available by alias in SQL transforms:

```yaml
transforms:
  - kind: DuckdbSqlTransform
    name: from_staging
    query: SELECT * FROM staging.my_table
```

## DuckdbFileInput

Reads files into a DuckDB relation. Supports all formats DuckDB supports.

```yaml
inputs:
  - kind: DuckdbFileInput
    name: customers
    path: data/customers.csv
    format: csv
```

Tiozin provides convenience format aliases for DuckDB:

| Alias | Resolves to |
|---|---|
| `tsv` | `read_csv(delim='\t')` |
| `jsonl` | `read_ndjson()` |
| `txt` | `read_text()` |
| `auto_csv` | `read_csv_auto()` |
| `auto_json` | `read_json_auto()` |

By default, results are returned as a lazy relation. Use `mode` to register the result under the step name instead.

When `explode_filepath: true` is set, each row gains extra file-level columns: `dirpath`, `dirname`, `filepath`, `filename`, `filestem`, `filetype` (and `filesize` for text and blob formats).

Any unrecognized property is passed as a DuckDB reader option to the `read_<format>()` function.

### Properties

| Property | Required | Default | Description |
|---|---|---|---|
| `path` | yes | | Path or list of paths to read from |
| `format` | no | `parquet` | File format or Tiozin alias |
| `hive_partitioning` | no | `true` | Interpret `col=value/` partition directories |
| `union_by_name` | no | `true` | Merge schemas by column name across files |
| `explode_filepath` | no | `false` | Expand file path into semantic columns |
| `mode` | no | `relation` | How the result is registered: `relation`, `table`, `view`, `temp_table`, `temp_view`, `overwrite_table` |
| `**options` | no | `-` | DuckDB reader options passed to the `read_<format>()` function |

## DuckdbSqlTransform

Runs a DQL SQL query using DuckDB. Each input or prior transform result is automatically registered as a named view accessible by the step `name`.

```yaml
transforms:
  - kind: DuckdbSqlTransform
    name: filtered
    query: SELECT * FROM @self WHERE status = $status
    args:
      status: active
```

Use `@self` to reference the current input without knowing its name:

```yaml
transforms:
  - kind: DuckdbSqlTransform
    name: enriched
    query: |-
      SELECT c.name, o.total
      FROM customers c
      JOIN orders o ON c.id = o.customer_id

  - kind: DuckdbSqlTransform
    name: high_value
    query: SELECT * FROM @self WHERE total > 100
```

With multiple inputs:

- `@self` or `@self0`: first dataset
- `@self1`, `@self2`, ...: additional datasets

Named parameters use `$param_name` syntax:

```yaml
transforms:
  - kind: DuckdbSqlTransform
    name: filtered
    query: SELECT * FROM @self WHERE total > $min_total
    args:
      min_total: 500
```

Only `SELECT`-like queries are supported. DDL and DML (`CREATE`, `INSERT`, `UPDATE`, `DROP`, etc.) are not allowed and will raise an error. Use outputs for write operations.

### Properties

| Property | Required | Description |
|---|---|---|
| `query` | yes | DQL SQL query. Supports `@self` references and `$param` named parameters |
| `args` | no | Named parameter values for the query |

## DuckdbFileOutput

Writes a DuckDB relation to files. Output is always written to a directory, never to a single file.

```yaml
outputs:
  - kind: DuckdbFileOutput
    name: raw_customers
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/
    format: parquet
    mode: overwrite
```

With Hive-style partitioning:

```yaml
outputs:
  - kind: DuckdbFileOutput
    name: partitioned
    path: .output/lake/orders/
    format: parquet
    mode: overwrite
    partition_by:
      - country
      - date
```

Files are named `part-{i}-{uuid}.snappy` by default.

### Properties

| Property | Required | Default | Description |
|---|---|---|---|
| `path` | yes | | Target directory path (trailing `/` is added automatically) |
| `format` | no | `parquet` | Output format (`parquet`, `csv`, `json`, etc.) |
| `mode` | no | `append` | Write mode: `append` or `overwrite` |
| `partition_by` | no | `[]` | Columns to partition by (Hive-style) |
| `compression` | no | `snappy` | Compression codec |
| `**options` | no | `-` | Additional DuckDB writer options |

## Accessing the session

All `tio_duckdb` steps inherit from `DuckdbStepMixin`, which provides a `self.duckdb` shortcut to the active `DuckDBPyConnection`:

```python
# Shortcut (available in all tio_duckdb steps)
conn = self.duckdb  # DuckDBPyConnection

# Equivalent standard form
conn = self.context.runner.session  # DuckDBPyConnection
```

`self.duckdb` is the idiomatic way to access the connection inside DuckDB steps. Both forms are equivalent.
