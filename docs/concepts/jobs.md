# Job

A Job is Tiozin's top-level unit. It groups an execution engine, data sources, transformations, and destinations into a single declarative description of a pipeline.

## The contract

`Job` is an abstract base class. Any class that extends it and registers as a Tiozin plugin becomes a valid job type.

Three lifecycle methods define the contract:

| Method | Required | Description |
|---|---|---|
| `setup()` | no | Called before `submit()`. Override to run pre-execution initialization |
| `submit()` | yes | Implements the execution model. Must be overridden |
| `teardown()` | no | Called after `submit()`, even on failure. Override to run cleanup |

The framework wraps every job in a `JobProxy` before execution. The proxy handles context creation, template rendering, logging, and lifecycle sequencing. Your job implementation focuses only on coordinating its steps.

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

`LinearJob` has no branches, no conditions, no retry logic, and no dependency rules between steps. Use it when data flows forward in one direction.

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
| `owner` | no | `str` | `None` | Team that requested this job |
| `maintainer` | no | `str` | `None` | Team that maintains this job |
| `cost_center` | no | `str` | `None` | Team that pays for this job |
| `labels` | no | `dict[str, str]` | `{}` | Free-form key-value metadata |

### Domain

These fields declare the organizational context and lineage of the data this job produces. All seven are required. They are also available as template variables in any YAML string property.

| Property | Required | Type | Description |
|---|---|---|---|
| `org` | yes | `str` | Organization that owns and produces this data |
| `region` | yes | `str` | Business region of the domain team. This is a business territory (`us-east`, `latam`, `emea`), not a cloud infrastructure region like an AWS availability zone or GCP region |
| `domain` | yes | `str` | Business domain that owns this pipeline (e.g. `ecommerce`, `marketing`) |
| `subdomain` | yes | `str` | More specific area within the domain (e.g. `retail`, `campaigns`) |
| `layer` | yes | `str` | Data layer: `raw`, `trusted`, `refined`, or any custom label |
| `product` | yes | `str` | Data product being produced. A product groups one or more related models |
| `model` | yes | `str` | Specific data representation within the product: a table, topic, file, collection, or any other structure. A product can expose one or more models |

### Pipeline components

| Property | Required | Type | Default | Description |
|---|---|---|---|---|
| `runner` | yes | `Runner` | | Execution engine for this pipeline |
| `inputs` | yes | `list[Input]` | min 1 | Sources that provide data |
| `transforms` | no | `list[Transform]` | `[]` | Steps that modify the data |
| `outputs` | no | `list[Output]` | `[]` | Destinations where data is written |

## Invariants

These constraints apply to all job types, including `LinearJob`:

- `name`, `runner`, `org`, `region`, `domain`, `subdomain`, `layer`, `product`, and `model` are required. Missing any one raises an error at construction time.
- `inputs` must contain at least one element.
- `transforms` and `outputs` are optional. A job with no outputs is valid: the runner receives an empty plan.
- Unknown fields in YAML are silently ignored. You can annotate job definitions with custom fields without breaking execution.

## A complete job

```yaml
kind: LinearJob
name: orders_daily_summary
description: Aggregates daily order totals by region.

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

inputs:
  - kind: NoOpInput
    name: read_raw_orders
    path: "data/{{ layer }}/{{ product }}/date={{ D[-1] }}"
    # → data/refined/orders/date=2026-02-23

transforms:
  - kind: NoOpTransform
    name: aggregate

outputs:
  - kind: NoOpOutput
    name: write_summary
    path: "data/{{ domain }}-{{ layer }}/{{ product }}/{{ model }}/date={{ D[0] }}"
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
    description="Aggregates daily order totals by region.",
    owner="data-platform",
    maintainer="analytics-team",
    cost_center="tio_scrooge",
    labels={"criticality": "high"},
    org="acme",
    region="us-east",
    domain="ecommerce",
    subdomain="retail",
    layer="refined",
    product="orders",
    model="daily_summary",
    runner=NoOpRunner(),
    inputs=[
        NoOpInput(
            name="read_raw_orders",
            path="data/{{ layer }}/{{ product }}/date={{ D[-1] }}",
        )
    ],
    transforms=[
        NoOpTransform(name="aggregate"),
    ],
    outputs=[
        NoOpOutput(
            name="write_summary",
            path="data/{{ domain }}-{{ layer }}/{{ product }}/{{ model }}/date={{ D[0] }}",
        )
    ],
)

app = TiozinApp()
app.run(job)
```
