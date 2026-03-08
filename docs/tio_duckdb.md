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

---

## DuckdbRunner

Runs a Tiozin pipeline on DuckDB. During setup, it opens a `DuckDBPyConnection`. During teardown, it closes it.

```yaml
runner:
  kind: DuckdbRunner
```

By default, the runner opens a named in-memory database using the job's slug. For a job named `my-analytics-job`, the database is `:memory:my_analytics_job`. Named in-memory databases are shared: any other connection that opens `:memory:my_analytics_job` sees the same data. To point a second job at the same database, set `database` explicitly:

```yaml
runner:
  kind: DuckdbRunner
  database: ":memory:my_analytics_job"
```

To use a file-based database that persists across runs:

```yaml
runner:
  kind: DuckdbRunner
  database: path/to/main.duckdb
```

### Parameters

| Property | Default | Description |
|---|---|---|
| `database` | `:memory:<job_slug>` | DuckDB database path, or `:memory:` for an anonymous in-memory database |
| `read_only` | `false` | Open the main database and all attached databases in read-only mode |
| `attach` | `{}` | Map of alias to path for external databases to attach during setup |
| `extensions` | `[]` | DuckDB extensions to install and load during setup |
| `**options` | | DuckDB config options passed to `duckdb.connect(config=...)` |

### Extensions

```yaml
runner:
  kind: DuckdbRunner
  extensions:
    - httpfs
    - spatial
```

Extensions are installed and loaded during `setup()`. Any extension supported by DuckDB works here.

### Attaching external databases

Use `attach` to make other DuckDB databases available by alias in SQL transforms:

```yaml
runner:
  kind: DuckdbRunner
  attach:
    staging: /data/staging.duckdb
    analytics: /data/analytics.duckdb
```

Attached databases are queryable by their alias:

```yaml
transforms:
  - kind: DuckdbSqlTransform
    name: from_staging
    query: SELECT * FROM staging.my_table
```

### DuckDB config options

