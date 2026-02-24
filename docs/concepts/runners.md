# Runner

A Runner is Tiozin's execution engine. It creates the runtime session, receives the execution plan produced by the pipeline steps, and releases resources when the job finishes.

## The contract

`Runner` is an abstract base class. Any class that extends it and registers as a Tiozin plugin becomes a valid runner type.

Four lifecycle methods define the contract:

| Method | Required | Description |
|---|---|---|
| `setup()` | yes | Called before execution. Create sessions, connections, or shared resources here |
| `run(plan)` | yes | Execute the plan. Receives the list of values returned by all outputs |
| `teardown()` | no | Called after execution. Release sessions, connections, and resources here |
| `session` | yes | Abstract property. Returns the active engine session |

The session is the live connection to the underlying engine, such as a `SparkSession` or a `DuckDBPyConnection`. It is created during `setup()` and made available to all steps via `self.context.runner.session`.

## Custom implementations

Any class that extends `Runner` and implements `session`, `setup()`, and `run()` becomes a valid runner type:

```python
from typing import Any
from tiozin import Runner


class MyRunner(Runner[list, Any, None]):
    @property
    def session(self) -> Any:
        return self._session

    def setup(self) -> None:
        self._session = create_session()

    def run(self, plan: list) -> None:
        for item in plan:
            if item is not None:
                execute(item, self._session)

    def teardown(self) -> None:
        self._session.close()
```

Register it as a `tiozin.family` entry point and use `kind: MyRunner` in YAML. See [Creating Provider Families](../extending/families.md) for registration details.

## Properties

### Identity

| Property | Required | Type | Default | Description |
|---|---|---|---|---|
| `kind` | yes | `str` | | Runner type, used to resolve the plugin |
| `name` | no | `str` | `None` | Optional identifier |
| `description` | no | `str` | `None` | Short description |

### Execution

| Property | Required | Type | Default | Description |
|---|---|---|---|---|
| `streaming` | no | `bool` | `false` | Whether this runner executes streaming workloads |
| `**options` | no | | | Provider-specific configuration parameters |

`streaming` is part of the base `Runner` contract, not provider-specific. Provider implementations may inspect it to switch between batch and streaming modes.

## Invariants

- `session`, `setup()`, and `run()` are required. A runner that does not implement them raises at construction time.
- `teardown()` is optional. The default implementation is a no-op.
- Accessing `session` before `setup()` raises `NotInitializedError`.
- The Runner is the only component that may hold stateful connections. Inputs, Transforms, and Outputs must access the session through `self.context.runner.session`.

## Accessing the session

Inside any step, access the runner's session via the context:

```python
session = self.context.runner.session
```

## Eager and lazy execution

A runner's `run()` method receives a list containing the return value of every output's `write()` method.

An **eager output** writes immediately inside `write()` and returns `None`. The runner receives `None` for that position and skips it.

A **lazy output** returns a typed plan object: a writer, a SQL string, or any value the runner knows how to process. The runner collects all plans and decides how to execute them: sequentially, in parallel, as a batch, or any other strategy appropriate for the underlying engine.

The choice is determined by what `write()` returns and what `run()` knows how to handle. Lazy execution is what makes runners genuinely useful for engines like Spark or DuckDB, where execution is most efficient when the engine controls scheduling.

## Available runners

Runners are provided by provider families:

- **`NoOpRunner`** from `tio_kernel`: accepts any plan and returns `None` without executing anything. Use for testing, dry-runs, and local development.
- **`SparkRunner`** and **`SparkIcebergRunner`** from `tio_spark`. See [tio_spark](../tio_spark.md).
- **`DuckdbRunner`** from `tio_duckdb`. See [tio_duckdb](../tio_duckdb.md).
