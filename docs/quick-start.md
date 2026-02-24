# Quick Start

This tutorial walks through building a real job field by field. By the end, you will have a complete job manifest and understand what each part does.

## Run your first job

Before anything else, create this file and run it:

```yaml
kind: LinearJob
name: my_first_job

org: acme
region: us-east
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

`NoOpRunner` and `NoOpInput` are built-in dry-run implementations. They validate the job structure without touching any real data source. Use them while building.

## Identity and description

`kind` selects the job implementation. `LinearJob` runs steps in fixed sequential order and is the standard choice.

`name` is the unique identifier for this job in your system. It is not the execution ID — a new execution ID is generated every time the job runs.

`description` is optional. Write it for whoever will be debugging this job at 3am.

```yaml
kind: LinearJob
name: orders_daily_summary
description: |
  Joins daily orders with the customer master and writes
  a regional summary to the refined layer.
  Runs daily after the raw ingestion window closes.
```

## Declare ownership

Who requested this job, who maintains it, and who pays for it. All fields are optional.

```yaml
owner: data-platform
maintainer: analytics-team
cost_center: tio_scrooge
labels:
  criticality: high
```

`labels` is free-form key-value metadata for your tooling.

## Declare domain

These seven fields define where this job lives in your data organization. They are all required. They also become available as template variables anywhere in the job — in paths, connection strings, table names, and so on.

```yaml
org: acme
region: us-east
domain: ecommerce
subdomain: retail
layer: refined
product: orders
model: daily_summary
```

`region` is a business territory (`brazil`, `latam`, `emea`), not a cloud region. `product` groups related `model`s. See [Jobs](concepts/jobs.md#domain) for the full definitions.

## Choose a runner

The runner manages the session and executes the plan. Provider-specific options go directly under `runner`.

```yaml
runner:
  kind: NoOpRunner
  log_level: "{{ ENV.LOG_LEVEL }}"
```

`{{ ENV.LOG_LEVEL }}` reads from `os.environ` at execution time. See [Templates](templates.md) for all available variables.

## Declare inputs

Inputs read data from sources. At least one is required. Each input has a `kind`, a unique `name`, and any provider-specific fields.

```yaml
inputs:
  - kind: NoOpInput
    name: read_raw_orders
    description: Raw orders from the previous day.
    layer: raw
    path: "data/{{ layer }}/{{ product }}/date={{ D[-1] }}"
```

`layer: raw` on the input overrides the job-level `layer` for template rendering within this step. `D[-1]` resolves to yesterday's date.

## Add transforms

Transforms receive data from the previous step, apply logic, and pass the result forward. They are optional.

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

Provider-specific fields like `strategy` and `group_by` pass through to the plugin without validation at the job level.

## Write outputs

Outputs write the final dataset to a destination. They are optional, and you can write to multiple destinations independently.

```yaml
outputs:
  - kind: NoOpOutput
    name: write_summary
    description: Regional order summary in the refined layer.
    path: "data/{{ domain }}-{{ layer }}/{{ product }}/{{ model }}/date={{ D[0] }}"
```

`D[0]` resolves to today's date.

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
region: us-east
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
    path: "data/{{ layer }}/{{ product }}/date={{ D[-1] }}"

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
    path: "data/{{ domain }}-{{ layer }}/{{ product }}/{{ model }}/date={{ D[0] }}"
```

Run it:

```bash
tiozin run jobs/orders_daily_summary.yaml
```

## Next steps

Replace the `NoOp*` kinds with real provider implementations from a [Tiozin Family](concepts/family.md) — Spark, DuckDB, or any other installed family.

- [Working with Jobs](working-with-jobs.md): all ways to define a job, pipeline shapes, and templating
- [Jobs](concepts/jobs.md): full field reference and execution model
- [Templates](templates.md): all available variables and date formats
