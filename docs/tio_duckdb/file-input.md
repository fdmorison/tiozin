# DuckdbFileInput

Reads files into a DuckDB relation. Supports all file formats DuckDB supports natively, including Parquet, CSV, JSON, and plain text. Any format added by a loaded DuckDB extension (such as Excel via `spatial`) also works.

```yaml
inputs:
  - kind: DuckdbFileInput
    name: customers
    path: data/customers.csv
    format: csv
```

## Parameters

| Property | Description | Default |
|---|---|---|
| `path` | Path or list of paths to read from | |
| `format` | File format | `parquet` |
| `hive_partitioning` | Interpret `col=value/` partition directories | `true` |
| `union_by_name` | Merge schemas by column name when reading multiple files | `true` |
| `explode_filepath` | Enrich rows with file path columns | `false` |
| `mode` | How the result is materialized before the pipeline continues | `relation` |
| `**options` | DuckDB reader options passed directly to the `read_<format>()` function | |

## Supported formats

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

## Read mode

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

## Enriching rows with file path columns

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

## Extra reader options

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
