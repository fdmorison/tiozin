# DuckdbFileOutput

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

## Parameters

| Property | Description | Default |
|---|---|---|
| `path` | Target directory path (trailing `/` is added automatically) | |
| `format` | Output format: `parquet`, `csv`, `json`, etc. | `parquet` |
| `mode` | Write mode: `append` (add files) or `overwrite` (clear directory first) | `append` |
| `partition_by` | Columns to use for Hive-style partitioning | `[]` |
| `compression` | Compression codec | `snappy` |
| `**options` | Additional DuckDB writer options | |

## Hive-style partitioning

Use `partition_by` to split the output into subdirectories by column values:

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
