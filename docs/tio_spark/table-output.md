# SparkTableOutput

Writes a Spark `DataFrame` to a table registered in a catalog.

The table is addressed by name, so the catalog decides where the data is stored. This makes the output suitable for managed tables.

```yaml
outputs:
  - kind: SparkTableOutput
    name: sales
    table: my_catalog.default.sales
```

This appends the rows to `my_catalog.default.sales`. If the table does not exist, it is created as an [Apache Iceberg](https://iceberg.apache.org/docs/latest/) table, the default format.

## Parameters

| Property | Required | Default | Description |
| -------- | -------- | ------- | ----------- |
| `table` | yes | | Table name, qualified as `catalog.schema.table` |
| `format` | no | `iceberg` | Table format used when the table is created or recreated, such as `delta` or `iceberg` |
| `mode` | no | `append` | How the `DataFrame` is written to the table |
| `keys` | no | | Column or list of columns that identify a row. Required by the `merge` mode and ignored by the others |
| `partition_by` | no | | Column name or list of column names used to partition the table when it is created or recreated |
| `properties` | no | | Table properties set when the table is created or recreated |
| `**options` | no | | Write options passed directly to Spark |

The properties shared by every Output are described in [Inputs, Transforms & Outputs](../concepts/steps.md#output).

## table

Table names follow the `catalog.schema.table` syntax. Any other shape is rejected with a `TiozinInputError` when the job is built:

- `my_catalog.default.sales` is accepted.
- `default.sales` is rejected because it has no catalog.
- `sales` is rejected because it has no catalog or schema.
- `my_catalog.default.sales.v2` is rejected because it has too many parts.

If `table` is missing, a `RequiredArgumentError` is raised instead.

## Table Creation

The table is always created when it does not exist, whatever the mode. On that first write, the whole `DataFrame` becomes the table content, and `format`, `partition_by`, and `properties` shape the new table.

```yaml
outputs:
  - kind: SparkTableOutput
    name: sales
    table: my_catalog.default.sales
    format: delta
    mode: append
```

When the table already exists, `mode` decides what happens.

## mode

Six modes are supported. Mode names are case-insensitive.

| Mode | Behavior on an existing table |
|---|---|
| `append` | Adds the rows to the table |
| `truncate` | Replaces all rows, preserving the table definition and history |
| `overwrite` | Replaces all rows and the table definition, keeping the history |
| `drop_overwrite` | Drops the table and creates it again, replacing all rows and the table definition and losing the history |
| `overwrite_partitions` | Replaces only the partitions present in the `DataFrame` |
| `merge` | Updates the rows that match `keys` and inserts the others |

Any other value raises a `TiozinInputError` that lists the supported modes. This error surfaces when the output runs, not when the job is built.

Both `overwrite` and `drop_overwrite` replace the rows and the table definition. The difference is the history: `overwrite` always keeps it, and `drop_overwrite` loses it.

> **Note:** On an existing [Delta Lake](https://docs.delta.io/latest/index.html) table, the `overwrite` mode fails with a `does not support truncate in batch mode` error on Spark 3.5.6+ with Delta 3.3.2 or older. This is a known Delta bug, [delta-io/delta#4671](https://github.com/delta-io/delta/issues/4671). On Spark 3.5.8, the write fails on Delta 3.2.0 and 3.3.2 and works on Delta 3.3.3. There are two ways out: upgrade Delta to 3.3.3, or use `drop_overwrite`, which loses the history.

For format-specific write behavior, see the [Iceberg Spark writes](https://iceberg.apache.org/docs/latest/spark-writes/) or [Delta Lake](https://docs.delta.io/latest/index.html) documentation.

## partition_by

Partition columns are applied when the table is created, or recreated by the `overwrite` and `drop_overwrite` modes. A single column name or a list is accepted.

```yaml
outputs:
  - kind: SparkTableOutput
    name: events
    table: my_catalog.default.events
    mode: overwrite_partitions
    partition_by: [country, day]
```

With `overwrite_partitions`, each run replaces only the `country` and `day` partitions present in the `DataFrame`. Other partitions stay untouched.

## keys

The `merge` mode uses `keys` to decide which incoming rows already exist in the table. A single column name or a list is accepted.

```yaml
outputs:
  - kind: SparkTableOutput
    name: customers
    table: my_catalog.default.customers
    mode: merge
    keys: [customer_id]
```

A row matches when it has the same values as a table row in all key columns. Matching rows are updated with every column from the `DataFrame`, and the rest are inserted. Rows already in the table that have no match in the `DataFrame` are kept.

If `mode` is `merge` and `keys` is empty, a `RequiredArgumentError` is raised when the output runs. Other modes ignore `keys`.

For format-specific merge behavior, see [Iceberg `MERGE INTO`](https://iceberg.apache.org/docs/latest/spark-writes/#merge-into) or [Delta Lake merge](https://docs.delta.io/latest/delta-update.html#upsert-into-a-table-using-merge).

## properties

Table properties are set only when the table is created, or recreated by the `overwrite` and `drop_overwrite` modes. Other modes leave the properties of an existing table unchanged.

```yaml
outputs:
  - kind: SparkTableOutput
    name: sales
    table: my_catalog.default.sales
    properties:
      write.format.default: parquet
```

Property names are format-specific. See the [Iceberg table properties](https://iceberg.apache.org/docs/latest/configuration/#table-properties) for the ones Iceberg accepts.

## Schema Evolution

`SparkTableOutput` always adds new `DataFrame` columns to an existing table, whatever the mode. This cannot be turned off. It covers nested fields in structs and in arrays of structs, on both [Iceberg](https://iceberg.apache.org/docs/latest/) and [Delta Lake](https://docs.delta.io/latest/index.html) tables.

Rows kept by the mode get `NULL` in the new columns. For example, `merge` keeps the rows with no match in the `DataFrame`, and those rows get `NULL`.

The column order of the `DataFrame` does not need to match the table.

Because `overwrite` and `drop_overwrite` replace the table definition, they also accept changed column types. In the other modes, a column type that cannot be changed fails the write. On Iceberg, for example, the error reads `Cannot change column type: id: string -> int`.

## Passing Extra Write Options

Any property not listed in the parameters table is passed to Spark as a write option. Which options take effect depends on the table format. See the [Iceberg write options](https://iceberg.apache.org/docs/latest/spark-configuration/#write-options) or the [Delta Lake batch writes](https://docs.delta.io/latest/delta-batch.html) documentation for the options each format accepts.

```yaml
outputs:
  - kind: SparkTableOutput
    name: sales
    table: my_catalog.default.sales
    target-file-size-bytes: 536870912
```

## Deferred Writes

The output returns a lazy writer instead of writing right away. Nothing is written to the table until the `save()` action is called on that writer.

## Lineage

The table is reported as the dataset written by this step. The catalog becomes the dataset namespace, and `schema.table` becomes the dataset name.

```yaml
table: my_catalog.default.sales
# → namespace: my_catalog
# → name: default.sales
```

See [How to Configure OpenLineage](../how-to/openlineage.md) for how datasets are emitted, and the [OpenLineage naming spec](https://openlineage.io/docs/spec/naming/) for the naming conventions.

## Related

- [SparkFileOutput](file-output.md)
- [Inputs, Transforms & Outputs](../concepts/steps.md)
