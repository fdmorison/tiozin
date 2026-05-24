# Working with Jobs

Run a job from a file, a string, a manifest, or a Python object.

## From a file

The most common form. Pass a path to a `.yaml` or `.json` file:

```python
from tiozin import TiozinApp

app = TiozinApp()
app.run("jobs/orders_daily_summary.yaml")
```

Tiozin detects the format automatically. The path is resolved through the `JobRegistry`. The
default registry is [`FileJobRegistry`](tio_kernel/file-job-registry.md) from `tio_kernel`,
which reads from any path supported by fsspec: local paths, `s3://`, `gs://`, `az://`, and others.

## How `app.run()` resolves a job

When you pass a string, `TiozinApp.run()` first tries to parse it as YAML or JSON. If that
succeeds, the manifest is built directly without a registry lookup. If parsing fails, the string is
treated as an identifier and handed to the `JobRegistry`, which resolves it to a manifest.

A custom [`JobRegistry`](api.md) could resolve identifiers from a REST API, a database table, or
any other source. The identifier is just a string. The registry decides what to do with it.

In production, the recommended pattern is to store manifests in a registry-compatible backend and
trigger execution by identifier. This decouples job authoring from job execution and keeps the
execution layer stateless.

## From an inline string

Pass a raw YAML or JSON string. Tiozin parses it directly, bypassing the registry:

```python
app.run("""
kind: LinearJob
name: orders_daily_summary

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
    name: read_orders

transforms:
  - kind: NoOpTransform
    name: aggregate

outputs:
  - kind: NoOpOutput
    name: write_summary
""")
```

Useful when job definitions are assembled dynamically or come from an API.

## From a JobManifest

[`JobManifest`](api.md) is a typed Pydantic object. Use it when jobs come from a database, API, or
registry and you want validation at construction time:

```python
from tiozin import (
    TiozinApp,
    InputManifest,
    JobManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)

manifest = JobManifest(
    kind="LinearJob",
    name="orders_daily_summary",
    org="acme",
    region="latam",
    domain="ecommerce",
    subdomain="retail",
    layer="refined",
    product="orders",
    model="daily_summary",
    runner=RunnerManifest(kind="NoOpRunner"),
    inputs=[InputManifest(kind="NoOpInput", name="read_orders")],
    transforms=[TransformManifest(kind="NoOpTransform", name="aggregate")],
    outputs=[OutputManifest(kind="NoOpOutput", name="write_summary")],
)

app = TiozinApp()
app.run(manifest)
```

Plugin configuration also accepts plain dicts. `RunnerManifest(kind="NoOpRunner")` and
`{"kind": "NoOpRunner"}` are equivalent when passed to `JobManifest`.

## With Job.builder()

A fluent API for assembling jobs programmatically. Accepts dicts, manifest objects, or concrete
plugin instances interchangeably:

```python
from tiozin import Job, TiozinApp

job = (
    Job.builder()
    .with_kind("LinearJob")
    .with_name("orders_daily_summary")
    .with_org("acme")
    .with_region("latam")
    .with_domain("ecommerce")
    .with_subdomain("retail")
    .with_layer("refined")
    .with_product("orders")
    .with_model("daily_summary")
    .with_runner({"kind": "NoOpRunner"})
    .with_inputs({"kind": "NoOpInput", "name": "read_orders"})
    .with_transforms({"kind": "NoOpTransform", "name": "aggregate"})
    .with_outputs({"kind": "NoOpOutput", "name": "write_summary"})
    .build()
)

app = TiozinApp()
app.run(job)
```

## Direct instantiation

Instantiate a concrete job class with plugin objects directly. The most explicit form, with full
IDE support and no indirection:

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
    org="acme",
    region="latam",
    domain="ecommerce",
    subdomain="retail",
    layer="refined",
    product="orders",
    model="daily_summary",
    runner=NoOpRunner(),
    inputs=[NoOpInput(name="read_orders")],
    transforms=[NoOpTransform(name="aggregate")],
    outputs=[NoOpOutput(name="write_summary")],
)

app = TiozinApp()
app.run(job)
```

## Pipeline shapes

`transforms` and `outputs` are optional. `inputs` requires at least one element.

### Input only

No transforms, no outputs. Use for validation jobs, source probes, or dry-run scenarios:

```yaml
inputs:
  - kind: NoOpInput
    name: validate_source
