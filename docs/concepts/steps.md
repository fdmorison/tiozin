# Inputs, Transforms & Outputs

Steps are the building blocks inside a pipeline: inputs read data, transforms modify it, outputs persist it.

---

## Inputs

An input defines a data source. Every job needs at least one.

### NoOpInput

For testing and development. Does nothing and returns `None`.

```yaml
inputs:
  - kind: NoOpInput
    name: load
    path: data/input
```

### SparkFileInput

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

For multiple paths:

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

| Property | Default | Description |
|---|---|---|
| `path` | required | Path or list of paths to read from |
| `format` | `parquet` | File format (`parquet`, `csv`, `json`, `orc`, `avro`, etc.) |
| `explode_filepath` | `false` | Expand file path into semantic columns |
| `**options` | — | Spark reader options passed directly to Spark |

### DuckdbFileInput

Reads files into a DuckDB relation. Supports all formats DuckDB supports.

```yaml
inputs:
  - kind: DuckdbFileInput
    name: customers
    path: data/customers.csv
    format: csv
    header: true
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

| Property | Default | Description |
|---|---|---|
| `path` | required | Path or list of paths to read from |
| `format` | `parquet` | File format or Tiozin alias |
| `hive_partitioning` | `true` | Interpret `col=value/` partition directories |
| `union_by_name` | `true` | Merge schemas by column name across files |
| `explode_filepath` | `false` | Expand file path into semantic columns |
| `mode` | `relation` | How the result is registered: `relation`, `table`, `view`, `temp_table`, `temp_view`, `overwrite_table` |
| `**options` | — | DuckDB reader options passed to the `read_<format>()` function |

---

## Transforms

A transform modifies data. Transforms are optional — a job can have zero or more.

Transforms run in sequence. Each receives the output of the previous step.

### NoOpTransform

For testing and development. Passes data through unchanged.

```yaml
transforms:
  - kind: NoOpTransform
    name: process
```

### SparkSqlTransform

Runs a Spark SQL query. Each input or prior transform result is automatically registered as a named view, accessible by the step `name`.

```yaml
transforms:
  - kind: SparkSqlTransform
    name: add_metadata
    query: |-
      SELECT *, current_timestamp() AS _created_at
      FROM @self
```

Use `@self` to reference the current input without knowing its name. Use the step name to reference any previous step:

```yaml
transforms:
  - kind: SparkSqlTransform
    name: enriched
    query: |-
      SELECT c.name, o.total
      FROM customers c          -- references the input named "customers"
      JOIN orders o ON c.id = o.customer_id

  - kind: SparkSqlTransform
    name: filtered
    query: SELECT * FROM @self WHERE total > 100   -- @self references "enriched"
```

Named parameters via `args` (`:param_name` syntax):

```yaml
transforms:
  - kind: SparkSqlTransform
    name: filtered
    query: SELECT * FROM @self WHERE total > :min_total
    args:
      min_total: 500
```

| Property | Required | Description |
|---|---|---|
| `query` | yes | SQL query. Supports `@self` references and `:param` named parameters |
| `args` | no | Named parameter values for the query |

### DuckdbSqlTransform

Runs a DQL SQL query using DuckDB. Works the same as `SparkSqlTransform` but against the active DuckDB connection.

```yaml
transforms:
  - kind: DuckdbSqlTransform
    name: filtered
    query: SELECT * FROM @self WHERE status = $status
    args:
      status: active
```

Only `SELECT`-like queries are supported. DDL and DML (`CREATE`, `INSERT`, `UPDATE`, `DROP`, etc.) are not allowed and will raise an error — use outputs for write operations.

| Property | Required | Description |
|---|---|---|
| `query` | yes | DQL SQL query. Supports `@self` and `$param` named parameters |
| `args` | no | Named parameter values for the query |

### Multiple inputs in a transform

When a job has multiple inputs, the first transform receives all datasets. `SparkSqlTransform` and `DuckdbSqlTransform` handle this automatically — reference each input by its step name.

For additional `@self` tokens with multiple inputs: `@self` or `@self0` is the first dataset, `@self1` the second, and so on.

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
    query: |-
      SELECT c.name, o.total
      FROM customers c
      JOIN orders o ON c.id = o.customer_id
```

---

## Outputs

An output defines where data is written. A job can have zero or more outputs.

### NoOpOutput

For testing and development. Accepts data and discards it.

```yaml
outputs:
  - kind: NoOpOutput
    name: sink
    path: data/output
```

### SparkFileOutput

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

| Property | Default | Description |
|---|---|---|
| `path` | required | Target path to write to |
| `format` | `parquet` | Output format (`parquet`, `csv`, `json`, `orc`, etc.) |
| `mode` | `append` | Write mode: `append`, `overwrite`, `ignore`, `error` |
| `partition_by` | `[]` | Columns to partition by (Hive-style) |
| `**options` | — | Spark writer options passed directly to Spark |

### DuckdbFileOutput

Writes a DuckDB relation to files. Output is always written to a directory, never to a single file. Files are named `part-{i}-{uuid}.snappy` by default.

```yaml
outputs:
  - kind: DuckdbFileOutput
    name: raw_customers
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/
    format: parquet
    mode: overwrite
```

| Property | Default | Description |
|---|---|---|
| `path` | required | Target directory path (trailing `/` is added automatically) |
| `format` | `parquet` | Output format (`parquet`, `csv`, `json`, etc.) |
| `mode` | `append` | Write mode: `append` or `overwrite` |
| `partition_by` | `[]` | Columns to partition by (Hive-style) |
| `compression` | `snappy` | Compression codec |
| `**options` | — | Additional DuckDB writer options |

---

## Step metadata

Every step (input, transform, output) accepts these common fields:

| Field | Required | Description |
|---|---|---|
| `name` | yes | Unique identifier within the job |
| `description` | no | Short description |

Steps also accept optional Data Mesh fields. When set, they override the job-level values for template rendering within that step:

| Field | Description |
|---|---|
| `org` | Organization owning this step's data |
| `region` | Business region |
| `domain` | Domain team |
| `subdomain` | Subdomain |
| `layer` | Data layer (e.g. `raw` for an input, `refined` for an output) |
| `product` | Data product |
| `model` | Data model |

Input steps additionally support:

| Field | Description |
|---|---|
| `schema` | Schema definition |
| `schema_subject` | Schema registry subject name |
| `schema_version` | Specific schema version |
