# Job

A Job is Tiozin's top-level unit. It groups an execution engine, data sources, transformations, and destinations into a single declarative description of a pipeline.

## The contract

`Job` is an abstract base class. Any class that extends it and registers as a Tiozin plugin becomes a valid job type.

Three lifecycle methods define the execution contract:

| Method | Required | Description |
|---|---|---|
| `setup()` | no | Called before `submit()`. Override to run pre-execution initialization |
| `submit()` | yes | Implements the execution model. Must be overridden |
| `teardown()` | no | Called after `submit()`, even on failure. Override to run cleanup |

The framework wraps every job in a `JobProxy` before execution. The proxy handles context creation, template rendering, logging, and lifecycle sequencing. Your job implementation focuses only on coordinating its steps.

## Properties

### Identity

| Property | Required | Type | Default | Description |
|---|---|---|---|---|
| `kind` | yes | `str` | | Job type, used to resolve the plugin |
| `name` | yes | `str` | | Unique job identifier. Not the execution ID |
| `description` | no | `str` | `None` | Short description of the pipeline |

### Ownership

| Property | Required | Type | Default | Description |
|---|---|---|---|---|
| `owner` | no | `str` | `None` | Who required this job, a team, person or organization |
| `maintainer` | no | `str` | `None` | Who maintains this job, a team, person or organization |
| `cost_center` | no | `str` | `None` | Cost center charged for this job, such as a billing code or team |
| `labels` | no | `dict[str, str]` | `{}` | Free-form key-value metadata |

### Domain

These fields declare the organizational context and lineage of the data this job produces. All seven domain fields are required. They are also available as template variables in any YAML string property.

| Property | Required | Type | Default | Description |
|---|---|---|---|---|
| `org` | yes | `str` | | Organization that owns and produces this data |
| `region` | yes | `str` | | Business region of the domain team. This is a business territory (`latam`, `north-america`, `emea`), not a cloud infrastructure region like an AWS availability zone or GCP region |
| `domain` | yes | `str` | | Business domain that owns this pipeline (e.g. `ecommerce`, `marketing`) |
| `subdomain` | yes | `str` | | More specific area within the domain (e.g. `retail`, `campaigns`) |
| `layer` | yes | `str` | | Data layer: `raw`, `trusted`, `refined`, or any custom label |
| `product` | yes | `str` | | Data product being produced. A product groups one or more related models |
| `model` | yes | `str` | | Specific data representation within the product: a table, topic, file, collection, or any other structure. A product can expose one or more models |
| `namespace` | no | `str` | `TIO_JOB_NAMESPACE_TEMPLATE` | Job namespace. Accepts a plain string or a Jinja template rendered with the domain fields. When omitted, the value is derived from `TIO_JOB_NAMESPACE_TEMPLATE` |

### Execution

| Property | Required | Type | Default | Description |
|---|---|---|---|---|
| `cadence` | no | `Cadence` | `minutely` | Rhythm at which the job runs. Determines the nominal time of each execution. One of `minutely`, `hourly`, `daily`, `weekly`, or `monthly` |
| `backlog_policy` | no | `BacklogPolicy` | `stateless` | How the job participates in batch backlogs. One of `stateless`, `incremental`, or `consumer` |
| `max_batches_per_run` | no | `int` | `1` | Number of batches processed together as one transaction |

### Pipeline components

| Property | Required | Type | Default | Description |
|---|---|---|---|---|
| `runner` | yes | `Runner` | | Execution engine for this pipeline |
| `inputs` | yes | `list[Input]` | | Sources that provide data. Must contain at least one element |
| `transforms` | no | `list[Transform]` | `[]` | Steps that modify the data |
| `outputs` | no | `list[Output]` | `[]` | Destinations where data is written |

## Cadence

Cadence is the rhythm at which a job runs. The available cadences are `minutely` (the default), `hourly`, `daily`, `weekly`, and `monthly`.

For each job run, cadence determines its nominal time: the reference instant the run represents, not the moment it started. For instance, a daily job started at `2026-02-24T14:37:00` has a nominal time of `2026-02-24T00:00:00`, whereas an hourly job has a nominal time of `2026-02-24T14:00:00`.

Every step in the same run shares the job's nominal time. It is available on the execution context as `nominal_time` and in templates as `{{ job.nominal_time }}`.

Since batches are identified by nominal time, cadence also sets batch granularity: a daily job produces one batch per day, while an hourly job produces one batch per hour.

This mechanism ensures that runs are idempotent within the same cadence slot. After a successful run, Tiozin prevents another execution from writing duplicate data for the same batch. After a failure, another execution retries the same batch. A batch that has already succeeded must be deliberately replayed before it can run again.


## Backlog Policy

Every job declares a backlog policy that controls how it participates in batch backlogs. The available policies are `stateless` (the default), `incremental`, and `consumer`.

