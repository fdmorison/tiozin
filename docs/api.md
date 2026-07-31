# API Reference

The public Python API. The stable surface for building Tiozin pipelines and provider families.

## Import

Everything is available from the top-level `tiozin` package:

```python
from tiozin import (
    # Bases
    Tiozin,
    Registry,
    # Processors
    Job,
    Runner,
    Input,
    Transform,
    CoTransform,
    Output,
    # Metadata
    JobManifest,
    Batch,
    BatchStatus,
    BacklogPolicy,
    # Registries
    JobRegistry,
    SettingRegistry,
    SecretRegistry,
    SchemaRegistry,
    LineageRegistry,
    MetricRegistry,
    BatchRegistry,
    # Runtime
    Context,
    TiozinApp,
    tioproxy,
)
```

## TiozinApp

Main entrypoint. Manages the application lifecycle and runs jobs.

```python
from tiozin import TiozinApp

app = TiozinApp()
app.run("path/to/job.yaml")
```

`run()` accepts:
- A path to a YAML or JSON file
- A raw YAML or JSON string
- A `JobManifest` object
- A `Job` instance

Returns the job execution result (provider-specific).

## Tiozin (base)

All executable components extend `Tiozin`. It provides:

| Property | Description |
|---|---|
| `tiozin_name` | Class name used as the `kind` in YAML |
| `tiozin_role` | Role: `job`, `runner`, `input`, `transform`, `output`, `registry` |
| `tiozin_family` | Provider family name (e.g. `tio_spark`, `tio_duckdb`) |
| `tiozin_uri` | Fully qualified identifier: `<family>/<role>/<name>` |
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

Lifecycle: `setup(data)` → `write(data)` → `teardown(data)`

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
| `MetricRegistry` | Extend to implement custom metric tracking against a backend such as Prometheus, InfluxDB, or Datadog |
| `BatchRegistry` | Persists and queries batches. See [Registries](concepts/registries.md#batchregistry) |

`SchemaRegistry`, `LineageRegistry`, and `BatchRegistry` accept extra constructor parameters on top of the base ones. See [Extending the Registry](extending/registry.md) for the full subtype contracts.

## Context

Holds the execution scope for the current job or step. Populated automatically by the framework. Every step and runner that runs inside a job has access to the same context for that execution.

### Thread and async safety

`Context` is implemented with Python's `contextvars.ContextVar`. This means:

- **Thread-safe**: each thread gets its own isolated copy of the active context. Parallel threads running different jobs never see each other's context.
- **Async-safe**: each `asyncio` Task gets its own copy. Concurrent coroutines do not share context state even when running in the same event loop.
- **Nested execution-safe**: activating a context is reentrant. Each `with context:` call pushes a restoration token onto an internal stack; exiting restores the previous scope. A child step context can be safely activated inside a parent job context without corrupting the parent.

These guarantees are provided by the Python runtime and do not require any application-level locking.

### Accessing the active context

From inside any Tiozin plugin:

```python
ctx = self.context                     # raises if no active context
ctx = Context.current()                # same
ctx = Context.current(required=False)  # returns None if not active
```

Context is activated automatically by the framework before calling `setup()`, `read()`, `transform()`, `write()`, or `teardown()` methods. Manual activation is not required.

### Key fields

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Job or step name |
| `run_id` | `str` | Unique execution ID for this run |
| `nominal_time` | `DateTime` | Reference time for this execution (UTC) |
| `org`, `domain`, `layer`, ... | `str` | Domain fields. See [Jobs](concepts/jobs.md#domain) |
| `runner` | `Runner` | Active runner |
| `job` | `Context` | The parent job context (same as `self` when accessed from a job) |
| `shared` | `dict` | Shared mutable state for passing data between steps within the same execution |
| `temp_workdir` | `Path` | Temporary working directory for this component's execution |

### Passing data between steps

`shared` is a plain `dict` scoped to the current job execution. Values written by one step are readable by any step that runs after it:

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

# Parse from a YAML file path or raw YAML/JSON string
manifest = JobManifest.try_from_yaml_or_json("path/to/job.yaml")
```

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