Any key not listed above is forwarded to `duckdb.connect(config=...)`. The full list of supported options is in the [DuckDB configuration reference](https://duckdb.org/docs/configuration/overview).

```yaml
runner:
  kind: DuckdbRunner
  threads: 4
  memory_limit: 2GB
```

---

## DuckdbFileInput

Reads files into a DuckDB relation. Supports all file formats DuckDB supports natively, including Parquet, CSV, JSON, and plain text. Any format added by a loaded DuckDB extension (such as Excel via `spatial`) also works.

```yaml
inputs:
  - kind: DuckdbFileInput
    name: customers
    path: data/customers.csv
    format: csv
```

### Parameters

| Property | Required | Default | Description |
|---|---|---|---|
| `path` | yes | | Path or list of paths to read from |
| `format` | no | `parquet` | File format |
| `hive_partitioning` | no | `true` | Interpret `col=value/` partition directories |
| `union_by_name` | no | `true` | Merge schemas by column name when reading multiple files |
| `explode_filepath` | no | `false` | Optionally enrich rows with file path columns |
| `mode` | no | `relation` | How the result is materialized before the pipeline continues |
| `**options` | no | | DuckDB reader options passed directly to the `read_<format>()` function |

### Supported formats

The `format` field maps directly to a DuckDB `read_<format>()` table function. Any format supported by a loaded DuckDB extension also works. For format-specific options, see the [DuckDB data import reference](https://duckdb.org/docs/data/overview).

| Format | DuckDB function | Notes |
|---|---|---|
| `parquet` | `read_parquet()` | Default |
| `csv` | `read_csv()` | |
| `csv_auto` | `read_csv_auto()` | Schema inferred from content |
| `json` | `read_json()` | |
| `json_auto` | `read_json_auto()` | Schema inferred from content |
| `ndjson` | `read_ndjson()` | Newline-delimited JSON |
| `text` | `read_text()` | Reads raw text; adds a `content` column |
| `blob` | `read_blob()` | Reads raw bytes; adds a `content` column |
| `tsv` | `read_csv(delim='\t')` | Tiozin alias |
| `jsonl` | `read_ndjson()` | Tiozin alias |
| `txt` | `read_text()` | Tiozin alias |
| `auto_csv` | `read_csv_auto()` | Tiozin alias |
| `auto_json` | `read_json_auto()` | Tiozin alias |

### Read mode

The `mode` property controls how the data is materialized at read time.

| Mode | Description |
|---|---|
| `relation` | DuckDB evaluates the file lazily when the relation is accessed downstream. The file is re-read each time the relation is queried |
| `table` | Reads the file immediately and stores the result as a persistent DuckDB table. Acts as a cache: subsequent queries hit the table instead of the file |
| `overwrite_table` | Same as `table`, but drops and recreates the table if it already exists. Useful for idempotent runs |
| `temp_table` | Reads the file immediately and stores the result as a DuckDB temporary table. Acts as a cache for the current session only |
| `view` | Creates a persistent DuckDB view. The query is stored; DuckDB re-reads the file each time the view is queried |
| `temp_view` | Same as `view`, but the view exists only for the current session |

```yaml
inputs:
  - kind: DuckdbFileInput
    name: events
    path: /data/events/
    format: parquet
    mode: table   # reads once and caches as a table; downstream queries hit the table
```

### Enriching rows with file path columns

When reading from multiple files, you often need to know which file each row came from. Set `explode_filepath: true` to add file-level columns to every row:

| Column | Value |
|---|---|
| `dirpath` | Full path to the directory containing the file |
| `dirname` | Name of the directory (last component of `dirpath`) |
| `filepath` | Full path to the file |
| `filename` | Name of the file including extension |
| `filestem` | Name of the file without extension |
| `filetype` | File extension without the dot |
| `filesize` | File size in bytes (text and blob formats only) |

```yaml
inputs:
  - kind: DuckdbFileInput
    name: logs
    path: /data/logs/
    format: txt
    explode_filepath: true
```

### Extra reader options

Any property not listed in the parameters table above is forwarded directly to the underlying DuckDB `read_<format>()` call. The full list of options per format is in the [DuckDB data import reference](https://duckdb.org/docs/data/overview).

```yaml
inputs:
  - kind: DuckdbFileInput
    name: raw
    path: data/raw.csv
    format: csv
    header: true
    quote: '"'
    escape: '\\'
```

---

## DuckdbSqlTransform

Runs a DQL SQL query on the active DuckDB connection and passes the resulting relation to the next step. Only queries that return a relation are supported: SELECT statements, CTEs (`WITH ... SELECT ...`), and similar DQL constructs. DDL (`CREATE`, `DROP`) and DML (`INSERT`, `UPDATE`, `DELETE`) do not return a relation and will raise an error. Use outputs for write operations.

```yaml
transforms:
  - kind: DuckdbSqlTransform
    name: filtered
    query: SELECT * FROM customers WHERE status = 'active'
```

### Parameters

| Property | Required | Description |
|---|---|---|
| `query` | yes | DQL SQL query. Supports step references, `@data` aliases, and `$param` named parameters |
| `args` | no | Named parameter values for the query |

### Referencing upstream steps

Because the framework registers every step result as a named view, any input or prior transform is referenceable by its slug directly in SQL:

```yaml
inputs:
  - kind: DuckdbFileInput
    name: customers
    path: data/customers.csv

  - kind: DuckdbFileInput
    name: orders
    path: data/orders.csv

transforms:
  - kind: DuckdbSqlTransform
    name: enriched
    query: |-
      SELECT c.name, o.total
      FROM customers c
      JOIN orders o ON c.id = o.customer_id
```

### Referencing transformation arguments: The @data alias

`@data` is a shorthand that resolves to the slug of the upstream step at query time. Use it when you want to write a generic transform without hardcoding the upstream step name.

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
    # @data resolves to enriched, the previous step
```

When a transform receives multiple upstream relations, the aliases map positionally to the inputs received by the `transform` method:

```python
def transform(self, data: DuckDBPyRelation, *others: DuckDBPyRelation) -> DuckDBPyRelation:
    # @data / @data0  →  data       (first upstream step)
    # @data1          →  others[0]  (second upstream step)
    # @data2          →  others[1]  (third upstream step)
    ...
```

```yaml
inputs:
  - kind: DuckdbFileInput
    name: customers
    path: data/customers.csv

  - kind: DuckdbFileInput
    name: orders
    path: data/orders.csv

transforms:
  - kind: DuckdbSqlTransform
    name: joined
    # @data   →  customers (first input)
    # @data1  →  orders    (second input)
    query: |-
      SELECT c.name, o.total
      FROM @data c
      JOIN @data1 o ON c.id = o.customer_id
```

### Named parameters

Named parameters are a DuckDB feature. Use `$param_name` in the query and supply the values under `args`. See the [DuckDB parameterized queries reference](https://duckdb.org/docs/clients/python/dbapi#parameterized-queries) for details.

```yaml
transforms:
  - kind: DuckdbSqlTransform
    name: filtered
    query: SELECT * FROM @data WHERE total > $min_total AND status = $status
    args:
      min_total: 500
      status: active
```

---

## DuckdbFileOutput

Writes a DuckDB relation to files. Output is always written to a directory, not a single file.

```yaml
outputs:
  - kind: DuckdbFileOutput
    name: raw_customers
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/
    format: parquet
    mode: overwrite
```

Output files are named `part-{i}-{uuid}.snappy` by default.

### Parameters

| Property | Required | Default | Description |
|---|---|---|---|
| `path` | yes | | Target directory path (trailing `/` is added automatically) |
| `format` | no | `parquet` | Output format: `parquet`, `csv`, `json`, etc. |
| `mode` | no | `append` | Write mode: `append` (add files) or `overwrite` (clear directory first) |
| `partition_by` | no | `[]` | Columns to use for Hive-style partitioning |
| `compression` | no | `snappy` | Compression codec |
| `**options` | no | | Additional DuckDB writer options |

### Hive-style partitioning

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

This produces directories like `.output/lake/orders/country=BR/date=2024-01-01/`.

---

## DuckdbPostgresOutput

Writes a DuckDB relation into a PostgreSQL table. Uses the DuckDB Postgres extension to handle the transfer directly. Supports four write modes, automatic schema evolution, and SQL hooks that run before and after each write.

A complete working example is in [`examples/jobs/duckdb/postgres/postgres_output.yaml`](../examples/jobs/duckdb/postgres/postgres_output.yaml).

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    name: save_customers
    table: customers
```

Connection defaults are read from standard PostgreSQL environment variables (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGSCHEMA`). Properties set in the job always take priority.

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

### Parameters

| Property | Required | Default | Description |
|---|---|---|---|
| `table` | yes | | Target table name in PostgreSQL |
| `host` | no | `$PGHOST` (`localhost`) | PostgreSQL server hostname |
| `port` | no | `$PGPORT` (`5432`) | PostgreSQL server port |
| `database` | no | `$PGDATABASE` (`postgres`) | PostgreSQL database name |
| `user` | no | `$PGUSER` (`postgres`) | PostgreSQL username |
| `password` | no | `$PGPASSWORD` | PostgreSQL password |
| `schema` | no | `$PGSCHEMA` (`public`) | Target schema |
| `mode` | no | `append` | Write mode: `append`, `truncate`, `overwrite`, or `merge` |
| `primary_key` | no | | Column name or list for the primary key. Required for `merge` mode |
| `merge_key` | no | `primary_key` | Conflict key for `merge`. Defaults to `primary_key` when omitted |
| `pre_pgsql` | no | | SQL statement or list to run on PostgreSQL before the write |
| `post_pgsql` | no | | SQL statement or list to run on PostgreSQL after the write |
| `**options` | no | | Additional keyword arguments passed to the DuckDB Postgres extension |

### Write modes

All modes create the target table automatically if it does not exist yet.

#### Append Mode

Inserts incoming rows into the table. Does not deduplicate: running twice on the same data produces twice as many rows.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: events
    mode: append
```

#### Truncate Mode

Clears the table before each write, then inserts incoming rows. Every run replaces the table content with the current batch. The table structure is preserved.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: events
    mode: truncate
```

#### Overwrite Mode

Recreates the table on every run. The new table structure matches the current batch exactly. Check constraints, column defaults, and outbound foreign keys are preserved. The primary key is re-added automatically if `primary_key` is set. Other indexes are not preserved: recreate them via `post_pgsql`.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: events
    mode: overwrite
    primary_key: id
    post_pgsql:
      - CREATE INDEX IF NOT EXISTS idx_events_date ON public.events(date)
```

#### Merge Mode

Upserts rows by key. Existing rows are updated; new rows are inserted. Incoming `NULL` values do not overwrite existing non-null values. Requires `primary_key`.

```yaml
outputs:
  - kind: DuckdbPostgresOutput
    table: customers
    mode: merge
    primary_key: id
```

Use `merge_key` when the conflict key differs from the primary key:

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

`pre_pgsql` runs SQL on PostgreSQL before the write strategy executes, but after schema evolution has already run. `post_pgsql` runs after the write completes. Both accept a single statement or a list.

Common uses: drop dependent views before an overwrite, grant permissions and recreate views after a write.

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

---

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