A `stateless` job runs without batches. It runs on every submit, even when the backlog is empty.

An `incremental` job produces and consumes its own batches, advancing its processing window after each successful execution. A `consumer` job consumes batches produced elsewhere, either by an upstream job or by an operator.

Both `incremental` and `consumer` are backlog-driven. They run only when the backlog holds batches to process and skip execution when the backlog is empty.

See [Batches](batches.md) for what batches, backlogs, and bookmarks are, and [How to Process Pending Work Incrementally](../how-to/batches.md) for incremental loads, bookmarks in practice, and consumer jobs.

## Max Batches Per Run

A submission works through the whole backlog, not a slice of it. `max_batches_per_run` sets how many batches are processed together in each transactional group: the default of 1 processes one batch at a time, while a higher value hands that many batches to a single call to `submit()`.

The batches in a group succeed or fail together. When a group fails, the job still works through the remaining groups before reporting the failure.

## Invariants

These constraints apply to all job types:

- `name`, `runner`, `org`, `region`, `domain`, `subdomain`, `layer`, `product`, and `model` are required. Missing any one raises an error at construction time.
- `inputs` must contain at least one element.
- `transforms` and `outputs` are optional. A job with no outputs is valid: the runner receives an empty plan.
- Unknown fields in YAML are silently ignored. You can annotate job definitions with custom fields without breaking execution.

## LinearJob

`LinearJob` is the built-in implementation, provided by the `tio_kernel` family. It runs steps in a fixed, sequential order:

1. All inputs run, in declaration order.
2. Transforms run in sequence. Each transform receives the output of the previous step. A `CoTransform` receives all current datasets at once (for joins, unions, or any multi-dataset operation).
3. All outputs write the same final dataset, independently.
4. The runner executes the resulting plan.

```text
┌───────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────┐
│  Input 1  │───►│             │    │             │    │ Output 1 │
├───────────┤    │ Transform 1 │───►│ Transform 2 │───►├──────────┤
│  Input N  │───►│             │    │             │    │ Output N │
└───────────┘    └─────────────┘    └─────────────┘    └──────────┘
```

`LinearJob` executes steps in a fixed forward order: inputs feed transforms, transforms feed outputs. Use it when data flows forward in one direction.

If your pipeline needs conditional execution, parallel steps, or DAG-style dependency control, extend `Job` directly and implement `submit()`. The framework keeps `Job` pluggable for exactly this reason.

## Custom implementations

Any class that extends `Job` and implements `submit()` becomes a valid job type:

```python
from typing import Any
from tiozin import Job


class MyJob(Job[Any]):
    def submit(self) -> Any:
        # implement your execution model here
        ...
```

Register it as a `tiozin.family` entry point and use `kind: MyJob` in YAML. See [Creating Pluggable Tiozins](../extending/tiozins.md) for registration details.

## A complete job

```yaml
kind: LinearJob
name: orders_daily_summary
namespace: acme.ecommerce
description: Aggregates daily order totals by region.

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

inputs:
  - kind: NoOpInput
    name: read_raw_orders
    path: "data/{{ layer }}/{{ product }}/date={{ DAY[-1] }}"
    # → data/refined/orders/date=2026-02-23

transforms:
  - kind: NoOpTransform
    name: aggregate

outputs:
  - kind: NoOpOutput
    name: write_summary
    path: "data/{{ domain }}-{{ layer }}/{{ product }}/{{ model }}/date={{ DAY[0] }}"
    # → data/ecommerce-refined/orders/daily_summary/date=2026-02-24
```

The same job programmatically:

```python
from tiozin import TiozinApp
from tiozin.family.tio_kernel import (
    LinearJob,
    NoOpInput,
    NoOpOutput,
    NoOpRunner,
    NoOpTransform,
)

job = LinearJob(
    name="orders_daily_summary",
    namespace="acme.ecommerce",
    description="Aggregates daily order totals by region.",
    owner="data-platform",
    maintainer="analytics-team",
    cost_center="tio_scrooge",
    labels={"criticality": "high"},
    org="acme",
    region="latam",
    domain="ecommerce",
    subdomain="retail",
    layer="refined",
    product="orders",
    model="daily_summary",
    runner=NoOpRunner(),
    inputs=[
        NoOpInput(
            name="read_raw_orders",
            path="data/{{ layer }}/{{ product }}/date={{ DAY[-1] }}",
        )
    ],
    transforms=[
        NoOpTransform(name="aggregate"),
    ],
    outputs=[
        NoOpOutput(
            name="write_summary",
            path="data/{{ domain }}-{{ layer }}/{{ product }}/{{ model }}/date={{ DAY[0] }}",
        )
    ],
)

app = TiozinApp()
app.run(job)
```
