# Runners

A Runner is the execution engine of your pipeline. It creates the runtime session, receives the execution plan after steps run, and releases resources when the job finishes.

---

## How runners work

Every job has exactly one runner. The runner:

1. Creates its session (a `SparkSession`, DuckDB connection, etc.) during `setup`
2. Receives the execution plan produced by the job after all steps complete
3. Executes the plan in `run`
4. Releases resources in `teardown`

You never call these methods yourself — the framework calls them automatically when you run a job.

---

## NoOpRunner

The default runner for testing and local development. Accepts any plan and returns `None` without executing anything.

```yaml
runner:
  kind: NoOpRunner
```

| Property | Default | Description |
|---|---|---|
| `streaming` | `false` | Simulate streaming mode |

---

## SparkRunner

Runs pipelines on Apache Spark. Requires `pip install tiozin[tio_spark]`.

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  log_level: WARN
```

The runner creates a `SparkSession` during setup and stops it during teardown. The app name is set to the job slug automatically.

### Spark Connect

To connect to a remote Spark Connect server (Spark 3.4+):

```yaml
runner:
  kind: SparkRunner
  endpoint: sc://localhost:15002
```

`master` and `endpoint` are mutually exclusive.

### Hive support

```yaml
runner:
  kind: SparkRunner
  enable_hive_support: true
```

### Adding JAR packages

```yaml
runner:
  kind: SparkRunner
  jars_packages:
    - org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0
```

### Arbitrary Spark config

Any unrecognized property is passed directly to `SparkSession.builder.config()`:

```yaml
runner:
  kind: SparkRunner
  spark.executor.memory: 4g
  spark.sql.shuffle.partitions: 200
```

### All SparkRunner properties

| Property | Default | Description |
|---|---|---|
| `master` | — | Spark master URL (e.g. `local[*]`, `yarn`, `spark://host:7077`) |
| `endpoint` | — | Spark Connect endpoint (e.g. `sc://localhost:15002`) |
| `enable_hive_support` | `false` | Enable Hive metastore integration |
| `log_level` | `WARN` | Spark context log level |
| `jars_packages` | `[]` | Maven coordinates to add to the classpath |
| `streaming` | `false` | Enable streaming execution mode |
| `**options` | — | Additional Spark config passed to `SparkSession.builder` |

### SparkIcebergRunner

A convenience variant that pre-loads the Iceberg runtime JAR and Spark catalog extensions. Drop-in replacement for `SparkRunner` when working with Iceberg tables.

```yaml
runner:
  kind: SparkIcebergRunner
  master: local[*]
```

---

## DuckdbRunner

Runs pipelines on DuckDB. Requires `pip install tiozin[tio_duckdb]`.

```yaml
runner:
  kind: DuckdbRunner
```

By default, uses an in-memory database named after the job slug.

### Persistent database

```yaml
runner:
  kind: DuckdbRunner
  database: path/to/main.duckdb
```

### Extensions

```yaml
runner:
  kind: DuckdbRunner
  extensions:
    - httpfs
    - spatial
```

Extensions are installed and loaded during setup.

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

### All DuckdbRunner properties

| Property | Default | Description |
|---|---|---|
| `database` | `:memory:<job_name>` | DuckDB database path, `:memory:`, or `:default:` |
| `read_only` | `false` | Open all databases in read-only mode |
| `attach` | `{}` | Map of alias → path for external databases |
| `extensions` | `[]` | DuckDB extensions to install and load |
| `**options` | — | DuckDB config options passed to `duckdb.connect(config=...)` |

---

## Accessing the session

Inside any step, access the runner's session via the context:

```python
session = self.context.runner.session
```

For Spark steps, this returns the `SparkSession`. For DuckDB steps, the `DuckDBPyConnection`. Accessing the session before `setup` raises `NotInitializedError`.
