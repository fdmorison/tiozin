# SparkFileInput

Reads files into a Spark DataFrame. Supports all formats Spark supports natively and any format added by a loaded Spark package.

```yaml
inputs:
  - kind: SparkFileInput
    name: customers
    path: data/customers
    format: parquet
```

## Parameters

| Property | Description | Default |
|---|---|---|
| `path` | Path or list of paths to read from | |
| `format` | File format | `parquet` |
| `explode_filepath` | Enrich rows with file path columns | `false` |
| `**options` | Spark reader options passed directly to Spark | |

## Supported formats

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

## Enriching rows with file path columns

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

## Streaming mode

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

## Extra reader options

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
