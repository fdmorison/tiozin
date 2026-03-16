# tio_spark

`tio_spark` is the Tiozin provider family for Apache Spark. It runs pipelines on a managed `SparkSession`. Every step result is automatically available as a named temporary view for downstream SQL queries. The family supports both batch and streaming execution.

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

## Components

- [SparkRunner](runner.md)
- [SparkIcebergRunner](iceberg-runner.md)
- [SparkFileInput](file-input.md)
- [SparkSqlTransform](sql-transform.md)
- [SparkFileOutput](file-output.md)

To implement a custom Input, Transform, or Output from scratch, see [Creating Pluggable Tiozins](../extending/tiozins.md).

## Accessing the session

When writing a custom step in `tio_spark`, use `self.spark` to access the active Spark session. `self` here refers to the step instance: any class that extends `SparkTransform`, `SparkInput`, or `SparkOutput`.

```python
def transform(self, data: DataFrame) -> DataFrame:
    return data.withColumn("tax", data["amount"] * 0.1)
```

This session is the one created and managed by the runner. It is shared across all steps in the pipeline, so every step reads from and writes to the same Spark session. Do not create a new session with `SparkSession.builder.getOrCreate()` inside a step: that would interfere with the runner-managed session and bypass the temporary views registered by other steps.

`self.spark` is shorthand for:

```python
session = self.context.runner.session  # SparkSession
```

Both are equivalent. `self.spark` is the idiomatic form.
