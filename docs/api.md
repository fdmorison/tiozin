# API Reference

The public Python API. The stable surface for building Tiozin pipelines and provider families.

## Import

Everything is available from the top-level `tiozin` package:

```python
from tiozin import (
    # Bases
    Tiozin,
    Registry,
    # Runtime
    Job,
    Runner,
    Input,
    Transform,
    CoTransform,
    Output,
    EtlStep,
    Context,
    TiozinApp,
    TemplateString,
    tioproxy,
    # Metadata
    JobManifest,
    RunnerManifest,
    InputManifest,
    TransformManifest,
    OutputManifest,
    SettingsManifest,
    Schema,
    Secret,
    Dataset,
    Datasets,
    LineageDataset,
    LineageEvent,
    LineageRunEvent,
    Batch,
    BatchStatus,
    BacklogPolicy,
    JobRegistry,
    SettingRegistry,
    SecretRegistry,
    SchemaRegistry,
    LineageRegistry,
    MetricRegistry,
    BatchRegistry,
)
```

Three enums live one level down, in `tiozin.api`: `Cadence`, `LowerEnum`, and `UpperEnum`.

## TiozinApp

Main entrypoint. Manages the application lifecycle and runs jobs.

```python
from tiozin import TiozinApp

app = TiozinApp()
app.run("path/to/job.yaml")
```

`run()` takes one or more jobs as positional arguments, or a single list. Each item may be:

- A `Job` instance
- A `JobManifest` object
- A raw YAML or JSON string
- A job identifier resolved by the job registry. With the default file registry, the identifier is the manifest path, joined to the registry location when it is relative

Returns a list of results, one per job, in submission order.

## Tiozin (base)

All executable components extend `Tiozin`. It provides:

| Property | Description |
|---|---|
| `tiozin_name` | Class name used as the `kind` in YAML |
| `tiozin_role` | Role class name: `Job`, `Runner`, `Input`, `Transform`, `Output`, or `Registry` |
| `tiozin_family` | Provider family name (e.g. `tio_spark`, `tio_duckdb`) |
| `tiozin_uri` | Fully qualified identifier: `tiozin://<family>/<role>/<name>`, with the role lowercased |
| `context` | Active execution `Context` (raises if no active context) |

## Job

Defines a complete pipeline. Extend and implement `submit()`. See [Jobs](concepts/jobs.md) for the full contract, properties, and invariants.

```python
from typing import Any
from tiozin import Job


class MyJob(Job[Any]):
    def submit(self) -> Any:
        # implement the execution model here
        ...
```

## Runner

Abstract base for execution engines. Extend and implement `session`, `setup()`, `run()`, and `teardown()`. See [Runners](concepts/runners.md) for the full contract and properties.

| Attribute | Description |
|---|---|
| `streaming` | `bool`. Whether this runner executes streaming workloads |
| `session` | Abstract property. Returns the active engine session |

## Input

