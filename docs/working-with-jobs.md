# Working with Jobs

## How `app.run()` works

`TiozinApp.run()` is the single entry point for executing any job. Its primary role is to resolve a job manifest and run it.

The primary use case is passing an **identifier** that the `JobRegistry` backend can resolve:

```python
from tiozin import TiozinApp

app = TiozinApp()
app.run("jobs/orders_daily_summary.yaml")  # resolved by the JobRegistry
```

The `JobRegistry` is a pluggable backend. What "resolving an identifier" means depends on which backend is configured:

- **`FileJobRegistry`** (the default, from `tio_kernel`): reads a YAML or JSON manifest from the filesystem or any object storage path supported by fsspec (local paths, `s3://`, `gs://`, `az://`, etc.). This is what runs when you pass a file path.
- A custom `JobRegistry` could resolve identifiers by fetching a manifest from a REST API, a database table, a service registry, or any other backend. The identifier is just a string. The registry decides what to do with it.

When you pass a raw YAML string or a `JobManifest` object directly, Tiozin bypasses the registry and runs the job without a lookup. This is a convenience for development and dynamic assembly, not the primary production path.

In production, the recommended pattern is to store job manifests in a registry-compatible backend and trigger execution by identifier. This decouples job authoring from job execution, enables versioning, and keeps the execution layer stateless.

## Building your first job

A Tiozin job is a declarative YAML document. This section walks through building one field by field so you understand the purpose of each part before seeing the whole.

### Step 1: Identify your job

Every job starts with a type and a name. `kind` selects the job implementation. `LinearJob` is the built-in implementation that runs steps in a fixed sequential order.

```yaml
kind: LinearJob
name: orders_daily_summary
```

`name` is the unique identifier for this job within your system. It is not the execution ID. A new execution ID is generated every time the job runs.

### Step 2: Describe what it does

`description` accepts a multi-line string. Write it for the person who will be on-call when this job fails at 3am.

```yaml
description: |
  Joins daily orders with the customer master and writes
  a regional summary to the refined layer.
  Runs daily after the raw ingestion window closes.
```

### Step 3: Declare ownership

Who requested this job, who maintains it, and who pays for it?

```yaml
owner: data-platform
maintainer: analytics-team
cost_center: tio_scrooge
labels:
  criticality: high
```

`labels` is free-form key-value metadata. Use it for anything your tooling needs to read.

### Step 4: Declare governance

These seven fields declare the organizational context and lineage of the data this job produces. They also become available as template variables in any string property across the job.

```yaml
org: acme
region: us-east
domain: ecommerce
subdomain: retail
layer: refined
product: orders
model: daily_summary
```

`region` is a business territory (`brazil`, `latam`, `emea`, `euro`), not a cloud infrastructure region. `product` groups one or more related `model`s. See [Jobs](concepts/jobs.md#governance) for the full field definitions.

### Step 5: Choose a runner

The runner is the execution engine. It manages the session and executes the plan produced by the pipeline steps. Provider-specific options go directly under `runner`.

```yaml
runner:
  kind: NoOpRunner
  description: Dry-run mode for local validation.
  log_level: "{{ ENV.LOG_LEVEL }}"
```

`{{ ENV.LOG_LEVEL }}` is a Jinja2 template. It reads from `os.environ` at execution time. ENV values are never exposed in logs.

### Step 6: Declare inputs

Inputs read data from sources. At least one input is required. Each input has a `kind`, a unique `name`, and any provider-specific fields. Unknown fields are passed through to the provider.

```yaml
inputs:
  - kind: NoOpInput
    name: read_raw_orders
    description: Raw orders from the previous day.
    layer: raw
    path: "data/{{ layer }}/{{ product }}/date={{ D[-1] }}"
```

`layer: raw` on the input overrides the job-level `layer` for template rendering within this step. `D[-1]` resolves to yesterday's date. `{{ product }}` resolves to `orders` from the job-level governance fields.

### Step 7: Add transforms

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

Provider-specific fields like `strategy` and `group_by` are passed through to the plugin without validation at the job level.

### Step 8: Write outputs

Outputs write the final dataset to a destination. They are optional. You can write to multiple destinations independently.

```yaml
outputs:
  - kind: NoOpOutput
    name: write_summary
    description: Regional order summary in the refined layer.
    path: "data/{{ domain }}-{{ layer }}/{{ product }}/{{ model }}/date={{ D[0] }}"
```

`{{ D[0] }}` resolves to today's date. The path uses governance fields declared at the job level.

### The complete job

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
  description: Dry-run mode for local validation.
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

Or from Python:

```python
from tiozin import TiozinApp

app = TiozinApp()
app.run("jobs/orders_daily_summary.yaml")
```

## Defining a job

Tiozin accepts jobs in several forms. Choose whichever fits your context.

### YAML file

The standard form for production. Pass a path to a `.yaml` file:

```python
app.run("jobs/orders_daily_summary.yaml")
```

JSON files work the same way. Tiozin detects the format automatically.

### Inline string

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

JSON is equally valid. Since JSON is a valid YAML subset, both are parsed the same way.

### JobManifest

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

### Job.builder()

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

### Direct instantiation

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

All string properties in job YAML are Jinja2 templates. The framework renders them at execution time using the current execution context as the variable namespace. Referencing an undefined variable raises an error.

### Governance variables

The governance fields declared at the job level (`org`, `region`, `domain`, `subdomain`, `layer`, `product`, `model`) are available as template variables in any string property across the runner, inputs, transforms, and outputs:

```yaml
org: acme
domain: ecommerce
layer: refined
product: orders
model: daily_summary

inputs:
  - kind: NoOpInput
    name: read_raw
    path: "data/{{ layer }}/{{ product }}/{{ model }}"
    # → data/refined/orders/daily_summary

outputs:
  - kind: NoOpOutput
    name: write_refined
    path: "data/{{ domain }}-{{ layer }}/{{ product }}"
    # → data/ecommerce-refined/orders
```

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

See [Templates](templates.md) for all available date formats and aliases.

### Environment variables

`ENV` is a read-only view of `os.environ`. Use it to inject secrets, credentials, or environment-specific configuration without hardcoding values in the job definition:

```yaml
runner:
  kind: NoOpRunner
  log_level: "{{ ENV.LOG_LEVEL }}"

outputs:
  - kind: NoOpOutput
    name: write_data
    destination: "{{ ENV.OUTPUT_BUCKET }}"
```

`ENV` values are never exposed in logs or debug output.

### Temporary workspace

Each job component gets its own temporary directory at execution time. Use `{{ temp_workdir }}` inside a component's properties to reference its own directory, and `{{ job.temp_workdir }}` to reference the shared job-level directory accessible across all components:

```yaml
runner:
  kind: NoOpRunner
  workspace: "{{ temp_workdir }}/runner_workspace"

inputs:
  - kind: NoOpInput
    name: download_data
    local_cache: "{{ temp_workdir }}/cache"
    output_path: "{{ job.temp_workdir }}/downloaded.csv"

transforms:
  - kind: NoOpTransform
    name: process_data
    input_path: "{{ job.temp_workdir }}/downloaded.csv"
    output_path: "{{ job.temp_workdir }}/processed.parquet"

outputs:
  - kind: NoOpOutput
    name: upload_results
    source_path: "{{ job.temp_workdir }}/processed.parquet"
```

`{{ job.temp_workdir }}` is the standard way to pass files between steps when using file-based runners.
