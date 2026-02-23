# Working with Jobs

A Job describes a complete data pipeline: where data comes from, how it's transformed, and where it goes.

---

## The simplest job

```yaml
kind: LinearJob
name: my_job

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
    name: load
    path: data/input
```

`name`, `org`, `region`, `domain`, `subdomain`, `layer`, `product`, `model`, `runner`, and at least one input are all required.

---

## LinearJob — how data flows

`LinearJob` is the standard job type. Data flows forward in a straight line:

```
Inputs → Transforms → Outputs
```

1. All inputs are read and produce datasets
2. Transforms are applied one by one in order, each receiving the result of the previous step
3. Outputs each receive the final transformed dataset

### Multiple inputs

When you declare multiple inputs, the first transform must handle all datasets at once — typically a join, union, or merge. `SparkSqlTransform` and `DuckdbSqlTransform` both support this by referencing each input by its `name`.

```yaml
inputs:
  - kind: SparkFileInput
    name: customers
    path: data/customers

  - kind: SparkFileInput
    name: orders
    path: data/orders

transforms:
  - kind: SparkSqlTransform
    name: joined
    query: |-
      SELECT c.name, o.total
      FROM customers c
      JOIN orders o ON c.id = o.customer_id
```

### Multiple outputs

When you declare multiple outputs, all of them write the same final dataset independently.

```yaml
outputs:
  - kind: SparkFileOutput
    name: parquet_sink
    path: .output/lake/customers
    format: parquet

  - kind: SparkFileOutput
    name: csv_export
    path: .output/exports/customers
    format: csv
```

---

## Job metadata

Every job has two groups of metadata: governance and Data Mesh.

### Governance

| Field | Required | Description |
|---|---|---|
| `name` | yes | Unique job identifier |
| `description` | no | Short description of the pipeline |
| `owner` | no | Team that required this job |
| `maintainer` | no | Team that maintains this job |
| `cost_center` | no | Team that pays for this job |
| `labels` | no | Key-value pairs for additional metadata |

### Data Mesh

| Field | Required | Description |
|---|---|---|
| `org` | yes | Organization producing the data product |
| `region` | yes | Business region (e.g. `europe`, `us-east`) |
| `domain` | yes | Domain team (e.g. `ecommerce`, `marketing`) |
| `subdomain` | yes | Subdomain within the domain (e.g. `retail`, `campaigns`) |
| `layer` | yes | Data layer: `raw`, `trusted`, `refined`, or custom |
| `product` | yes | Data product being produced (e.g. `customers`) |
| `model` | yes | Data model within the product (e.g. `customers_v2`) |

All Data Mesh fields are available as template variables inside YAML string values. See [Templates](../templates.md).

---

## Running a job

From the command line:

```bash
tiozin run path/to/job.yaml
```

From Python:

```python
from tiozin import TiozinApp

app = TiozinApp()
app.run("path/to/job.yaml")
```

`TiozinApp.run()` accepts:
- A path to a YAML or JSON file
- A raw YAML or JSON string
- A `JobManifest` object
- A `Job` instance

---

## Labels

Use `labels` to attach free-form key-value metadata to a job:

```yaml
labels:
  team: data-platform
  env: production
  pipeline: nightly
```

Labels are stored in the execution context but not used by the framework for execution logic.

---

## Unknown fields

Fields not recognized by the framework are silently ignored. You can add custom annotations to job YAML without breaking anything:

```yaml
kind: LinearJob
name: my_job
my_custom_annotation: some_value   # ignored by Tiozin
...
```
