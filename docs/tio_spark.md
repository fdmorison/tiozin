# tio_spark

`tio_spark` is the Tiozin provider family for Apache Spark. It provides a runner, file inputs, SQL transforms, and file outputs for Spark-based pipelines.

> **Note:** `tio_spark` currently lives inside the `tiozin` core repository. In a future major version it will be extracted into its own independent package. Creating new provider families inside the core repository is not allowed.

## Installation

```bash
pip install tiozin[tio_spark]
```

## SparkRunner

Runs pipelines on Apache Spark. Manages a `SparkSession` during setup and stops it during teardown. The app name is set to the job slug automatically.

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  log_level: WARN
```

### Properties

| Property | Default | Description |
|---|---|---|
| `master` | `-` | Spark master URL (e.g. `local[*]`, `yarn`, `spark://host:7077`) |
| `endpoint` | `-` | Spark Connect endpoint (e.g. `sc://localhost:15002`). Requires Spark 3.4+ |
| `enable_hive_support` | `false` | Enable Hive metastore integration |
| `log_level` | `WARN` | Spark context log level |
| `jars_packages` | `[]` | Maven coordinates to add to the classpath |
| `streaming` | `false` | Enable streaming execution mode |
| `**options` | `-` | Additional Spark config passed directly to `SparkSession.builder` |

`master` and `endpoint` are mutually exclusive.

### Spark Connect

To connect to a remote Spark Connect server (Spark 3.4+):

```yaml
runner:
  kind: SparkRunner
  endpoint: sc://localhost:15002
```

### Arbitrary Spark config

Any unrecognized property is passed directly to `SparkSession.builder.config()`:

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  spark.executor.memory: 4g
  spark.sql.shuffle.partitions: 200
```

### Adding JAR packages

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  jars_packages:
    - org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0
```

## SparkIcebergRunner

A Spark runner pre-configured for Apache Iceberg. Extends `SparkRunner` and wires the required Spark SQL extensions and catalog configuration automatically.

```yaml
runner:
  kind: SparkIcebergRunner
  master: local[*]
  catalog_name: local
  catalog_type: hadoop
  catalog_warehouse: s3://my-bucket/warehouse
```

### Properties

Inherits all `SparkRunner` properties, plus:

| Property | Required | Default | Description |
|---|---|---|---|
| `catalog_name` | yes | | Name of the Iceberg catalog |
| `catalog_type` | one of type or impl | `-` | Catalog type: `hive`, `hadoop`, `rest`, `glue`, `nessie`, `jdbc` |
| `catalog_impl` | one of type or impl | `-` | Custom catalog implementation class |
| `catalog_uri` | no | `-` | Catalog URI (e.g. Hive metastore or REST endpoint) |
| `catalog_warehouse` | no | `-` | Warehouse path |
| `iceberg_class` | no | `SparkSessionCatalog` | Spark catalog class |

## SparkFileInput

Reads files into a Spark DataFrame. Supports all formats Spark supports (Parquet, CSV, JSON, ORC, Avro, and more).

```yaml
inputs:
  - kind: SparkFileInput
    name: customers
    path: data/customers.csv
    format: csv
    header: true
    inferSchema: true
```

Multiple paths:

```yaml
inputs:
  - kind: SparkFileInput
    name: events
    path:
      - data/events/2026-01-01
      - data/events/2026-01-02
    format: parquet
```

When `streaming: true` is set on the runner, exactly one directory path is required.

When `explode_filepath: true` is set, each row gains extra file-level columns: `filesize`, `dirpath`, `dirname`, `filepath`, `filename`, `filestem`, `filetype`.

Any unrecognized property is passed directly as a Spark reader option (e.g. `header`, `inferSchema`, `delimiter`).

### Properties

| Property | Required | Default | Description |
|---|---|---|---|
| `path` | yes | | Path or list of paths to read from |
| `format` | no | `parquet` | File format (`parquet`, `csv`, `json`, `orc`, `avro`, etc.) |
| `explode_filepath` | no | `false` | Expand file path into semantic columns |
| `**options` | no | `-` | Spark reader options passed directly to Spark |

## SparkSqlTransform

Runs a Spark SQL query against temporary views. Each input or prior transform result is automatically registered as a named view accessible by the step `name`.

```yaml
transforms:
  - kind: SparkSqlTransform
    name: add_metadata
    query: |-
      SELECT *, current_timestamp() AS _created_at
      FROM @self
```

Use `@self` to reference the current input without knowing its name:

```yaml
transforms:
  - kind: SparkSqlTransform
    name: enriched
    query: |-
      SELECT c.name, o.total
      FROM customers c
      JOIN orders o ON c.id = o.customer_id

  - kind: SparkSqlTransform
    name: filtered
    query: SELECT * FROM @self WHERE total > 100
```

With multiple inputs:

- `@self` or `@self0`: first dataset
- `@self1`, `@self2`, ...: additional datasets

Named parameters via `args` (`:param_name` syntax):

```yaml
transforms:
  - kind: SparkSqlTransform
    name: filtered
    query: SELECT * FROM @self WHERE total > :min_total
    args:
      min_total: 500
```

### Properties

| Property | Required | Description |
|---|---|---|
| `query` | yes | SQL query. Supports `@self` references and `:param` named parameters |
| `args` | no | Named parameter values for the query |

## SparkFileOutput

Writes a Spark DataFrame to files.

```yaml
outputs:
  - kind: SparkFileOutput
    name: raw_customers
    path: .output/lake-{{domain}}-{{layer}}/{{product}}
    format: parquet
    mode: append
```

With Hive-style partitioning:

```yaml
outputs:
  - kind: SparkFileOutput
    name: partitioned
    path: .output/lake/orders
    format: parquet
    mode: overwrite
    partition_by:
      - country
      - date
```

### Properties

| Property | Required | Default | Description |
|---|---|---|---|
| `path` | yes | | Target path to write to |
| `format` | no | `parquet` | Output format (`parquet`, `csv`, `json`, `orc`, etc.) |
| `mode` | no | `append` | Write mode: `append`, `overwrite`, `ignore`, `error` |
| `partition_by` | no | `[]` | Columns to partition by (Hive-style) |
| `**options` | no | `-` | Spark writer options passed directly to Spark |

## Accessing the session

All `tio_spark` steps inherit from `SparkStepMixin`, which provides a `self.spark` shortcut to the active `SparkSession`:

```python
# Shortcut (available in all tio_spark steps)
spark = self.spark  # SparkSession

# Equivalent standard form
spark = self.context.runner.session  # SparkSession
```

`self.spark` is the idiomatic way to access the session inside Spark steps. Both forms are equivalent.