```

### Extract-Load

Outputs receive the input data directly, with no transformation step. Use for copy or replication
pipelines that move data as-is:

```yaml
inputs:
  - kind: NoOpInput
    name: read_source

outputs:
  - kind: NoOpOutput
    name: write_destination
```

### No outputs

Transforms still run. Use when transforms perform writes or side effects directly (external API
calls, eager writes through the runner session):

```yaml
inputs:
  - kind: NoOpInput
    name: read_events

transforms:
  - kind: NoOpTransform
    name: emit_notification
```

### Fan-in

Multiple inputs load in sequence, then converge at the first transform. Use a `CoTransform` (such
as `SparkSqlTransform` or `DuckdbSqlTransform`) when that step needs to combine them:

```yaml
inputs:
  - kind: NoOpInput
    name: read_orders
  - kind: NoOpInput
    name: read_customers
  - kind: NoOpInput
    name: read_products

transforms:
  - kind: NoOpTransform
    name: join_data
```

### Multiple transforms

Transforms run in sequence, each receiving the output of the previous step:

```yaml
transforms:
  - kind: NoOpTransform
    name: filter_valid
  - kind: NoOpTransform
    name: deduplicate
  - kind: NoOpTransform
    name: aggregate
```

### Multiple outputs

All outputs write the same final dataset, independently. Use for fan-out scenarios such as writing
to a data warehouse, cache, and archive simultaneously:

```yaml
outputs:
  - kind: NoOpOutput
    name: write_to_warehouse
  - kind: NoOpOutput
    name: write_to_cache
  - kind: NoOpOutput
    name: write_to_archive
```

## namespace

Every job has a `namespace` field. Set it to any string:

```yaml
name: orders_daily_summary
namespace: acme-ecommerce
description: Daily order summary pipeline
```

It also accepts a Jinja template rendered with the job's domain fields:

```yaml
namespace: "{{org}}.{{domain}}"
# → acme.ecommerce

org: acme
region: latam
domain: ecommerce
subdomain: checkout
layer: refined
product: orders
model: daily_summary
```

Available variables: `org`, `region`, `domain`, `subdomain`, `layer`, `product`, `model`.

When `namespace` is not set, the value comes from `TIO_JOB_NAMESPACE_TEMPLATE`, which is itself a
Jinja template with the same available variables:

```bash
# default
TIO_JOB_NAMESPACE_TEMPLATE="{{org}}.{{region}}.{{domain}}.{{subdomain}}"
# → acme.latam.ecommerce.checkout

# custom deployment-wide
TIO_JOB_NAMESPACE_TEMPLATE="{{org}}.{{domain}}"
# → acme.ecommerce
```

## Templating

All string properties in job YAML are Jinja2 templates rendered at execution time. Referencing an
undefined variable raises an error.

The two most common variable sources are domain fields and date offsets.

### Domain variables

The domain fields declared at the job level (`org`, `region`, `domain`, `subdomain`, `layer`,
`product`, `model`) are available as template variables in any string property across the runner,
inputs, transforms, and outputs:

```yaml
domain: ecommerce
layer: refined
product: orders

inputs:
  - kind: NoOpInput
    name: read_raw
    path: "data/{{ layer }}/{{ product }}"
    # → data/refined/orders

outputs:
  - kind: NoOpOutput
    name: write_refined
    path: "data/{{ domain }}-{{ layer }}/{{ product }}"
    # → data/ecommerce-refined/orders
```

A step can override any domain field locally. `layer: raw` on an input uses `raw` for template
rendering within that step only, leaving the job-level `layer` unchanged.

### Date variables

`DAY` is a date object anchored to the job's execution time. Use index syntax for relative offsets:
`DAY[0]` is today, `DAY[-1]` is yesterday, `DAY[7]` is seven days ahead.

```yaml
inputs:
  - kind: NoOpInput
    name: read_yesterday
    path: "data/raw/date={{ DAY[-1] }}"
    # → data/raw/date=2026-02-23

outputs:
  - kind: NoOpOutput
    name: write_today
    path: "data/refined/date={{ DAY[0] }}"
    # → data/refined/date=2026-02-24
```

See [Templates](templates.md) for all available variables, date formats, environment variable
access, and temporary workspace paths.
