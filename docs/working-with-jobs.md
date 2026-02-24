# Working with Jobs

Run a job from a file, a string, a manifest, or a Python object.

## YAML file

The standard form for production. Pass a path to a `.yaml` file:

```python
from tiozin import TiozinApp

app = TiozinApp()
app.run("jobs/orders_daily_summary.yaml")
```

JSON files work the same way. Tiozin detects the format automatically.

## How `app.run()` resolves a job

When you pass a file path, `TiozinApp.run()` hands the identifier to the `JobRegistry` backend, which resolves it to a manifest and runs it.

The default backend is `FileJobRegistry` (from `tio_kernel`). It reads YAML or JSON from any path supported by fsspec: local paths, `s3://`, `gs://`, `az://`, and others.

A custom `JobRegistry` could resolve identifiers from a REST API, a database table, or any other source. The identifier is just a string. The registry decides what to do with it.

In production, the recommended pattern is to store manifests in a registry-compatible backend and trigger execution by identifier. This decouples job authoring from job execution, enables versioning, and keeps the execution layer stateless.

## Inline string

Pass a raw YAML or JSON string. Useful when job definitions are assembled dynamically or come from an API:

```python
app.run("""
kind: LinearJob
name: orders_daily_summary

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
    name: read_orders

transforms:
  - kind: NoOpTransform
    name: aggregate

outputs:
  - kind: NoOpOutput
    name: write_summary
""")
```

When you pass a raw string or a `JobManifest` object, Tiozin bypasses the registry and runs the job without a lookup.

## JobManifest

A typed Pydantic object. Use it when jobs come from a database, API, or registry and you want validation at construction time:

```python
from tiozin import TiozinApp
from tiozin.api.metadata.job_manifest import (
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
    region="us-east",
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

Plugin configuration also accepts plain dicts. `RunnerManifest(kind="NoOpRunner")` and `{"kind": "NoOpRunner"}` are equivalent.

## Job.builder()

A fluent API for assembling jobs programmatically. Accepts dicts, manifest objects, or concrete plugin instances interchangeably:

```python
from tiozin import Job, TiozinApp

job = (
    Job.builder()
    .with_kind("LinearJob")
    .with_name("orders_daily_summary")
    .with_org("acme")
    .with_region("us-east")
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

Instantiate a concrete job class with plugin objects directly. The most explicit form, with full IDE support and no indirection:

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
    region="us-east",
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

No transforms, no outputs. The runner receives an empty plan. Use for validation jobs, source probes, or dry-run scenarios:

```yaml
inputs:
  - kind: NoOpInput
    name: validate_source
```

### Extract-Load (No Transform)

Outputs receive the input data directly. No transformation step. Use for copy or replication pipelines that move data as-is:

```yaml
inputs:
  - kind: NoOpInput
    name: read_source

outputs:
  - kind: NoOpOutput
    name: write_destination
```

### No outputs

Transforms still run. The runner receives an empty plan. Use when transforms perform writes or side effects directly (external API calls, eager writes through the runner session):

```yaml
inputs:
  - kind: NoOpInput
    name: read_events

transforms:
  - kind: NoOpTransform
    name: emit_notification
```

### Fan-in

Multiple inputs load in parallel, then converge at the first transform. Use a `CoTransform` (such as `SparkSqlTransform` or `DuckdbSqlTransform`) when that step needs to combine them:

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

All outputs write the same final dataset, independently. Use for fan-out scenarios such as writing to a data warehouse, cache, and archive simultaneously:

```yaml
outputs:
  - kind: NoOpOutput
    name: write_to_warehouse
  - kind: NoOpOutput
    name: write_to_cache
  - kind: NoOpOutput
    name: write_to_archive
```

## Templating

All string properties in job YAML are Jinja2 templates rendered at execution time. Referencing an undefined variable raises an error.

The two most common variable sources are domain fields and date offsets.

### Domain variables

The domain fields declared at the job level (`org`, `region`, `domain`, `subdomain`, `layer`, `product`, `model`) are available as template variables in any string property across the runner, inputs, transforms, and outputs:

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

A step can override any domain field locally. `layer: raw` on an input uses `raw` for template rendering within that step only, leaving the job-level `layer` unchanged.

### Date variables

`D` is a date object anchored to the job's execution time. Use index syntax for relative offsets: `D[0]` is today, `D[-1]` is yesterday, `D[7]` is seven days ahead.

```yaml
inputs:
  - kind: NoOpInput
    name: read_yesterday
    path: "data/raw/date={{ D[-1] }}"
    # → data/raw/date=2026-02-23

outputs:
  - kind: NoOpOutput
    name: write_today
    path: "data/refined/date={{ D[0] }}"
    # → data/refined/date=2026-02-24
```

See [Templates](templates.md) for all available variables, date formats, environment variable access, and temporary workspace paths.
