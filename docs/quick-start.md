# Quick Start

Build a working job manifest one section at a time. Each section introduces one group of fields, explains what they do, and shows the final result.

## Run a First Job

Create this file and run it:

```yaml
kind: LinearJob
name: my_first_job

org: acme
region: latam
domain: ecommerce
subdomain: retail
layer: refined
product: orders
model: daily_summary

runner:
  kind: NoOpRunner

inputs:
  - kind: NoOpInput
    name: read_data
```

```bash
tiozin run my_first_job.yaml
```

[`NoOpRunner`](tio_kernel/noops.md) and [`NoOpInput`](tio_kernel/noops.md) are built-in stubs. They do nothing and return empty results. Use them to run the full job lifecycle without connecting to any data source.

## Identity and description

`kind` selects the job implementation. [`LinearJob`](tio_kernel/linear-job.md) runs steps in fixed sequential order.

`name` identifies this job. It is not the execution ID. Tiozin generates a new execution ID each time the job runs.

`description` is optional. Write it so the person debugging this job months from now understands what it does.

```yaml
kind: LinearJob
name: orders_daily_summary
description: |
  Joins daily orders with the customer master and writes
  a regional summary to the refined layer.
  Runs daily after the raw ingestion window closes.
```

## Declare ownership

These fields record who requested this job, who maintains it, and who pays for it. All are optional.

```yaml
owner: data-platform
maintainer: analytics-team
cost_center: tio_scrooge
labels:
  criticality: high
```

`labels` stores free-form key-value metadata. Tiozin does not interpret it.

## Declare domain

These seven fields declare the organizational context of the data product this job produces. All seven are required. They are also available as template variables anywhere in the job: paths, connection strings, table names.

```yaml
org: acme
region: latam
domain: ecommerce
subdomain: retail
layer: refined
product: orders
model: daily_summary
```

`region` is a business territory (`brazil`, `latam`, `emea`), not a cloud region. `product` groups related `model`s. See [Jobs](concepts/jobs.md#domain) for the full definitions.

## Choose a runner

The runner is the execution engine for the job. It sets up connections, runs the pipeline steps, and tears everything down. Provider-specific options go directly under `runner`.

```yaml
runner:
  kind: NoOpRunner
  log_level: "{{ ENV.LOG_LEVEL }}"
```

`{{ ENV.LOG_LEVEL }}` reads from `os.environ` at execution time. See [Templates](templates.md) for all available variables.

## Declare inputs

Inputs read data from a source and pass it into the pipeline. At least one is required. Each input has a `kind`, a unique `name`, and any provider-specific fields.

```yaml
inputs:
  - kind: NoOpInput
    name: read_raw_orders
    description: Raw orders from the previous day.
    layer: raw
    path: "data/{{ layer }}/{{ product }}/date={{ DAY[-1] }}"
```

`layer: raw` on the input overrides the job-level `layer` for template rendering within this step. `DAY[-1]` resolves to yesterday's date.

## Add transforms

Transforms process the data between inputs and outputs. They are optional.

```yaml
transforms:
  - kind: NoOpTransform
    name: aggregate_by_region
    description: Aggregates order totals by country and region.
    strategy: sum
    group_by:
      - country
      - region
```

Tiozin passes `strategy`, `group_by`, and any other provider-specific fields directly to the plugin. The job does not validate them.

## Write outputs

Outputs write data to a destination. They are optional. A job can declare more than one output.

```yaml
outputs:
  - kind: NoOpOutput
    name: write_summary
    description: Regional order summary in the refined layer.
    path: "data/{{ domain }}-{{ layer }}/{{ product }}/{{ model }}/date={{ DAY[0] }}"
```

`DAY[0]` resolves to today's date.

## The complete job

```yaml
kind: LinearJob
name: orders_daily_summary
description: |
  Joins daily orders with the customer master and writes
  a regional summary to the refined layer.

owner: data-platform
maintainer: analytics-team
cost_center: tio_scrooge
labels:
  criticality: high

org: acme
region: latam
domain: ecommerce
subdomain: retail
layer: refined
product: orders
model: daily_summary

runner:
  kind: NoOpRunner
  log_level: "{{ ENV.LOG_LEVEL }}"

inputs:
  - kind: NoOpInput
    name: read_raw_orders
    description: Raw orders from the previous day.
    layer: raw
    path: "data/{{ layer }}/{{ product }}/date={{ DAY[-1] }}"

transforms:
  - kind: NoOpTransform
    name: aggregate_by_region
    description: Aggregates order totals by country and region.
    strategy: sum
    group_by:
      - country
      - region

outputs:
  - kind: NoOpOutput
    name: write_summary
    description: Regional order summary in the refined layer.
    path: "data/{{ domain }}-{{ layer }}/{{ product }}/{{ model }}/date={{ DAY[0] }}"
```

Run it:

```bash
tiozin run jobs/orders_daily_summary.yaml
```

## Next steps

Swap the `NoOp*` kinds for a provider from a [Tiozin Family](concepts/family.md). Spark and DuckDB families are included. Other families can be installed as packages.

- [Working with Jobs](working-with-jobs.md): all ways to define a job, pipeline shapes, and templating
- [Jobs](concepts/jobs.md): full field reference and execution model
- [Templates](templates.md): all available variables and date formats
