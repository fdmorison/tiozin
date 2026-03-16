# Examples

All examples live under [`examples/jobs/`](../examples/jobs/) in the repository. Each is a self-contained job manifest you can run directly with `tiozin run`.

## How the folder structure works

The `examples/jobs/` tree is also a reference for how to organize jobs in a real repository. Jobs are grouped by data product, and each job within a product gets its own YAML file named after its layer or purpose:

```text
examples/jobs/
  spark/
    ecommerce/
      ingestion_customers_job.yaml
      ingestion_orders_job.yaml
      refined_customer_orders_job.yaml
    shakespeare/
      ingestion_job.yaml
      refined_hamlet_job.yaml
      ...
```

One folder per data product. One YAML per job. No shared state between files.

## Two transform styles

Each scenario includes examples of both approaches to business logic:

- **SQL transforms** (`SparkSqlTransform`, `DuckdbSqlTransform`): logic lives in the query, the plugin is generic. The ecommerce examples follow this pattern.
- **Plugin transforms** (`SparkWordCountTransform`, `DuckdbWordCountTransform`): logic is fully encapsulated in the plugin class, and the YAML only declares parameters. The Shakespeare examples follow this pattern.

Both approaches are valid. SQL transforms are faster to write for ad hoc logic. Plugin transforms are easier to test, version, and reuse across jobs.

## Minimal

**[`examples/jobs/dummy.yaml`](../examples/jobs/dummy.yaml)**

The starting point. No additional packages needed, no execution engine to configure. Shows the full YAML layout: job metadata, domain fields, runner, inputs, transforms, and outputs. Also demonstrates Jinja templates in path fields.

```bash
tiozin run examples/jobs/dummy.yaml
```

## Ecommerce

A two-step pipeline split across three jobs: raw ingestion for customers and orders, followed by a refined join. The same scenario is implemented in both Spark and DuckDB so you can compare the two side by side. Only the `kind` fields change. The job structure, YAML layout, and intent are identical.

### Spark

| File | What it shows |
|---|---|
| [`spark/ecommerce/ingestion_customers_job.yaml`](../examples/jobs/spark/ecommerce/ingestion_customers_job.yaml) | CSV ingestion to raw layer with `SparkFileInput` and `SparkFileOutput` |
| [`spark/ecommerce/ingestion_orders_job.yaml`](../examples/jobs/spark/ecommerce/ingestion_orders_job.yaml) | Same ingestion pattern for the orders dataset |
| [`spark/ecommerce/refined_customer_orders_job.yaml`](../examples/jobs/spark/ecommerce/refined_customer_orders_job.yaml) | Multiple inputs joined in SQL, chained transforms with `@data`, parameterized queries with `args:`, and output partitioned by column |

### DuckDB

| File | What it shows |
|---|---|
| [`duckdb/ecommerce/ingestion_customers_job.yaml`](../examples/jobs/duckdb/ecommerce/ingestion_customers_job.yaml) | Same ingestion pattern as the Spark version, running locally on DuckDB |
| [`duckdb/ecommerce/ingestion_orders_job.yaml`](../examples/jobs/duckdb/ecommerce/ingestion_orders_job.yaml) | Orders ingestion on DuckDB |
| [`duckdb/ecommerce/refined_customer_orders_job.yaml`](../examples/jobs/duckdb/ecommerce/refined_customer_orders_job.yaml) | Join and filter with `DuckdbSqlTransform`, `@data` token, and parameterized queries |

## Shakespeare

A realistic multi-job data pipeline using the complete works of Shakespeare as the source dataset. An ingestion job loads raw texts into the lake. Each subsequent job refines one work independently. The scenario demonstrates how a collection of independent, reusable jobs composes into a larger pipeline.

### Spark

| File | What it shows |
|---|---|
| [`spark/shakespeare/ingestion_job.yaml`](../examples/jobs/spark/shakespeare/ingestion_job.yaml) | Ingestion of source texts to the raw layer |
| [`spark/shakespeare/refined_hamlet_job.yaml`](../examples/jobs/spark/shakespeare/refined_hamlet_job.yaml) | Refinement of Hamlet |
| [`spark/shakespeare/refined_sonnets_job.yaml`](../examples/jobs/spark/shakespeare/refined_sonnets_job.yaml) | Refinement of the Sonnets |
| [`spark/shakespeare/refined_kinglear_job.yaml`](../examples/jobs/spark/shakespeare/refined_kinglear_job.yaml) | Refinement of King Lear |
| [`spark/shakespeare/refined_loverscomplaint_job.yaml`](../examples/jobs/spark/shakespeare/refined_loverscomplaint_job.yaml) | Refinement of A Lover's Complaint |

### DuckDB

| File | What it shows |
|---|---|
| [`duckdb/shakespeare/ingestion_job.yaml`](../examples/jobs/duckdb/shakespeare/ingestion_job.yaml) | Same ingestion, running locally on DuckDB |
| [`duckdb/shakespeare/refined_hamlet_job.yaml`](../examples/jobs/duckdb/shakespeare/refined_hamlet_job.yaml) | Hamlet refinement on DuckDB |
| [`duckdb/shakespeare/refined_sonnets_job.yaml`](../examples/jobs/duckdb/shakespeare/refined_sonnets_job.yaml) | Sonnets refinement on DuckDB |
| [`duckdb/shakespeare/refined_kinglear_job.yaml`](../examples/jobs/duckdb/shakespeare/refined_kinglear_job.yaml) | King Lear refinement on DuckDB |
| [`duckdb/shakespeare/refined_loverscomplaint_job.yaml`](../examples/jobs/duckdb/shakespeare/refined_loverscomplaint_job.yaml) | A Lover's Complaint refinement on DuckDB |

## Iceberg

**[`spark/iceberg/example_iceberg_job.yaml`](../examples/jobs/spark/iceberg/example_iceberg_job.yaml)**

Minimal Spark + Iceberg pipeline using AWS Glue as the catalog. Shows `SparkIcebergRunner` configuration: catalog name, type, warehouse path, and the `jars_packages` needed for the Iceberg AWS bundle.

## DuckDB + PostgreSQL

**[`duckdb/postgres/postgres_output.yaml`](../examples/jobs/duckdb/postgres/postgres_output.yaml)**

Loads customer data from CSV into PostgreSQL using DuckDB as the execution engine. Shows `DuckdbPostgresOutput` with environment-based credentials (`PGHOST`, `PGUSER`, etc.) and multiple outputs writing to different tables in the same run.
