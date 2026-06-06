# tio_spark

`tio_spark` is the Tiozin Family for Apache Spark. It runs jobs on a managed `SparkSession` and supports both batch and streaming execution.

> **Note:** `tio_spark` currently lives inside the `tiozin` core repository. In a future major version it will be extracted into its own independent package. Creating new provider families inside the core repository is not allowed.

## Installation

```bash
pip install tiozin[tio_spark]
```

## How data flows between steps

Every step in `tio_spark` produces a Spark `DataFrame`. After each step runs, the framework registers that DataFrame as a named temporary view using the step's slug. The slug is the slugified version of the step's `name` field: lowercase, with spaces and special characters replaced by underscores.

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

This view registration happens at the framework level for all inputs and transforms.

## Components

- [SparkRunner](runner.md)
- [SparkIcebergRunner](iceberg-runner.md)
- [SparkFileInput](file-input.md)
- [SparkJsonSchemaInferenceTransform](json-schema-inference-transform.md)
- [SparkSqlTransform](sql-transform.md)
- [SparkFileOutput](file-output.md)
- [SparkWordCountTransform](../examples.md#shakespeare)

To implement a custom Input, Transform, or Output from scratch, see [Creating Pluggable Tiozins](../extending/tiozins.md).

## Accessing the Spark session

Use `self.spark` to access the active `SparkSession` from any custom step that extends `SparkInput`, `SparkTransform`, `SparkCoTransform`, or `SparkOutput`.

```python
def transform(self, data: DataFrame) -> DataFrame:
    return self.spark.sql("SELECT * FROM some_view")
```

This session is created and managed by the runner. It is shared across all steps in the job, so every step reads from and writes to the same session. Do not call `SparkSession.builder.getOrCreate()` inside a step. That can interfere with the runner-managed session and bypass the temporary views registered by other steps.

`self.spark` is shorthand for:

```python
session = self.context.runner.session  # SparkSession
```

Both are equivalent. `self.spark` is the idiomatic form.
