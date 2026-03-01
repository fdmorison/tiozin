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
    query: SELECT * FROM @data WHERE status = $status
    args:
      status: active
```

Use `@data` to reference the current input without knowing its name:

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
    query: SELECT * FROM @data WHERE total > 100
```

With multiple inputs:

- `@data` or `@data0`: first dataset
- `@data1`, `@data2`, ...: additional datasets

Named parameters use `$param_name` syntax:

```yaml
transforms:
  - kind: DuckdbSqlTransform
    name: filtered
    query: SELECT * FROM @data WHERE total > $min_total
    args:
      min_total: 500
```

Only `SELECT`-like queries are supported. DDL and DML (`CREATE`, `INSERT`, `UPDATE`, `DROP`, etc.) are not allowed and will raise an error. Use outputs for write operations.

### Properties

| Property | Required | Description |
|---|---|---|
| `query` | yes | DQL SQL query. Supports `@data` references and `$param` named parameters |
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

## DuckdbPostgresOutput

Writes data from a DuckDB pipeline into a PostgreSQL table. Supports four write modes, automatic schema evolution, and SQL hooks that run before and after each write.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    name: save_customers
    table: customers
```

To connect to a specific Postgres instance, set the connection properties directly in the job:

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    name: save_customers
    table: customers
    host: my-postgres-host
    port: 5432
    database: analytics
    user: etl_user
    password: "{{ ENV.PGPASSWORD }}"
```

You can also configure the connection via environment variables (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGSCHEMA`). Properties set in the job always take priority.

### Write modes

The `mode` property controls how data is written to the target table on each run. All modes create the table automatically if it does not exist yet.

**append** (default): Inserts incoming rows into the table. Does not deduplicate: running twice on the same data produces twice as many rows.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: events
    mode: append
```

**truncate**: Clears the table before each write, then inserts incoming rows. Every run replaces the table content with the current batch. The table structure is preserved between runs.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: events
    mode: truncate
```

**overwrite**: Recreates the table on every run. Each run produces a table whose structure matches the current batch exactly. Check constraints, column defaults, and outbound foreign keys are preserved. The primary key is re-added automatically if `primary_key` is set. Other indexes are not: recreate them via `post_pgsql`.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: events
    mode: overwrite
    primary_key: id
    post_pgsql:
      - CREATE INDEX IF NOT EXISTS idx_events_date ON public.events(date)
```

**merge**: Upserts rows by primary key. Rows that already exist are updated; rows that do not exist are inserted. Incoming `NULL` values do not overwrite existing values. Requires `primary_key`.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: customers
    mode: merge
    primary_key: id
```

Use `merge_key` when the conflict key is different from the primary key:

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: customers
    mode: merge
    primary_key: id
    merge_key: external_id
```

### Schema evolution

All modes detect new columns automatically. When the incoming batch has a column the target table does not, that column is added to the table before the write runs. Existing rows get `NULL` for the new column.

### Hooks

`pre_pgsql` runs SQL on PostgreSQL before the write strategy executes, but after schema evolution has already run. `post_pgsql` runs after the write completes. Both accept a single statement or a list. Common uses: dropping dependent views before an overwrite, granting permissions and recreating views after a write.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: events
    mode: overwrite
    primary_key: id
    pre_pgsql:
      - DROP VIEW IF EXISTS public.vw_events_summary
    post_pgsql:
      - CREATE INDEX IF NOT EXISTS idx_events_date ON public.events(date)
      - GRANT SELECT ON public.events TO reporter
      - CREATE VIEW public.vw_events_summary AS SELECT date, count(*) FROM public.events GROUP BY date
```

### Properties

#### Connection

| Property | Required | Default | Description |
|---|---|---|---|
| `host` | no | `$PGHOST` (`localhost`) | PostgreSQL server hostname |
| `port` | no | `$PGPORT` (`5432`) | PostgreSQL server port |
| `database` | no | `$PGDATABASE` (`postgres`) | PostgreSQL database name |
| `user` | no | `$PGUSER` (`postgres`) | PostgreSQL username |
| `password` | no | `$PGPASSWORD` (`postgres`) | PostgreSQL password |
| `schema` | no | `$PGSCHEMA` (`public`) | Target schema |

#### Write behavior

| Property | Required | Default | Description |
|---|---|---|---|
| `table` | yes | | Target table name in PostgreSQL |
| `mode` | no | `append` | Write mode: `append`, `truncate`, `overwrite`, or `merge` |
| `primary_key` | no | | Column name or list for the primary key. Required for `merge` mode |
| `merge_key` | no | | Column name or list used as the conflict key for `merge`. Defaults to `primary_key` when omitted |
| `pre_pgsql` | no | | SQL statement or list to run on PostgreSQL before the write |
| `post_pgsql` | no | | SQL statement or list to run on PostgreSQL after the write |
| `**options` | no | | Additional keyword arguments passed to the postgres extension |

## Accessing the session

All `tio_duckdb` steps inherit from `DuckdbStepMixin`, which provides a `self.duckdb` shortcut to the active `DuckDBPyConnection`:

```python
# Shortcut (available in all tio_duckdb steps)
conn = self.duckdb  # DuckDBPyConnection

# Equivalent standard form
conn = self.context.runner.session  # DuckDBPyConnection
```

`self.duckdb` is the idiomatic way to access the connection inside DuckDB steps. Both forms are equivalent.
