# Examples

Ready-to-run examples organized by provider. Full examples live in the `examples/jobs/` directory of the repository.

## Minimal (NoOp)

The starting point. No additional packages needed, no execution engine to configure. Use this to understand the full YAML layout: job metadata, domain fields, runner, inputs, transforms, and outputs. It also shows Jinja templates in path fields.

```yaml
kind: LinearJob
name: example_job
description: Minimal example job demonstrating a basic ETL pipeline.

owner: tiozin@tiozin.com
maintainer: tiozin
cost_center: tio_scrooge

org: tiozin
region: latam
domain: marketing
subdomain: campaigns
layer: refined
product: users
model: customers

runner:
  kind: NoOpRunner

inputs:
  - kind: NoOpInput
    name: load_it
    layer: raw
    path: .output/lake-{{domain}}-raw/{{product}}/{{model}}/date={{ DAY[-1] }}

transforms:
  - kind: NoOpTransform
    name: do_something

outputs:
  - kind: NoOpOutput
    name: save_it
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/{{model}}/{{ today }}
```

Run it:

```bash
tiozin run examples/jobs/dummy.yaml
```

## Spark: CSV to Parquet ingestion

The standard raw ingestion pattern on Spark. A single input reads a CSV, a transform injects traceability metadata (`run_id`, `nominal_time`, `created_at`), and an output writes Parquet to the raw layer. Shows `SparkRunner`, `SparkFileInput`, `SparkSqlTransform`, and `SparkFileOutput` working together for the first time.

```yaml
kind: LinearJob
name: customers_ingestion

owner: data@company.com
maintainer: data-team
cost_center: data

org: acme
region: europe
domain: ecommerce
subdomain: retail
layer: raw
product: customers
model: customers

runner:
  kind: SparkRunner

inputs:
  - kind: SparkFileInput
    name: customers_source
    description: Customer master data from source system.
    path: data/customers.csv
    format: csv
    header: true
    inferSchema: true

transforms:
  - kind: SparkSqlTransform
    name: metadata
    description: Adds ingestion metadata.
    query: |-
      SELECT
          *,
          '{{job.run_id}}'       AS _raw_run_id,
          '{{job.nominal_time}}' AS _raw_nominal_date,
          current_timestamp()    AS _raw_created_at
      FROM @data

outputs:
  - kind: SparkFileOutput
    name: customers_raw
    description: Raw customer data in parquet format.
    path: .output/lake-{{domain}}-{{layer}}/{{product}}
    format: parquet
```

## Spark: Multi-input join with parameterized filter

Shows four patterns not in the previous example: multiple inputs joined by name in SQL, chained transforms where each `@data` refers to the previous output, a parameterized query with `args:` to keep literals out of SQL, and output partitioned by column. Each pattern is independent. You can use any combination of them.

```yaml
kind: LinearJob
name: high_value_orders

owner: data@company.com
maintainer: data-team
cost_center: data

org: acme
region: europe
domain: ecommerce
subdomain: retail
layer: refined
product: high_value_orders
model: high_value_orders

runner:
  kind: SparkRunner

inputs:
  - kind: SparkFileInput
    name: customers
    path: .output/lake-ecommerce-raw/customers
    format: parquet

  - kind: SparkFileInput
    name: orders
    path: .output/lake-ecommerce-raw/orders
    format: parquet

transforms:
  - kind: SparkSqlTransform
    name: customer_orders
    query: |-
      SELECT c.id, c.name, c.country, o.id AS order_id, o.total, o.status
      FROM customers c
      JOIN orders o ON c.id = o.customer_id

  - kind: SparkSqlTransform
    name: completed_orders
    query: SELECT * FROM @data WHERE status = 'completed'

  - kind: SparkSqlTransform
    name: high_value
    query: SELECT * FROM @data WHERE total > :min_total
    args:
      min_total: 500

outputs:
  - kind: SparkFileOutput
    name: sink
    path: .output/lake-{{domain}}-{{layer}}/{{product}}
    format: parquet
    partition_by:
      - country
```

## DuckDB: CSV to Parquet ingestion

The same ingestion pattern as the Spark example above, but running on DuckDB locally. Compare the two side by side: only the `kind` fields change. The job structure, YAML layout, and intent are identical. This is the portability guarantee Tiozin provides across execution engines.

```yaml
kind: LinearJob
name: customers_ingestion

owner: data@company.com
maintainer: data-team
cost_center: data

org: acme
region: europe
domain: ecommerce
subdomain: retail
layer: raw
product: customers
model: customers

runner:
  kind: DuckdbRunner

inputs:
  - kind: DuckdbFileInput
    name: customers_source
    path: data/customers.csv
    format: csv
    header: true

transforms:
  - kind: DuckdbSqlTransform
    name: metadata
    query: |-
      SELECT
          *,
          '{{job.run_id}}'       AS _raw_run_id,
          current_timestamp      AS _raw_created_at
      FROM @data

outputs:
  - kind: DuckdbFileOutput
    name: customers_raw
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/
    format: parquet
    mode: overwrite
```

## DuckDB: Extensions and attached databases

Shows runner-level configuration: `extensions` loads `httpfs` and `spatial` so DuckDB can read from S3 and run geospatial queries; `attach` mounts an external DuckDB file under an alias. The input reads from an S3 path with a date template. The transform joins across databases using the `staging.table` syntax that the attach alias provides.

```yaml
kind: LinearJob
name: cross_db_analysis

owner: data@company.com
maintainer: data-team
cost_center: data

org: acme
region: us-east
domain: analytics
subdomain: reporting
layer: refined
product: summary
model: monthly_summary

runner:
  kind: DuckdbRunner
  extensions:
    - httpfs
    - spatial
  attach:
    staging: /data/staging.duckdb

inputs:
  - kind: DuckdbFileInput
    name: events
    path: s3://my-bucket/events/{{ D[-1].deep_date }}/
    format: parquet

transforms:
  - kind: DuckdbSqlTransform
    name: enriched
    query: |-
      SELECT e.*, s.category
      FROM events e
      JOIN staging.categories s ON e.category_id = s.id

outputs:
  - kind: DuckdbFileOutput
    name: summary_output
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/{{ D[-1] }}/
    format: parquet
    mode: overwrite
```
