# tio_spark

`tio_spark` is the Tiozin provider family for Apache Spark. It runs pipelines on a managed `SparkSession` and provides four plugins: a file reader, a SQL transform, a file writer, and an Iceberg-ready runner. Every step result is automatically available as a named temporary view for downstream SQL queries. The family supports both batch and streaming execution.

> **Note:** `tio_spark` currently lives inside the `tiozin` core repository. In a future major version it will be extracted into its own independent package. Creating new provider families inside the core repository is not allowed.

## Installation

```bash
pip install tiozin[tio_spark]
```

## How data flows through steps

Every step in `tio_spark` produces a Spark `DataFrame`. After each step runs, the framework automatically registers that DataFrame as a named temporary view using the step's slug as the view name. The slug is the slugified version of the step's `name` field: lowercase, with spaces and special characters replaced by underscores.

```yaml
inputs:
  - kind: SparkFileInput
    name: raw customers      # slug: raw_customers
    path: data/customers

transforms:
  - kind: SparkSqlTransform
    name: filtered
    query: SELECT * FROM raw_customers WHERE status = 'active'
    # raw_customers is available because the input was registered under that slug
```

This view registration happens at the framework level for all inputs and transforms. No step needs to do it explicitly.

---

## SparkRunner

Runs a Tiozin pipeline on Apache Spark. During setup, it creates a `SparkSession` with the job slug as the app name. During teardown, it stops the session.

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  log_level: WARN
```

### Parameters

| Property | Default | Description |
|---|---|---|
| `master` | | Spark master URL (`local[*]`, `yarn`, `spark://host:7077`, etc.) |
| `endpoint` | | Spark Connect server endpoint (`sc://host:port`). Requires Spark 3.4+. Mutually exclusive with `master` |
| `enable_hive_support` | `false` | Enable Hive metastore integration |
| `log_level` | `WARN` | Spark context log level |
| `jars_packages` | `[]` | Maven coordinates to add to the Spark classpath |
| `streaming` | `false` | Enable streaming execution mode |
| `**options` | | Spark config options passed directly to `SparkSession.builder` |

### Spark config options

