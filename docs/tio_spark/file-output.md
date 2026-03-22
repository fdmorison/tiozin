# SparkFileOutput

Writes a Spark DataFrame to files.

```yaml
outputs:
  - kind: SparkFileOutput
    name: raw_customers
    path: .output/lake-{{domain}}-{{layer}}/{{product}}
    format: parquet
    mode: overwrite
```

## Parameters

| Property | Description | Default |
|---|---|---|
| `path` | Target path to write to | |
| `format` | Output format | `parquet` |
| `mode` | Write mode | `append` |
| `partition_by` | Columns to use for Hive-style partitioning | `[]` |
| `**options` | Spark writer options passed directly to Spark | |

## Write modes

| Mode | Description |
|---|---|
| `append` | Adds new files to the path. Does not remove existing files |
| `overwrite` | Removes all existing files at the path before writing |
| `ignore` | Writes only if no data exists at the path. Skips silently if it does |
| `error` | Raises an error if any data already exists at the path |
| `errorifexists` | Alias for `error` |

## Lineage

The output path is reported as the dataset written by this step following the [OpenLineage naming spec](https://openlineage.io/docs/spec/naming/).

## Hive-style partitioning

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

## Extra writer options

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
