# DuckdbFileOutput

Writes a DuckDB relation to files. Output is always written to a directory, not a single file.

```yaml
outputs:
  - kind: DuckdbFileOutput
    name: raw_customers
    path: .output/lake/customers/
    format: parquet
    mode: overwrite
```

Output files are named `part-{i}-{uuidv7}.snappy` by default.

## Parameters

| Property | Description | Default |
|---|---|---|
| `path` | Target directory path (trailing `/` is added automatically) | |
| `format` | Output format: `parquet`, `csv`, `json`, `ndjson`, `text`, `blob`, `xlsx`, `tsv`, `jsonl`, `txt`, `auto_csv`, `auto_json` | `parquet` |
| `mode` | Write mode: `append`, `overwrite`, `overwrite_or_ignore` | `append` |
| `partition_by` | Columns to use for Hive-style partitioning | `[]` |
| `compression` | Compression codec: `uncompressed`, `snappy`, `zstd`, `gzip`, `brotli`, `lz4`, `lz4_raw` | `snappy` |
| `**options` | Additional DuckDB writer options passed to the `COPY TO` statement | |

## Write modes

`append` adds new part files to the directory on each run without removing existing files.

`overwrite` deletes the entire directory contents before writing. Use this to guarantee a clean output on every run.

`overwrite_or_ignore` writes new files without clearing the directory first, and skips files that already exist.

## Hive-style partitioning

Use `partition_by` to split the output into subdirectories by column values:

```yaml
outputs:
  - kind: DuckdbFileOutput
    name: partitioned_orders
    path: .output/lake/orders/
    format: parquet
    mode: overwrite
    partition_by:
      - country
      - date
```

This produces directories like `.output/lake/orders/country=BR/date=2024-01-01/`.

When `partition_by` is empty, `PER_THREAD_OUTPUT true` is added to the `COPY TO` statement to allow parallel writes. When `partition_by` is set, `PER_THREAD_OUTPUT` is excluded: the two options are mutually exclusive in DuckDB.

## Lineage

The output path is reported as the dataset written by this step following the [OpenLineage naming spec](https://openlineage.io/docs/spec/naming/).
