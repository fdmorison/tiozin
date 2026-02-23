# API Reference

The public Python API — the stable surface for building Tiozin pipelines and provider families.

---

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
    # Registries
    JobRegistry,
    SettingRegistry,
    SecretRegistry,
    SchemaRegistry,
    LineageRegistry,
    MetricRegistry,
    TransactionRegistry,
    # Runtime
    Context,
    TiozinApp,
    tioproxy,
)
```

---

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

---

## Tiozin (base)

All executable components extend `Tiozin`. It provides:

| Property | Description |
|---|---|
| `tiozin_name` | Class name used as the `kind` in YAML |
| `tiozin_role` | Role: `job`, `runner`, `input`, `transform`, `output`, `registry` |
| `tiozin_family` | Provider family name (e.g. `tio_spark`, `tio_duckdb`) |
| `tiozin_uri` | Fully qualified identifier: `<family>/<role>/<name>` |
| `context` | Active execution `Context` (raises if no active context) |

---

## Job

Defines a complete pipeline. Extend and implement `submit()`.

```python
from tiozin import Job

class LinearJob(Job):
    def submit(self):
        datasets = [i.read() for i in self.inputs]
        for t in self.transforms:
            datasets = [t.transform(d) for d in datasets]
        results = [o.write(d) for o in self.outputs for d in datasets]
        return self.runner.run(results)
```

Key attributes populated from the YAML manifest:

| Attribute | Type | Description |
|---|---|---|
| `name` | `str` | Job identifier |
| `runner` | `Runner` | Execution backend |
| `inputs` | `list[Input]` | Data sources |
| `transforms` | `list[Transform]` | Data transformations |
| `outputs` | `list[Output]` | Data destinations |
| `org`, `domain`, `layer`, ... | `str` | Data Mesh fields |

---

## Runner

Abstract base for execution engines. Extend and implement `session`, `setup()`, `run()`, `teardown()`.

```python
from tiozin import Runner

class MyRunner(Runner):
    @property
    def session(self):
        return self._session

    def setup(self):
        self._session = create_session()

    def run(self, plan):
        return execute(plan, self._session)

    def teardown(self):
        self._session.close()
```

| Attribute | Description |
|---|---|
| `streaming` | `bool` — whether this runner executes streaming workloads |
| `session` | Abstract property — the active engine session |

---

## Input

Abstract base for data sources. Extend and implement `read()`.

```python
from tiozin import Input

class MyInput(Input):
    def read(self):
        return load_data(self.path)
```

Lifecycle: `setup()` → `read()` → `teardown()`

`setup()` and `teardown()` are no-ops by default. Override them if needed.

---

## Transform and CoTransform

Abstract bases for data transformations.

`Transform.transform(data)` — single dataset:

```python
from tiozin import Transform

class MyTransform(Transform):
    def transform(self, data):
        return filter_data(data)
```

`CoTransform.transform(data, *others)` — multiple datasets:

```python
from tiozin import CoTransform

class JoinTransform(CoTransform):
    def transform(self, left, right):
        return join(left, right)
```

Lifecycle: `setup(data)` → `transform(data)` → `teardown(data)`

---

## Output

Abstract base for data destinations. Extend and implement `write()`.

```python
from tiozin import Output

class MyOutput(Output):
    def write(self, data):
        save_data(data, self.path)
        return data
```

`write()` can return the data, a writer object, or `None`. The return value becomes part of the execution plan passed to the runner's `run()` method.

Lifecycle: `setup(data)` → `write(data)` → `teardown(data)`

---

## Registry

Abstract base for metadata services. Extend and implement `get()` and `register()`.

```python
from tiozin import Registry

class MyRegistry(Registry):
    def get(self, identifier, version=None):
        return fetch(identifier)

    def register(self, identifier, value):
        store(identifier, value)
```

| Method | Description |
|---|---|
| `get(identifier, version=None)` | Retrieve metadata. Raises `TiozinNotFoundError` if not found |
| `register(identifier, value)` | Store metadata |
| `try_get(identifier, version=None)` | Retrieve metadata or return `None` |

---

## Context

Holds the execution scope for the current job or step. Populated automatically by the framework.

Access the active context from any Tiozin:

```python
ctx = self.context                     # raises if no active context
ctx = Context.current()                # same
ctx = Context.current(required=False)  # returns None if not active
```

Key fields:

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Job or step name |
| `run_id` | `str` | Unique execution ID for this run |
| `nominal_time` | `DateTime` | Reference time for this execution (UTC) |
| `org`, `domain`, `layer`, ... | `str` | Data Mesh fields |
| `runner` | `Runner` | Active runner |
| `shared` | `dict` | Shared state for passing data between steps |
| `temp_workdir` | `Path` | Temporary working directory for this execution |

---

## JobManifest

Pydantic model representing a parsed YAML job definition.

```python
from tiozin import JobManifest

# Parse from a YAML file path or raw YAML/JSON string
manifest = JobManifest.try_from_yaml_or_json("path/to/job.yaml")
```

---

## tioproxy

Registers proxy classes on a Tiozin class. Used when building provider families.

```python
from tiozin import tioproxy

@tioproxy(MyProxy)
class MyInput(Input):
    ...
```

Proxy classes must inherit from `wrapt.ObjectProxy`. A class may only use `@tioproxy` once.

See [Tio Proxy](concepts/proxies.md) for details on how the proxy chain is built.
