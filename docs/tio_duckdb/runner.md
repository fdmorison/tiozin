# DuckdbRunner

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

## Parameters

| Property | Description | Default |
|---|---|---|
| `database` | DuckDB database path, or `:memory:` for an anonymous in-memory database | `:memory:<job_slug>` |
| `read_only` | Open the main database and all attached databases in read-only mode | `false` |
| `attach` | Map of alias to path for external databases to attach during setup | `{}` |
| `extensions` | DuckDB extensions to install and load during setup | `[]` |
| `**options` | DuckDB config options passed to `duckdb.connect(config=...)` | |

## Extensions

Use `extensions` to add DuckDB capabilities not available by default, such as reading remote files with `httpfs` or geospatial data with `spatial`. Extensions are installed and loaded during `setup()`.

```yaml
runner:
  kind: DuckdbRunner
  extensions:
    - httpfs
    - spatial
```

## Attaching external databases

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

## DuckDB config options

Any key not listed above is forwarded to `duckdb.connect(config=...)`. The full list of supported options is in the [DuckDB configuration reference](https://duckdb.org/docs/configuration/overview).

```yaml
runner:
  kind: DuckdbRunner
  threads: 4
  memory_limit: 2GB
```
