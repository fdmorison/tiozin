# Examples

Ready-to-run examples organized by provider. Full examples live in the `examples/jobs/` directory of the repository.

---

## Minimal (NoOp)

The simplest possible job. Runs without any additional dependencies. Good for understanding the structure.

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

---

## Spark — CSV to Parquet ingestion

Reads a CSV file and writes it as Parquet to the raw layer, adding ingestion metadata.

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
      FROM @self

outputs:
  - kind: SparkFileOutput
    name: customers_raw
    description: Raw customer data in parquet format.
    path: .output/lake-{{domain}}-{{layer}}/{{product}}
    format: parquet
```

---

## Spark — Multi-input join with parameterized filter

Joins two inputs, filters the result, and writes partitioned Parquet output.

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
    query: SELECT * FROM @self WHERE status = 'completed'

  - kind: SparkSqlTransform
    name: high_value
    query: SELECT * FROM @self WHERE total > :min_total
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

---

## DuckDB — CSV to Parquet ingestion

Same ingestion pattern, local DuckDB execution.

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
      FROM @self

outputs:
  - kind: DuckdbFileOutput
    name: customers_raw
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/
    format: parquet
    mode: overwrite
```

---

## DuckDB — Extensions and attached databases

Uses DuckDB extensions and reads from an attached external database.

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
