# Your First Job

Run your first pipeline in two minutes.

---

## Install

```bash
pip install tiozin
```

## The simplest job

A Tiozin job is a YAML file that describes where data comes from, what happens to it, and where it goes.

Save this as `my_first_job.yaml`:

```yaml
kind: LinearJob
name: my_first_job

owner: your-team@company.com
maintainer: your-team
cost_center: engineering

org: acme
region: us-east
domain: marketing
subdomain: campaigns
layer: refined
product: users
model: customers

runner:
  kind: NoOpRunner

inputs:
  - kind: NoOpInput
    name: load_data
    path: data/source

transforms:
  - kind: NoOpTransform
    name: process

outputs:
  - kind: NoOpOutput
    name: save_data
    path: data/output
```

Run it:

```bash
tiozin run my_first_job.yaml
```

Or from Python:

```python
from tiozin import TiozinApp

app = TiozinApp()
app.run("my_first_job.yaml")
```

Done.

---

## What's in a job?

Every job has the same structure:

| Section | Required | What it does |
|---|---|---|
| `kind` | yes | Which Job type to use (e.g. `LinearJob`) |
| `name` | yes | Unique identifier for this job |
| `runner` | yes | Execution backend (`NoOpRunner`, `SparkRunner`, `DuckdbRunner`) |
| `inputs` | yes | One or more data sources |
| `transforms` | no | Zero or more data transformations |
| `outputs` | no | Zero or more data destinations |

The `org`, `region`, `domain`, `subdomain`, `layer`, `product`, and `model` fields are required. They follow Data Mesh principles and power the templating system.

---

## A real Spark job

Install the Spark extras:

```bash
pip install tiozin[tio_spark]
```

A real ingestion job looks like this:

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
    path: data/customers.csv
    format: csv
    header: true
    inferSchema: true

transforms:
  - kind: SparkSqlTransform
    name: add_metadata
    query: |-
      SELECT *, current_timestamp() AS _created_at
      FROM @self

outputs:
  - kind: SparkFileOutput
    name: raw_customers
    path: .output/lake-{{domain}}-{{layer}}/{{product}}
    format: parquet
```

Notice the template variables `{{domain}}`, `{{layer}}`, and `{{product}}` — they resolve automatically from the job definition. See [Templates Reference](templates.md) for the full list.

---

## A real DuckDB job

For local, single-node workloads:

```bash
pip install tiozin[tio_duckdb]
```

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
    name: add_metadata
    query: |-
      SELECT *, current_timestamp AS _created_at
      FROM @self

outputs:
  - kind: DuckdbFileOutput
    name: raw_customers
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/
    format: parquet
    mode: overwrite
```

---

## What's next?

- [Jobs](concepts/jobs.md) — All job options and the LinearJob pipeline model
- [Runners](concepts/runners.md) — SparkRunner, DuckdbRunner, and NoOpRunner in detail
- [Inputs, Transforms & Outputs](concepts/steps.md) — All step types and their options
- [Templates Reference](templates.md) — Dynamic values, date variables, and filters