Any key not listed above is forwarded to `SparkSession.builder.config()`. The full list of supported options is in the [Spark configuration reference](https://spark.apache.org/docs/latest/configuration.html).

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  spark.executor.memory: 4g
  spark.sql.shuffle.partitions: 200
```

### JAR packages

Use `jars_packages` to add Maven-coordinated dependencies to the Spark classpath. This is equivalent to setting `spark.jars.packages`.

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  jars_packages:
    - org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0
    - io.delta:delta-spark_2.12:3.2.0
```

### Hive support

Set `enable_hive_support: true` to connect to a Hive metastore and read or write Hive tables. Requires a Hive-compatible environment with `hive-site.xml` on the classpath.

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  enable_hive_support: true
```

### Spark Connect

To connect to a remote Spark Connect server instead of creating a local session, use `endpoint`. `master` and `endpoint` are mutually exclusive.

```yaml
runner:
  kind: SparkRunner
  endpoint: sc://localhost:15002
```

### Streaming mode

Set `streaming: true` to enable streaming execution. When streaming is enabled, `SparkFileInput` uses `spark.readStream` instead of `spark.read`, and each input must point to exactly one directory path.

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  streaming: true
```

---

## SparkIcebergRunner

A Spark runner pre-configured for Apache Iceberg. Extends `SparkRunner` and wires the required Spark SQL extensions and catalog configuration automatically. Use this instead of `SparkRunner` when your pipeline reads or writes Iceberg tables.

```yaml
runner:
  kind: SparkIcebergRunner
  master: local[*]
  catalog_name: local
  catalog_type: hadoop
  catalog_warehouse: s3://my-bucket/warehouse
```

### Parameters

Inherits all `SparkRunner` parameters, plus:

| Property | Required | Default | Description |
|---|---|---|---|
| `catalog_name` | yes | | Name of the Iceberg catalog, used as a prefix in SQL (`catalog_name.db.table`) |
| `catalog_type` | one of `catalog_type` or `catalog_impl` | | Catalog backend type |
| `catalog_impl` | one of `catalog_type` or `catalog_impl` | | Fully qualified class name of a custom catalog implementation |
| `catalog_uri` | no | | Catalog URI (Hive metastore `thrift://`, REST endpoint, etc.) |
| `catalog_warehouse` | no | | Warehouse path for the catalog |
| `iceberg_class` | no | `org.apache.iceberg.spark.SparkSessionCatalog` | Spark catalog class used to register the Iceberg catalog |

### Catalog types

`catalog_type` selects the Iceberg catalog backend. The accepted values are:

| Value | Description |
|---|---|
| `hadoop` | Filesystem-based catalog. No external service needed. Works with local paths, S3, GCS, etc. |
| `hive` | Uses the Hive metastore. Requires `catalog_uri` pointing to the metastore |
| `rest` | REST catalog API (Project Nessie, Polaris, Unity Catalog, etc.). Requires `catalog_uri` |
| `glue` | AWS Glue Data Catalog. No `catalog_uri` needed. Uses the AWS SDK credential chain |
| `jdbc` | JDBC-backed catalog. Requires `catalog_uri` with the JDBC connection string |
| `nessie` | Project Nessie catalog. Requires `catalog_uri` pointing to the Nessie server |

For custom catalog implementations not covered by `catalog_type`, use `catalog_impl` with the fully qualified class name instead.

For the full Iceberg catalog configuration reference, see the [Iceberg Spark configuration docs](https://iceberg.apache.org/docs/latest/spark-configuration/#spark-sql-options).

#### AWS Glue

The Glue catalog integrates Iceberg with the AWS Glue Data Catalog. AWS credentials are picked up from the environment (instance profile, environment variables, or `~/.aws/credentials`). The `catalog_warehouse` points to the S3 path where Iceberg data files are stored.

The Iceberg AWS bundle must be on the classpath. Add it via `jars_packages`:

```yaml
runner:
  kind: SparkIcebergRunner
  master: local[*]
  catalog_name: glue
  catalog_type: glue
  catalog_warehouse: s3://my-bucket/warehouse
  jars_packages:
    - org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0
    - org.apache.iceberg:iceberg-aws-bundle:1.5.0
```

To query an Iceberg table registered in Glue:

```sql
SELECT * FROM glue.my_database.my_table
```

#### Other catalog examples

```yaml
# Hive metastore
runner:
  kind: SparkIcebergRunner
  master: local[*]
  catalog_name: hive_catalog
  catalog_type: hive
  catalog_uri: thrift://hive-metastore:9083

# REST catalog
runner:
  kind: SparkIcebergRunner
  master: local[*]
  catalog_name: rest_catalog
  catalog_type: rest
  catalog_uri: http://catalog:8181
```

### iceberg_class

`iceberg_class` controls which Spark catalog class Iceberg registers under `catalog_name`. The two supported values are:

| Value | Use when |
|---|---|
| `org.apache.iceberg.spark.SparkSessionCatalog` (default) | Replacing the default Spark `spark_catalog`. Allows using unqualified table names |
| `org.apache.iceberg.spark.SparkCatalog` | Adding a new named catalog alongside the existing Spark catalog |

---

## SparkFileInput

Reads files into a Spark DataFrame. Supports all formats Spark supports natively and any format added by a loaded Spark package.

```yaml
inputs:
  - kind: SparkFileInput
    name: customers
    path: data/customers
    format: parquet
```

### Parameters

| Property | Required | Default | Description |
|---|---|---|---|
| `path` | yes | | Path or list of paths to read from |
| `format` | no | `parquet` | File format |
| `explode_filepath` | no | `false` | Optionally enrich rows with file path columns |
| `**options` | no | | Spark reader options passed directly to Spark |

### Supported formats

The `format` field is passed directly to Spark's `DataFrameReader.format()`. The full list of Spark data sources is in the [Spark SQL data sources reference](https://spark.apache.org/docs/latest/sql-data-sources-load-save-functions.html).

| Format | Notes |
|---|---|
| `parquet` | Default |
| `csv` | |
| `json` | Newline-delimited JSON |
| `orc` | |
| `avro` | Requires the `spark-avro` package |
| `text` | Reads each line as a single `value` string column |
| `binaryFile` | Reads each file as a binary blob with metadata columns |
| `xml` | Requires the `spark-xml` package |
| `sequenceFile` | Hadoop SequenceFile format |

### Enriching rows with file path columns

When reading from multiple files, you often need to know which file each row came from. Set `explode_filepath: true` to add file-level columns to every row:

| Column | Value |
|---|---|
| `filesize` | File size in bytes (from Spark file metadata) |
| `dirpath` | Full path to the directory containing the file |
| `dirname` | Name of the directory (last path component before the filename) |
| `filepath` | Full path to the file |
| `filename` | Name of the file including extension |
| `filestem` | Name of the file without extension |
| `filetype` | File extension without the dot |

```yaml
inputs:
  - kind: SparkFileInput
    name: logs
    path: /data/logs/
    format: text
    explode_filepath: true
```

### Streaming mode

When the runner has `streaming: true`, `SparkFileInput` uses `spark.readStream` instead of `spark.read`. In streaming mode, `path` must be a single directory path. Providing a list of paths raises an error.

```yaml
runner:
  kind: SparkRunner
  master: local[*]
  streaming: true

inputs:
  - kind: SparkFileInput
    name: events
    path: /data/incoming/events/   # single directory required in streaming mode
    format: json
```

### Extra reader options

Any property not listed in the parameters table above is forwarded directly to Spark's `DataFrameReader.options()`. The full list of options per format is in the [Spark SQL data sources reference](https://spark.apache.org/docs/latest/sql-data-sources-load-save-functions.html).

```yaml
inputs:
  - kind: SparkFileInput
    name: raw
    path: data/raw.csv
    format: csv
    header: true
    inferSchema: true
    delimiter: ";"
```

---

## SparkSqlTransform

Runs a Spark SQL query against the registered temporary views and passes the resulting DataFrame to the next step. Any SQL query supported by Spark SQL works here.

```yaml
transforms:
  - kind: SparkSqlTransform
    name: filtered
    query: SELECT * FROM customers WHERE status = 'active'
```

### Parameters

| Property | Required | Description |
|---|---|---|
| `query` | yes | Spark SQL query. Supports step references, `@data` aliases, and `:param` named parameters |
| `args` | no | Named parameter values for the query, as a dict or a positional list |

### Referencing upstream steps

Because the framework registers every step result as a named temporary view, any input or prior transform is referenceable by its slug directly in SQL:

```yaml
inputs:
  - kind: SparkFileInput
    name: customers
    path: data/customers

  - kind: SparkFileInput
    name: orders
    path: data/orders

transforms:
  - kind: SparkSqlTransform
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
  - kind: SparkSqlTransform
    name: enriched
    query: |-
      SELECT c.name, o.total
      FROM customers c
      JOIN orders o ON c.id = o.customer_id

  - kind: SparkSqlTransform
    name: high_value
    query: SELECT * FROM @data WHERE total > 100
    # @data resolves to enriched, the previous step
```

When a transform receives multiple upstream DataFrames, the aliases map positionally to the inputs received by the `transform` method:

```python
def transform(self, data: DataFrame, *others: DataFrame) -> DataFrame:
    # @data / @data0  →  data       (first upstream step)
    # @data1          →  others[0]  (second upstream step)
    # @data2          →  others[1]  (third upstream step)
    ...
```

```yaml
inputs:
  - kind: SparkFileInput
    name: customers
    path: data/customers

  - kind: SparkFileInput
    name: orders
    path: data/orders

transforms:
  - kind: SparkSqlTransform
    name: joined
    # @data   →  customers (first input)
    # @data1  →  orders    (second input)
    query: |-
      SELECT c.name, o.total
      FROM @data c
      JOIN @data1 o ON c.id = o.customer_id
```

### Named parameters

Named parameters are a Spark SQL feature. Use `:param_name` in the query and supply the values under `args`. `args` accepts a dict of named values or a list of positional values. See the [Spark SQL parameterized queries reference](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select.html) for details.

```yaml
transforms:
  - kind: SparkSqlTransform
    name: filtered
    query: SELECT * FROM @data WHERE total > :min_total AND status = :status
    args:
      min_total: 500
      status: active
```

---

## SparkFileOutput

Writes a Spark DataFrame to files.

```yaml
outputs:
  - kind: SparkFileOutput
    name: raw_customers
    path: .output/lake-{{domain}}-{{layer}}/{{product}}
    format: parquet
    mode: overwrite
```

### Parameters

| Property | Required | Default | Description |
|---|---|---|---|
| `path` | yes | | Target path to write to |
| `format` | no | `parquet` | Output format |
| `mode` | no | `append` | Write mode |
| `partition_by` | no | `[]` | Columns to use for Hive-style partitioning |
| `**options` | no | | Spark writer options passed directly to Spark |

### Write modes

| Mode | Description |
|---|---|
| `append` | Adds new files to the path. Does not remove existing files |
| `overwrite` | Removes all existing files at the path before writing |
| `ignore` | Writes only if no data exists at the path. Skips silently if it does |
| `error` | Raises an error if any data already exists at the path |
| `errorifexists` | Alias for `error` |

### Hive-style partitioning

Use `partition_by` to split the output into subdirectories by column values:

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

This produces directories like `.output/lake/orders/country=BR/date=2024-01-01/`.

### Extra writer options

Any property not listed in the parameters table above is forwarded directly to Spark's `DataFrameWriter.option()`. The full list of options per format is in the [Spark SQL data sources reference](https://spark.apache.org/docs/latest/sql-data-sources-load-save-functions.html).

```yaml
outputs:
  - kind: SparkFileOutput
    name: compressed
    path: .output/lake/events
    format: json
    mode: overwrite
    compression: gzip
```

---

## Accessing the session

When writing a custom step in `tio_spark`, use `self.spark` to access the active Spark session. `self` here refers to the step instance: any class that extends `SparkTransform`, `SparkInput`, or `SparkOutput`.

```python
    def transform(self, data: DataFrame) -> DataFrame:
        sql = f"SELECT * FROM {data.alias} WHERE amount > 100"
        return self.spark.sql(sql)
```

This session is the one created and managed by the runner. It is shared across all steps in the pipeline, so every step reads from and writes to the same Spark session. Do not create a new session with `SparkSession.builder.getOrCreate()` inside a step: that would interfere with the runner-managed session and bypass the temporary views registered by other steps.

`self.spark` is shorthand for:

```python
session = self.context.runner.session  # SparkSession
```

Both are equivalent. `self.spark` is the idiomatic form.
