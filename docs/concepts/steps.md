# Inputs, Transforms & Outputs

Steps are the building blocks inside a pipeline: inputs read data, transforms modify it, outputs persist it.

## Input

An Input reads data from a source and passes the result to the next step.

### The contract

`Input` is an abstract base class. Extend it and implement `read()`:

```python
from typing import Any
from tiozin import Input


class MyInput(Input[Any]):
    def read(self) -> Any:
        # implement your read logic here
        ...
```

Three lifecycle methods define the contract:

| Method | Required | Description |
|---|---|---|
| `setup()` | no | Called before `read()`. Override to initialize connections or resources |
| `read()` | yes | Reads and returns data. Must be overridden |
| `teardown()` | no | Called after `read()`. Override to release resources |

### Properties

| Property | Required | Type | Default | Description |
|---|---|---|---|---|
| `kind` | yes | `str` | | Input type, used to resolve the plugin |
| `name` | yes | `str` | | Unique identifier within the job |
| `description` | no | `str` | `None` | Short description of the data source |
| `schema` | no | `str` | `None` | Schema definition of the input data |
| `schema_subject` | no | `str` | `None` | Schema registry subject name |
| `schema_version` | no | `str` | `None` | Specific schema version to enforce |

### Domain overrides

Every input optionally accepts the same domain fields declared at the job level. When set, they override the job-level values for template rendering within that step. This is useful when an input reads from a different layer or domain than the job's output:

| Field | Description |
|---|---|
| `org` | Organization owning this step's data |
| `region` | Business region |
| `domain` | Domain team |
| `subdomain` | Subdomain |
| `layer` | Data layer (e.g. `raw` for an input reading from the raw layer) |
| `product` | Data product |
| `model` | Data model |

## Transform

A Transform receives the output of the previous step, applies logic, and returns the result.

### The contract

`Transform` is an abstract base class. Extend it and implement `transform()`:

```python
from typing import Any
from tiozin import Transform


class MyTransform(Transform[Any]):
    def transform(self, data: Any) -> Any:
        # implement your transformation logic here
        ...
```

Three lifecycle methods define the contract:

| Method | Required | Description |
|---|---|---|
| `setup(data)` | no | Called before `transform()`. Override to initialize resources |
| `transform(data)` | yes | Applies transformation logic and returns the result. Must be overridden |
| `teardown(data)` | no | Called after `transform()`. Override to release resources |

For operations that need to combine multiple datasets, extend `CoTransform` instead:

```python
from typing import Any
from tiozin import CoTransform


class MyCoTransform(CoTransform[Any]):
    def transform(self, data: Any, *others: Any) -> Any:
        # implement your multi-dataset logic here
        ...
```

`CoTransform` receives all current datasets when a job has multiple inputs or prior steps produced multiple datasets.

| Method | Required | Description |
|---|---|---|
| `setup(data, *others)` | no | Called before `transform()` |
| `transform(data, *others)` | yes | Applies cooperative transformation logic. Must be overridden |
| `teardown(data, *others)` | no | Called after `transform()` |

### Properties

| Property | Required | Type | Default | Description |
|---|---|---|---|---|
| `kind` | yes | `str` | | Transform type, used to resolve the plugin |
| `name` | yes | `str` | | Unique identifier within the job |
| `description` | no | `str` | `None` | Short description of the transformation |

Transforms accept the same domain override fields as inputs.

## Output

An Output writes data to a destination. Its `write()` method may return `None` (eager execution) or a plan object (lazy execution). See [Runners](runners.md) for the eager/lazy distinction.

### The contract

`Output` is an abstract base class. Extend it and implement `write()`:

```python
from typing import Any
from tiozin import Output


class MyOutput(Output[Any]):
    def write(self, data: Any) -> Any:
        # implement your write logic here
        ...
```

Three lifecycle methods define the contract:

| Method | Required | Description |
|---|---|---|
| `setup(data)` | no | Called before `write()`. Override to initialize resources |
| `write(data)` | yes | Writes data to the destination and returns a plan object or `None`. Must be overridden |
| `teardown(data)` | no | Called after `write()`. Override to release resources |

### Properties

| Property | Required | Type | Default | Description |
|---|---|---|---|---|
| `kind` | yes | `str` | | Output type, used to resolve the plugin |
| `name` | yes | `str` | | Unique identifier within the job |
| `description` | no | `str` | `None` | Short description of the destination |

Outputs accept the same domain override fields as inputs.

## Invariants

- `name` is required for all steps. Missing it raises an error at construction time.
- `inputs` must contain at least one element per job.
- `transforms` and `outputs` are optional.
- Unknown fields in YAML are passed as provider-specific options. The framework does not validate them.

## Available steps

Steps are provided by provider families:

- **`NoOpInput`**, **`NoOpTransform`**, **`NoOpOutput`** from `tio_kernel`: do nothing. Use for testing, dry-runs, and local development.
- **`SparkFileInput`**, **`SparkSqlTransform`**, **`SparkFileOutput`** from `tio_spark`. See [tio_spark](../tio_spark.md).
- **`DuckdbFileInput`**, **`DuckdbSqlTransform`**, **`DuckdbFileOutput`** from `tio_duckdb`. See [tio_duckdb](../tio_duckdb.md).