Abstract base for data sources. Extend and implement `read()`. See [Steps](concepts/steps.md#input) for the full contract and properties.

Lifecycle: `setup()` → `read()` → `teardown()`

## Transform and CoTransform

Abstract bases for data transformations. Extend and implement `transform()`. See [Steps](concepts/steps.md#transform) for the full contract and properties.

`Transform.transform(data)` for a single dataset. `CoTransform.transform(data, *others)` for multiple datasets.

## Output

Abstract base for data destinations. Extend and implement `write()`. See [Steps](concepts/steps.md#output) for the full contract and properties.

`write()` can return the data, a writer object, or `None`. The return value becomes part of the execution plan passed to the runner's `run()` method.

Lifecycle: `setup()` → `write(data)` → `teardown()`

## Registry

Abstract base for metadata services. The base class defines the construction and lifecycle contract shared by every registry. Each registry subtype declares its own method interface.

| Parameter | Type | Description |
|---|---|---|
| `location` | `str` | Backend location (HTTP/HTTPS, FTP, local path, `s3://`, `gs://`, `az://`) |
| `readonly` | `bool` | If `True`, disables write operations |
| `cache` | `bool` | If `True`, enables in-memory caching |
| `timeout` | `int` | Request timeout in seconds |
| `failfast` | `bool` | If `True`, raises when metadata is not found. If `False`, returns `None` |
| `ready` | `bool` | Instance attribute. `True` after `setup()` runs, `False` after `teardown()` |

Defaults for `readonly`, `cache`, `timeout`, and `failfast` are resolved from `tiozin.config`. The base class also inherits `setup()` and `teardown()`, which toggle the `ready` flag.

### Registry Subtypes

Each subtype defines its own contract. The table below lists the methods or extension role for each one.

| Registry | Contract |
|---|---|
| `SettingRegistry` | `get() -> SettingsManifest` |
| `SecretRegistry` | `get(identifier: str) -> Secret`, `register(identifier: str, value: Secret) -> None` |
| `SchemaRegistry` | `get(subject: str, version: str = None) -> Schema`, `register(subject: str, value: Schema) -> None` |
| `JobRegistry` | `get(identifier: str) -> JobManifest`, `register(identifier: str, value: JobManifest) -> None` |
| `LineageRegistry` | `emit(event: LineageEvent) -> None` |
| `MetricRegistry` | No methods yet. The class is declared as a reservation for future use, with metric backends such as Prometheus, InfluxDB, or Datadog as the intended direction |
| `BatchRegistry` | Persists and queries batches. See [Registries](concepts/registries.md#batchregistry) |

`SchemaRegistry`, `LineageRegistry`, and `BatchRegistry` accept extra constructor parameters on top of the base ones. See [Extending the Registry](extending/registry.md) for the full subtype contracts.

## Context

Holds the execution scope for the current job or step. The framework builds one context for the job and, from it, a separate context for every step that runs inside that job.

Those contexts are not identical. Each one carries its own `name`, `kind`, `options`, and `temp_workdir`, because they describe the component the context belongs to. The domain fields (`org`, `region`, `domain`, `subdomain`, `layer`, `product`, and `model`) take the step's own value and fall back to the job's when the step declares none. Everything that describes the execution as a whole is inherited unchanged from the job: `namespace`, the ownership fields (`maintainer`, `cost_center`, `owner`, and `labels`), and the runtime values `job`, `runner`, `cadence`, `backlog_policy`, `nominal_time`, `shared`, `catalog`, `registries`, and `template_vars`.

For a plugin developer, `Context` is the API to work against. It is the single place that exposes what the framework knows about the running execution: who the job is, which runner is active, which registries are available, and which batches are waiting to be processed.

### Thread and async safety

`Context` is implemented with Python's `contextvars.ContextVar`. This means:

- **Thread-safe**: each thread gets its own isolated copy of the active context. Parallel threads running different jobs never see each other's context.
- **Async-safe**: each `asyncio` Task gets its own copy. Concurrent coroutines do not share context state even when running in the same event loop.
- **Nested execution-safe**: activating a context is reentrant. Each `with context:` call pushes a restoration token onto an internal stack; exiting restores the previous scope. A child step context can be safely activated inside a parent job context without corrupting the parent.

These guarantees are provided by the Python runtime and do not require any application-level locking.

### Accessing the active context

From inside any Tiozin plugin:

```python
from tiozin import Context
from tiozin.utils import current_context, try_current_context

ctx = self.context                     # raises if no active context
ctx = Context.current()                # same
ctx = Context.current(required=False)  # returns None if not active
ctx = current_context()                # raises if no active context
ctx = try_current_context()            # returns None if not active
```

`current_context()` and `try_current_context()` are thin wrappers over `Context.current()`. They exist for helper code that is not a plugin method and therefore has no `self.context` to reach for.

Context is activated automatically by the framework before calling `setup()`, `read()`, `transform()`, `write()`, or `teardown()` methods. Manual activation is not required.

### Key fields

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Job or step name, normalized as an underscore-separated slug |
| `display_name` | `str` | Job or step name as declared, before slugification |
| `qualified_name` | `str` | Job and step names joined with a dot, as in `example_job.load_it`. On a job context, the job name alone |
| `qualified_slug` | `str` | The same identity as a single slug, as in `example_job_load_it` |
| `run_id` | `str` | Unique execution ID for this run |
| `nominal_time` | `NominalTime` | Reference time for this execution. A UTC datetime truncated to the job's cadence |
| `org`, `domain`, `layer`, ... | `str` | Domain fields. See [Jobs](concepts/jobs.md#domain) |
| `runner` | `Runner` | Active runner |
| `job` | `Context` | The parent job context (same as `self` when accessed from a job) |
| `shared` | `dict` | Session-scoped state shared by every step of the same execution |
| `temp_workdir` | `Path` | Temporary working directory for this component's execution |

Every registry is reachable as a property: `setting_registry`, `secret_registry`, `schema_registry`, `job_registry`, `metric_registry`, `lineage_registry`, and `batch_registry`. Each returns the configured instance, or the fallback Tiozin installs when the job declares none, with the contracts listed in [Registry Subtypes](#registry-subtypes).

### Sharing Session State

Pipeline data does not pass through the context. It moves from step to step as the step's return value: the value returned by `read()` is the input of `transform()`, and the value returned by `transform()` is the input of `write()`. Tiozin wraps that value in a `Dataset`, which holds the payload together with its `(namespace, name)` identity and an optional `Schema`.

`shared` answers a different need: values that are not the data itself but must remain available after the step that produced them finishes. It is a plain `dict` created once per job execution and passed to every step context, so every step reads and writes the same object. Session attributes in a web server are the closest analogy: whatever a step stores stays visible to every step that runs after it, and it is gone once the execution ends.

Counting records in a transform and reporting the count from an output is a typical use:

```python
from typing import Any
from tiozin import Transform, Output


class RecordCountTransform(Transform):
    def transform(self, data: Any) -> Any:
        self.context.shared["record_count"] = len(data)
        return data


class AuditOutput(Output):
    def write(self, data: Any) -> Any:
        count = self.context.shared.get("record_count")
        self.info(f"{self.context.name}: writing {count} records")
        return data
```

The dataset is still the return value of each method. Only the count is stored in `shared`.

### Accessing the Job Backlog

The `Batch` is Tiozin's state model for incremental processing. This API lets incremental jobs work with pending data through a backlog abstraction.

Like a task backlog, each item represents a unit of work waiting to be completed. In Tiozin, those work items are batches of data. Plugins inspect and update batches while Tiozin tracks their execution and processing state.

See [Batches](concepts/batches.md) for the batch model and lifecycle, and [How to Work with Backlogs](how-to/batches.md) for practical usage.

| Member | Type | Description |
| --- | --- | --- |
| `cadence` | `Cadence` | Job cadence. See [Jobs](concepts/jobs.md#cadence). |
| `backlog_policy` | `BacklogPolicy` | Active backlog policy. See [Jobs](concepts/jobs.md#backlog-policy). |
| `batch_registry` | `BatchRegistry` | Registry subtype that persists and queries batches, falling back to `NoOpBatchRegistry` when none is configured. See [Registries](concepts/registries.md#batchregistry) for the full contract. |
| `get_job_backlog()` | `list[Batch]` | Returns the batches assigned to the current execution, limited by the job's `max_batches_per_run`. See [Jobs](concepts/jobs.md#max-batches-per-run). |
| `get_job_managed_bookmark(key, fallback=None)` | `Any` | Shortcut for `Batch.get_managed_bookmark()` on the first batch. Returns `fallback` when no batch is assigned. |
| `set_job_managed_bookmark(key, next_value)` | `Any` | Shortcut for `Batch.set_managed_bookmark()` on the first batch. Returns `None` when no batch is assigned. |
| `get_job_bookmark(key, fallback=None)` | `Any` | Shortcut for `Batch.get_bookmark()` on the first batch. Returns `fallback` when no batch is assigned. |
| `set_job_bookmark(key, next_value)` | `Any` | Shortcut for `Batch.set_bookmark()` on the first batch. Returns `None` when no batch is assigned. |

## JobManifest

Pydantic model representing a parsed YAML job definition.

```python
from tiozin import JobManifest

manifest = JobManifest.from_file("path/to/job.yaml")  # local path or URI
manifest = JobManifest.from_yaml(content)             # raw YAML or JSON string
manifest = JobManifest.try_from_yaml(content)         # same, returns None instead of raising
```

`from_file()` reads local paths and remote URIs through [fsspec](https://filesystem-spec.readthedocs.io/en/latest/), including `s3://`, `gs://`, `az://`, `http://`, `https://`, `ftp://`, and `sftp://`. Both YAML and JSON files are accepted.

To accept any of these forms in a single call, use `TiozinApp.resolve_manifest()`. It returns a `JobManifest` as is, parses a string as YAML or JSON content, and falls back to a job registry lookup by identifier.

## @tioproxy

Registers proxy classes on a Tiozin class. Used when building provider families.

```python
from tiozin import tioproxy

@tioproxy(MyProxy)
class MyInput(Input):
    ...
```

Proxy classes must inherit from `wrapt.ObjectProxy`. A class may only use `@tioproxy` once.

See [Tio Proxy](extending/proxies.md) for details on how the proxy chain is built.
